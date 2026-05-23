import copy
from typing import List, Optional, Tuple

from game_algorithms.interfaces import GameState, Action, ActionsFunction, ResultFunction
from game_algorithms.game import Game
from models import (GameBoardState, Player, Monster, Position,
                    ITEM_HEALING, ITEM_CROWD_CTRL, ITEM_ATTACK, ITEM_MOVEMENT)
from pathfinding import (manhattan_distance, is_in_attack_range,
                         find_legal_move_positions, find_distance,
                         GridNearestItemGoalTest, GridNearestCardGoalTest,
                         find_distance_with_bfs)

# ─── State ────────────────────────────────────────────────────────────────────

class MonsterHuntState(GameState):
    """
    Wraps GameBoardState as a GameState for the minimax engine.
    player_to_move is the player ID (int) whose turn it is.
    Equivalent to XOState in exercise-07.
    """

    def __init__(self, board: GameBoardState, player_to_move: int) -> None:
        """Initializes the MonsterHuntState.
        Args:
            board (GameBoardState): The current game board.
            player_to_move (int): ID of the player whose turn it is.
        """
        super().__init__(board, player_to_move)

    def __str__(self) -> str:
        return f"{self.state}\n  Player to move: {self.player_to_move}"


# ─── Actions ──────────────────────────────────────────────────────────────────

class MonsterHuntAction(Action):
    """Base class for all Monster Hunt actions."""
    pass


class MoveAction(MonsterHuntAction):
    """Moves the player to a new position on the map (1 action = 1 API call)."""

    def __init__(self, to_x: int, to_y: int) -> None:
        """Initializes the MoveAction.
        Args:
            to_x (int): Destination X coordinate.
            to_y (int): Destination Y coordinate.
        """
        self.to_x = to_x
        self.to_y = to_y

    def __str__(self) -> str:
        return f"Move to ({self.to_x}, {self.to_y})"


class AttackAction(MonsterHuntAction):
    """Attacks an entity (player or monster) by its ID."""

    def __init__(self, target_id: int, target_x: int, target_y: int) -> None:
        """Initializes the AttackAction.
        Args:
            target_id (int): ID of the entity to attack.
            target_x (int): X position of the target (for display).
            target_y (int): Y position of the target (for display).
        """
        self.target_id = target_id
        self.target_x = target_x
        self.target_y = target_y

    def __str__(self) -> str:
        return f"Attack entity {self.target_id} at ({self.target_x}, {self.target_y})"


class UseItemAction(MonsterHuntAction):
    """Uses an item from the player's inventory."""

    def __init__(self, item_id: int, item_name: str) -> None:
        """Initializes the UseItemAction.
        Args:
            item_id (int): ID of the item to use.
            item_name (str): Name of the item (for display).
        """
        self.item_id = item_id
        self.item_name = item_name

    def __str__(self) -> str:
        return f"Use item '{self.item_name}' (id={self.item_id})"


class PickupCardAction(MonsterHuntAction):
    """Picks up a monster card from the map."""

    def __init__(self, card_id: int, card_x: int, card_y: int, card_name: str) -> None:
        """Initializes the PickupCardAction.
        Args:
            card_id (int): ID of the card.
            card_x, card_y (int): Position of the card on the map.
            card_name (str): Card name (for display).
        """
        self.card_id = card_id
        self.card_x = card_x
        self.card_y = card_y
        self.card_name = card_name

    def __str__(self) -> str:
        return f"Pickup card '{self.card_name}' at ({self.card_x}, {self.card_y})"


class SummonAction(MonsterHuntAction):
    """Summons a monster from a card in the player's hand."""

    def __init__(self, card_id: int, summon_x: int, summon_y: int, card_name: str) -> None:
        """Initializes the SummonAction.
        Args:
            card_id (int): ID of the card to summon from.
            summon_x, summon_y (int): Position to summon the monster to.
            card_name (str): Card name (for display).
        """
        self.card_id = card_id
        self.summon_x = summon_x
        self.summon_y = summon_y
        self.card_name = card_name

    def __str__(self) -> str:
        return f"Summon '{self.card_name}' at ({self.summon_x}, {self.summon_y})"


class SkipAction(MonsterHuntAction):
    """Skips the turn — used as a fallback when no better action exists."""

    def __str__(self) -> str:
        return "Skip turn"


# ─── Actions Function ─────────────────────────────────────────────────────────

# Maximum number of move destinations to consider in minimax (pruning).
# Increasing this makes the bot smarter but slower.
MAX_MOVE_CANDIDATES = 8


class MonsterHuntActionsFunction(ActionsFunction):
    """
    Returns all legal actions for the current player in the Monster Hunt game.
    Priority order: attack > use healing item > summon > move > pickup card > skip.
    Equivalent to XOActionsFunction in exercise-07.
    """

    def actions(self, game_state: MonsterHuntState) -> List[MonsterHuntAction]:
        """Returns all legal actions for the current player.
        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            List[MonsterHuntAction]: All legal actions, best-first ordered.
        """
        board: GameBoardState = game_state.state
        me: Player = board.getPlayerById(game_state.player_to_move)
        if not me or not board.Map:
            return [SkipAction()]

        actions = []

        # 1. ATTACK — if any enemy is within attack range, add attack actions
        opp = board.getOpponentOf(me.Id)
        if opp and opp.is_alive():
            if is_in_attack_range(me.Position.X, me.Position.Y,
                                  opp.Position.X, opp.Position.Y,
                                  me.AttackRange):
                actions.append(AttackAction(opp.Id, opp.Position.X, opp.Position.Y))

        # Attack opponent's monsters too
        for monster in board.get_all_monsters():
            if monster.SummonedByPlayerId != me.Id:  # not my own monster
                if is_in_attack_range(me.Position.X, me.Position.Y,
                                      monster.Position.X, monster.Position.Y,
                                      me.AttackRange):
                    actions.append(AttackAction(monster.Id,
                                                monster.Position.X, monster.Position.Y))

        # 2. USE ITEM — healing items are valuable (use when low on HP)
        for item in me.Inventory:
            actions.append(UseItemAction(item.Id, item.Name))

        # 3. SUMMON — if we have cards ready (not on cooldown)
        if board.Map:
            for card in me.Cards:
                if not card.OnCooldown and card.Uses and card.Uses > 0:
                    # Summon to adjacent passable tiles
                    for _, nx, ny in board.Map.get_passable_neighbors(
                            me.Position.X, me.Position.Y):
                        actions.append(SummonAction(card.Id, nx, ny, card.Name))
                        break  # one summon position per card to limit branching

        # 4. PICKUP CARD — if adjacent to a card on the map
        for card, cx, cy in board.get_cards_on_map():
            if manhattan_distance(me.Position.X, me.Position.Y, cx, cy) <= 1:
                actions.append(PickupCardAction(card.Id, cx, cy, card.Name))

        # 5. MOVE — find best movement candidates
        move_actions = self._get_move_actions(me, opp, board)
        actions.extend(move_actions)

        # 6. SKIP — always available as fallback
        actions.append(SkipAction())

        return actions

    def _get_move_actions(self, me: Player, opp: Optional[Player],
                           board: GameBoardState) -> List[MoveAction]:
        """Generates move action candidates, limited to MAX_MOVE_CANDIDATES.
        Prefers moves towards: opponent, items, monster cards.
        Args:
            me (Player): Current player.
            opp (Player): Opponent player.
            board (GameBoardState): Current board state.
        Returns:
            List[MoveAction]: Move action candidates.
        """
        if not board.Map:
            return []

        # Positions blocked by entities (can't move through them)
        blocked = set()
        for p in board.Players:
            if p.Id != me.Id:
                blocked.add((p.Position.X, p.Position.Y))
        for monster in board.get_all_monsters():
            blocked.add((monster.Position.X, monster.Position.Y))

        reachable = find_legal_move_positions(
            board.Map, me.Position.X, me.Position.Y,
            me.MaxMoveDistance, blocked
        )
        reachable.discard((me.Position.X, me.Position.Y))  # can't "move" to current pos

        if not reachable:
            return []

        # Score each reachable position by strategic value
        scored = []
        for (x, y) in reachable:
            score = self._score_position(x, y, me, opp, board)
            scored.append((score, x, y))

        scored.sort(reverse=True)
        return [MoveAction(x, y) for _, x, y in scored[:MAX_MOVE_CANDIDATES]]

    def _score_position(self, x: int, y: int, me: Player,
                         opp: Optional[Player], board: GameBoardState) -> float:
        """Quick heuristic to rank move destinations (used for move pruning).
        Args:
            x, y: Candidate position.
            me, opp: Players.
            board: Current board state.
        Returns:
            float: Higher = better destination.
        """
        score = 0.0

        # Prefer getting close to opponent (to attack next turn)
        if opp:
            dist_to_opp = manhattan_distance(x, y, opp.Position.X, opp.Position.Y)
            score -= dist_to_opp * 3.0  # closer = better

        # Prefer tiles with items
        if board.Map:
            tile = board.Map.get_tile(x, y)
            if tile and tile.Item:
                score -= 100.0  # item tiles are not legal move destinations

            # Prefer tiles adjacent to items, since pickup happens from a neighboring tile
            for item, ix, iy in board.get_items_on_map():
                dist = manhattan_distance(x, y, ix, iy)
                if dist == 1:
                    score += 30.0
                elif dist == 2:
                    score += 10.0
                else:
                    score += max(0.0, 4.0 - dist)

            # Prefer tiles near monster cards (to summon later)
            for card, cx, cy in board.get_cards_on_map():
                dist = manhattan_distance(x, y, cx, cy)
                score += max(0.0, 8.0 - dist * 2.0)

        return score


# ─── Result Function ──────────────────────────────────────────────────────────

HEALING_POTION_HP = 50  # From presentation: Healing Potion = +50 HP


class MonsterHuntResultFunction(ResultFunction):
    """
    Simulates the effect of an action on the game state.
    Used by the minimax engine to explore the game tree.
    Equivalent to XOResultFunction in exercise-07.
    """

    def result(self, game_state: MonsterHuntState, action: MonsterHuntAction) -> MonsterHuntState:
        """Applies the action and returns the resulting game state.
        Args:
            game_state (MonsterHuntState): The current game state.
            action (MonsterHuntAction): The action to apply.
        Returns:
            MonsterHuntState: The resulting game state.
        """
        new_board: GameBoardState = game_state.state.clone()
        me: Player = new_board.getPlayerById(game_state.player_to_move)

        if isinstance(action, MoveAction):
            me.Position = Position(X=action.to_x, Y=action.to_y)

        elif isinstance(action, AttackAction):
            # Find target: could be opponent player or a monster
            target_player = new_board.getPlayerById(action.target_id)
            if target_player:
                target_player.Health = max(0, target_player.Health - me.AttackPower)
            else:
                # Find monster in map tiles
                for tile in (new_board.Map.Grid if new_board.Map else []):
                    if (tile.Entity and isinstance(tile.Entity, Monster)
                            and tile.Entity.Id == action.target_id):
                        tile.Entity.Health = max(0, tile.Entity.Health - me.AttackPower)
                        if tile.Entity.Health <= 0:
                            tile.Entity = None
                        break

        elif isinstance(action, UseItemAction):
            # Find and apply item from inventory
            for item in me.Inventory:
                if item.Id == action.item_id:
                    if item.ItemType == ITEM_HEALING:
                        me.Health = min(me.MaxHealth, me.Health + HEALING_POTION_HP)
                    # Other items (crowd control, attack buffs) are complex;
                    # for minimax we just model healing precisely
                    me.Inventory.remove(item)
                    break

        elif isinstance(action, PickupCardAction):
            # Remove card from map tile, add to player's hand
            if new_board.Map:
                for tile in new_board.Map.Grid:
                    if (tile.MonsterCard and tile.MonsterCard.Id == action.card_id
                            and tile.Position.X == action.card_x
                            and tile.Position.Y == action.card_y):
                        me.Cards.append(tile.MonsterCard)
                        tile.MonsterCard = None
                        break

        elif isinstance(action, SummonAction):
            # Place monster on map (simplified — we don't track monster turns in minimax)
            for card in me.Cards:
                if card.Id == action.card_id:
                    card.OnCooldown = True
                    card.CooldownCounter = 0
                    break

        # Advance to the next player's turn
        new_board.TurnCounter += 1
        opp = new_board.getOpponentOf(game_state.player_to_move)
        next_player = opp.Id if opp else game_state.player_to_move
        return MonsterHuntState(new_board, next_player)


# ─── Game ─────────────────────────────────────────────────────────────────────

class MonsterHuntGame(Game):
    """
    Monster Hunt game using minimax with alpha-beta pruning.
    Our agent is the maximizing player.
    Equivalent to XOGame in exercise-07.
    """

    def __init__(self, actions_function, result_function,
                 my_player_id: int = None, **kwargs) -> None:
        """Initializes the MonsterHuntGame.
        Args:
            actions_function: The actions function.
            result_function: The result function.
            my_player_id (int): Our agent's player ID.
        """
        super().__init__(actions_function, result_function, **kwargs)
        self.my_player_id = my_player_id

    def is_terminal(self, game_state: MonsterHuntState) -> bool:
        """Returns True if the game is over.
        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            bool: True if terminal.
        """
        board: GameBoardState = game_state.state
        if board.isGameOver():
            return True
        # Also terminal if any player is dead (killed in simulation)
        for p in board.Players:
            if not p.is_alive():
                return True
        return False

    def compute_utility(self, game_state: MonsterHuntState) -> float:
        """
        Heuristic evaluation — called at terminal states and depth cutoff.
        Higher value = better for our agent.

        Components:
          1. HP ratio difference   — most important (mirrors win condition)
          2. Level / XP advantage  — more XP = stronger player
          3. Item advantage        — healing items can save a fight
          4. Card / monster value  — summoned monsters deal damage
          5. Attack opportunity    — being in range to attack next turn
          6. Proximity to items    — more items = future advantage

        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            float: Utility value for our agent.
        """
        board: GameBoardState = game_state.state
        my_id = self.my_player_id

        me: Optional[Player] = board.getPlayerById(my_id)
        opp: Optional[Player] = board.getOpponentOf(my_id)

        if not me or not opp:
            return 0.0

        utility = 0.0

        # 1. HP ratio (primary win condition after 100 turns)
        my_hp_ratio  = me.Health  / max(me.MaxHealth, 1)
        opp_hp_ratio = opp.Health / max(opp.MaxHealth, 1)
        utility += (my_hp_ratio - opp_hp_ratio) * 200.0

        # Terminal cases: dead player
        if not me.is_alive():
            return -10000.0
        if not opp.is_alive():
            return +10000.0

        # 2. Level / XP advantage
        utility += (me.Level - opp.Level) * 30.0
        utility += (me.Xp - opp.Xp) * 0.5

        # 3. Item advantage (count healing items especially)
        for item in me.Inventory:
            if item.ItemType == ITEM_HEALING:
                utility += 25.0
            else:
                utility += 10.0
        for item in opp.Inventory:
            if item.ItemType == ITEM_HEALING:
                utility -= 20.0
            else:
                utility -= 8.0

        # 4. Card advantage (ready-to-summon cards)
        for card in me.Cards:
            if not card.OnCooldown:
                utility += 15.0
        for card in opp.Cards:
            if not card.OnCooldown:
                utility -= 12.0

        # 5. Attack opportunity (am I in range to attack opponent?)
        if board.Map:
            if is_in_attack_range(me.Position.X, me.Position.Y,
                                  opp.Position.X, opp.Position.Y,
                                  me.AttackRange):
                utility += 20.0  # can attack next turn

            # 6. Proximity to items on map (closer = more likely to grab them)
            for item, ix, iy in board.get_items_on_map():
                my_dist  = manhattan_distance(me.Position.X, me.Position.Y, ix, iy)
                opp_dist = manhattan_distance(opp.Position.X, opp.Position.Y, ix, iy)
                if my_dist < opp_dist:
                    utility += 8.0  # I'll reach it first
                elif opp_dist < my_dist:
                    utility -= 6.0

            # Prefer standing next to a card so we can pick it up immediately.
            for card, cx, cy in board.get_cards_on_map():
                dist = manhattan_distance(me.Position.X, me.Position.Y, cx, cy)
                if dist == 1:
                    utility += 35.0
                elif dist == 2:
                    utility += 12.0

        return utility

import copy
from dataclasses import dataclass
from typing import List, Tuple, Optional

from game_algorithms.interfaces import GameState, Action, ActionsFunction, ResultFunction
from game_algorithms.game import Game
from models import GameBoardState, Player, Position
from pathfinding import (
    find_distance_with_search,
    HexGoalTest,
    HexHeuristic,
    HexNearestResourceGoalTest,
)

class XOState(GameState):
    """
    Wraps XOBoard as a GameState (player_to_move is 0 or 1).
    Equivalent to XOState in exercise-07.
    """

    def __init__(self, board: GameBoardState, player_to_move: int) -> None:
        """Initializes the XOState.
        Args:
            board (GameBoardState): The current board.
            player_to_move (int): Id of the player whose turn it is (0 or 1).
        """
        super().__init__(board, player_to_move)

    def __str__(self) -> str:
        return f"{self.state}\n  Player to move: {self.player_to_move}"


# ─── Actions ──────────────────────────────────────────────────────────────────

class XOAction(Action):
    """Base class for all XO actions."""
    pass


class MoveAction(XOAction):
    """Moves the player to an adjacent hex cell (costs 1 energy)."""

    def __init__(self, to_row: int, to_col: int) -> None:
        """Initializes the MoveAction.
        Args:
            to_row (int): Destination row.
            to_col (int): Destination column.
        """
        self.to_row = to_row
        self.to_col = to_col

    def __str__(self) -> str:
        return f"Move to ({self.to_row}, {self.to_col})"


# ─── Actions Function ─────────────────────────────────────────────────────────

class XOActionsFunction(ActionsFunction):
    """
    Returns all legal actions for the current player.
    Equivalent to XOActionsFunction in exercise-07.
    """

    def actions(self, game_state: XOState) -> List[XOAction]:
        """Returns all legal actions for the current player.
        Args:
            game_state (XOState): The current game state.
        Returns:
            List[XOAction]: All legal actions.
        """
        board: GameBoardState = game_state.state
        player: Player = board.getPlayerById(game_state.player_to_move)
        available = []


        for r, c in board.get_neighboring_tiles(player.getPosition()):
            available.append(MoveAction(r, c))

        return available


# ─── Result Function ──────────────────────────────────────────────────────────

class XOResultFunction(ResultFunction):
    """
    Applies an action to a game state and returns the resulting state.
    Equivalent to XOResultFunction in exercise-07.
    """

    def result(self, game_state: XOState, action: XOAction) -> XOState:
        """Applies the action to the game state.
        Args:
            game_state (XOState): The current game state.
            action (XOAction): The action to apply.
        Returns:
            XOState: The resulting game state.
        """
        new_board: GameBoardState = game_state.state.clone()
        player: Player = new_board.getPlayerById(game_state.player_to_move)

        if isinstance(action, MoveAction):
            player.Position = Position(X=action.to_row, Y=action.to_col)
            cell = new_board.board.get_cell(action.to_row, action.to_col)

        # Advance to next player's turn
        new_board.TurnCounter += 1
        next_player = 1 - game_state.player_to_move
        return XOState(new_board, next_player)


# ─── Game ─────────────────────────────────────────────────────────────────────

class XOGame(Game):
    """
    XO game using minimax with alpha-beta pruning.
    Our agent is always player 0 (the maximizing player).
    Equivalent to XOGame in exercise-07.
    """

    MY_PLAYER_ID = 0

    def is_terminal(self, game_state: XOState) -> bool:
        """Returns True if the game is over.
        Args:
            game_state (XOState): The current game state.
        Returns:
            bool: True if terminal.
        """
        return game_state.state.isGameOver()

    def compute_utility(self, game_state: XOState) -> float:
        """
        Heuristic evaluation function — called both at terminal states and
        at depth cutoff (as in exercise-07's Game.compute_utility).
        Higher value = better for player 0 (our AI).

        Components:
          1. Score difference        — most important long-term signal
          2. Inventory value         — resources we're holding (not yet scored)
          3. Return-to-base urgency  — prioritize going home when inventory is full
          4. Proximity to resources  — go towards resources when inventory is low

        Args:
            game_state (XOState): The current game state.
        Returns:
            float: The utility value for player 0.
        """
        board: XOBoard = game_state.state
        me: PlayerData = board.get_player(self.MY_PLAYER_ID)
        opp: PlayerData = board.get_opponent(self.MY_PLAYER_ID)

        utility = 0.0

        # 1. Score difference (dominant term)
        utility += (me.score - opp.score) * 100.0

        # 2. Inventory advantage (held resources count towards future score)
        utility += me.inventory * 10.0
        utility -= opp.inventory * 8.0   # slightly less weight — opponent hasn't deposited yet

        # 3. Return-to-base urgency (use A* distance for accuracy)
        if me.inventory > 0:
            dist_home = find_distance_with_search(
                board=board.board,
                start=me.position,
                goal_test=HexGoalTest(me.home_base),
                search_algorithm="astar",
                heuristic_function=HexHeuristic(me.home_base),
            ) or 0
            fullness = me.inventory / me.max_inventory
            # The fuller our inventory, the more urgent the return trip
            utility += fullness * max(0.0, 25.0 - dist_home * 4.0)

        # 4. Proximity to nearest resource (when inventory isn't full)
        if me.inventory < me.max_inventory:
            dist_resource = find_distance_with_search(
                board=board.board,
                start=me.position,
                goal_test=HexNearestResourceGoalTest(board.board),
                search_algorithm="bfs",
                heuristic_function=None,
            )
            if dist_resource is not None:
                utility += max(0.0, 15.0 - dist_resource * 2.0)

        # 5. Energy ratio (low energy limits future moves)
        energy_ratio = me.energy / me.max_energy
        utility += energy_ratio * 8.0
        if me.energy < 3:
            utility -= 30.0   # hard penalty for near-zero energy

        return utility



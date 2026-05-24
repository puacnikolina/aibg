"""
AIBG V5.0 — Monster Hunt Bot
Usage: python main.py <server_url> <game_id> <bot_name>
Example: python main.py http://localhost:8080 game123 MojBot
"""

import requests
import sys
import time

from models import GameBoardState, ITEM_SCROLL
from game_definition import (MonsterHuntState, MonsterHuntGame,
                              MonsterHuntActionsFunction, MonsterHuntResultFunction,
                              MoveAction, AttackAction, UseItemAction,
                              PickupAction, SummonAction)
from agent import AIAgent


# ─── API Client ───────────────────────────────────────────────────────────────

class BotClient:
    """Handles all HTTP communication with the AIBG game server."""

    def __init__(self, server_url: str, game_id: str, bot_name: str) -> None:
        """Initializes the BotClient.
        Args:
            server_url (str): Base URL of the game server (e.g. http://localhost:8080).
            game_id (str): The game session ID.
            bot_name (str): This bot's display name.
        """
        self.server_url = server_url.rstrip('/')
        self.game_id = game_id
        self.bot_name = bot_name
        self.player_id = None
        # Last PUT response info (status code and text) for diagnostics
        self.last_put_status = None
        self.last_put_text = None

    def get_game_state(self) -> dict:
        """Fetches and returns the current game state as a dict.
        Returns:
            dict: Raw API response, or None on failure.
        """
        try:
            url = f"{self.server_url}/game/state/{self.game_id}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"[API] get_game_state error: {e}")
        return None

    def find_my_player_id(self, raw_state: dict) -> bool:
        """Finds and stores our player ID from the game state.
        Args:
            raw_state (dict): Raw API response.
        Returns:
            bool: True if our player was found.
        """
        players = raw_state.get('Players', {})
        for player_id, player in players.items():
            if player.get('Name') == self.bot_name:
                self.player_id = player.get('Id')
                print(f"[Init] Found as Player ID={self.player_id}, Name={self.bot_name}")
                return True
        return False

    def send_move(self, to_x: int, to_y: int) -> dict:
        """Sends a move action to the server.
        Args:
            to_x (int): Destination X.
            to_y (int): Destination Y.
        Returns:
            dict: Updated game state from server response.
        """
        # PUT /player/move/gameId/{gameId}
        url = f"{self.server_url}/player/move/gameId/{self.game_id}"
        payload = {
            "PlayerId": self.player_id,
            "newPosition": {"X": to_x, "Y": to_y}
        }
        return self._put(url, payload)

    def send_attack(self, attacker_id: int, target_id: int) -> dict:
        """Sends an attack action to the server.
        Args:
            attacker_id (int): Our player's ID.
            target_id (int): Target entity's ID.
        Returns:
            dict: Updated game state from server response.
        """
        # PUT /player/{attackerId}/attack/{attackedId}/gameId/{gameId}
        url = (f"{self.server_url}/player/{attacker_id}"
               f"/attack/{target_id}/gameId/{self.game_id}")
        return self._put(url, None)

    def send_use_item(self, player_id: int, item_id: int) -> dict:
        """Sends a use-item action to the server.
        Args:
            player_id (int): Our player's ID.
            item_id (int): Item's ID.
        Returns:
            dict: Updated game state from server response.
        """
        # PUT /player/{playerId}/use-item/{itemId}/gameId/{gameId}
        url = (f"{self.server_url}/player/{player_id}"
               f"/use-item/{item_id}/gameId/{self.game_id}")
        return self._put(url, None)

    def send_pickup(self, player_id: int, field_info) -> dict:
        """Sends a pickup action to the server.
        Args:
            player_id (int): Our player's ID.
            field_info: Full field payload to pick up from.
        Returns:
            dict: Updated game state from server response.
        """
        # PUT /player/pickup/{playerId}/gameId/{gameId}
        url = f"{self.server_url}/player/pickup/{player_id}/gameId/{self.game_id}"
        payload = field_info.to_dict() if hasattr(field_info, "to_dict") else field_info
        return self._put(url, payload)

    def send_summon(self, player_id: int, card_id: int,
                    summon_x: int, summon_y: int) -> dict:
        """Sends a summon-monster action to the server.
        Args:
            player_id (int): Our player's ID.
            card_id (int): Card ID to summon from.
            summon_x, summon_y (int): Position to summon the monster to.
        Returns:
            dict: Updated game state from server response.
        """
        # PUT /map/{playerId}/summon/{cardId}/gameId/{gameId}
        url = (f"{self.server_url}/map/{player_id}"
               f"/summon/{card_id}/gameId/{self.game_id}")
        payload = {"X": summon_x, "Y": summon_y}
        return self._put(url, payload)

    def _put(self, url: str, payload) -> dict:
        """Internal helper for PUT requests. All PUT endpoints return updated state.
        Args:
            url (str): Endpoint URL.
            payload: JSON body, or None for no body.
        Returns:
            dict: Server response, or None on failure.
        """
        try:
            if payload is not None:
                response = requests.put(url, json=payload, timeout=10)
            else:
                response = requests.put(url, timeout=10)
            if response.status_code == 200:
                # clear last status on success
                self.last_put_status = 200
                self.last_put_text = None
                return response.json()
            else:
                self.last_put_status = response.status_code
                self.last_put_text = response.text
                print(f"[API] PUT {url} failed: {response.status_code} — {response.text}")
        except Exception as e:
            print(f"[API] PUT error: {e}")
            # network errors treated as transient
            self.last_put_status = None
            self.last_put_text = str(e)
        return None


# ─── Action → API Call ────────────────────────────────────────────────────────

def execute_action(action, client: BotClient) -> dict:
    """Converts a minimax action into the appropriate API call.
    Args:
        action (MonsterHuntAction): The action chosen by minimax.
        client (BotClient): The API client.
    Returns:
        dict: Updated game state from the server.
    """
    if isinstance(action, MoveAction):
        print(f"[Bot] → Move to ({action.to_x}, {action.to_y})")
        return client.send_move(action.to_x, action.to_y)

    elif isinstance(action, AttackAction):
        print(f"[Bot] → Attack entity {action.target_id}")
        return client.send_attack(client.player_id, action.target_id)

    elif isinstance(action, UseItemAction):
        print(f"[Bot] → Use item '{action.item_name}' (id={action.item_id})")
        return client.send_use_item(client.player_id, action.item_id)

    elif isinstance(action, PickupAction):
        print(f"[Bot] → {action}")
        return client.send_pickup(client.player_id, action.field_info)

    elif isinstance(action, SummonAction):
        print(f"[Bot] → Summon '{action.card_name}' at ({action.summon_x}, {action.summon_y})")
        return client.send_summon(client.player_id, action.card_id,
                                  action.summon_x, action.summon_y)

    if action is None:
        print("[Bot] → No legal action (skipping)")
        return None

    print(f"[Bot] Unknown action type: {type(action)}")
    return None


# ─── Game Setup ───────────────────────────────────────────────────────────────

def build_game(my_player_id: int) -> MonsterHuntGame:
    """Creates the MonsterHuntGame (minimax engine) for our agent.
    Args:
        my_player_id (int): Our player's ID.
    Returns:
        MonsterHuntGame: Configured game instance.
    """
    return MonsterHuntGame(
        actions_function=MonsterHuntActionsFunction(),
        result_function=MonsterHuntResultFunction(),
        my_player_id=my_player_id,
        max_player=True,
        alpha_beta_prunning=True,
        max_depth=1,  # increase to 4 if turns are slow enough; 3 is safe for 20h
    )


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <server_url> <game_id> <bot_name>")
        sys.exit(1)

    server_url, game_id, bot_name = sys.argv[1], sys.argv[2], sys.argv[3]
    client = BotClient(server_url, game_id, bot_name)

    # ── 1. Connect and find our player ID ─────────────────────────────────────
    print(f"[Init] Connecting to {server_url}, game={game_id}, name={bot_name}")
    raw_state = None
    while not raw_state or not client.find_my_player_id(raw_state):
        raw_state = client.get_game_state()
        time.sleep(0.5)

    my_id = client.player_id

    # ── 2. Build the minimax engine ───────────────────────────────────────────
    game = build_game(my_id)
    agent = AIAgent(game, my_id, bot_name)

    print(f"[Init] Ready. Playing as Player {my_id}")

    # ── 3. Main game loop ─────────────────────────────────────────────────────
    try:
        while True:
            raw_state = client.get_game_state()
            if not raw_state:
                time.sleep(0.3)
                continue

            board = GameBoardState.getState(raw_state)

            if board.isGameOver():
                me = board.getPlayerById(my_id)
                opp = board.getOpponentOf(my_id)
                print(f"\n[GAME OVER] Final: Me={me.Health if me else 0}HP  "
                      f"Opp={opp.Health if opp else 0}HP")
                break

            if not board.isMyTurn(my_id):
                # Not our turn — wait for server to advance
                time.sleep(0.2)
                continue

            # ── Our turn: run minimax and execute action ───────────────────
            print(f"\n[Turn {board.TurnCounter}] {board}")
            current_state = MonsterHuntState(board, my_id)
            # Inject locally remembered pickups so the next-turn scroll use rule is visible to minimax.
            try:
                my_player = current_state.state.getPlayerById(my_id)
                if my_player is not None:
                    my_player.RecentlyPickedItems = list(agent.recently_picked_items)
            except Exception:
                pass
            action = agent.make_move(current_state)

            response = execute_action(action, client)

            # If the action failed (e.g., 409 Not Your Turn or server error), poll server until state changes
            if response is None:
                prev_turn = board.TurnCounter
                # Wait for server to process or advance the turn. Poll for up to ~8 seconds.
                waited = 0.0
                poll_interval = 0.5
                max_wait = 8.0
                while waited < max_wait:
                    raw_state = client.get_game_state()
                    if raw_state:
                        new_board = GameBoardState.getState(raw_state)
                        # If turn advanced or it's no longer our turn, stop waiting
                        if new_board.TurnCounter != prev_turn or not new_board.isMyTurn(my_id):
                            board = new_board
                            break
                    time.sleep(poll_interval)
                    waited += poll_interval
                # After polling, continue main loop (will recompute action if it's still our turn)
                continue

            # On success, update agent-side recently-picked bookkeeping
            if isinstance(action, PickupAction):
                # If we picked up a scroll, schedule it for use next turn
                try:
                    if action.field_info and action.field_info.Item and action.field_info.Item.ItemType == ITEM_SCROLL:
                        if action.field_info.Item.Id not in agent.recently_picked_items:
                            agent.recently_picked_items.append(action.field_info.Item.Id)
                except Exception:
                    pass

            if isinstance(action, UseItemAction):
                # If we used a scheduled item, remove it from the schedule
                try:
                    if action.item_id in agent.recently_picked_items:
                        agent.recently_picked_items.remove(action.item_id)
                except ValueError:
                    pass

            # Server returned updated state; small delay to avoid hammering
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[Bot] Stopped by user.")


if __name__ == "__main__":
    main()

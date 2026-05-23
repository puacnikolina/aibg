
import requests
import sys
import time
import models as stateObj
from directions import Directions

def move(id, Direction, steps, state):
     #URL: PUT http://localhost:8080/player/move/gameId/{gameId}
    url = f"{bot.server_url}/player/move/gameId/{bot.game_id}"

    player = state.getPlayerById(id)

    if Direction == Directions.Up:
        newX = player.Position.X
        newY = player.Position.Y + steps
    elif Direction == Directions.Down:
         newX = player.Position.X 
         newY = player.Position.Y - steps
    elif Direction == Directions.Left:
         newX = player.Position.X - steps
         newY = player.Position.Y
    elif Direction == Directions.Right:
         newX = player.Position.X + steps
         newY = player.Position.Y

    payload = {
        "PlayerId": bot.player_id,
        "newPosition":  { "X": newX, "Y": newY }
    }

    response = requests.put(url, json=payload, timeout=50)
    if response.status_code == 200:
        print("Move successful")
    else:
        print(f"Move failed: {response.status_code} - {response.text}")

class BotTemplate:
    def __init__(self, server_url, game_id, bot_name):
        self.server_url = server_url.rstrip('/')
        self.game_id = game_id
        self.bot_name = bot_name
        self.player_id = None
    
    def get_game_state(self):
        url = f"{self.server_url}/game/state/{self.game_id}"
        response = requests.get(url, timeout=5)
        return response.json() if response.status_code == 200 else None
    
    def find_my_player_id(self, game_state):
        players = game_state.get('Players', {})
        for player_id, player in players.items():
            if player.get('Name') == self.bot_name:
                self.player_id = player.get('Id')
                return True
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python bot_template.py <server_url> <game_id> <bot_name>")
        sys.exit(1)
    
    bot = BotTemplate(sys.argv[1], sys.argv[2], sys.argv[3])
    
    while not (state := bot.get_game_state()) or not bot.find_my_player_id(state):
        time.sleep(0.5)
    
    print(f"Connected as Player {bot.player_id}\n")
    
    #returns the game state as a GameState object from json file
    gameState = stateObj.GameBoardState.getState(bot.get_game_state())

    try:
        while gameState and not stateObj.GameBoardState.isGameOver(gameState):
            if stateObj.GameBoardState.isMyTurn(gameState, bot.player_id):
                move(bot.player_id, Directions.Left, 2, gameState)
                time.sleep(0.5)
                gameState = stateObj.GameBoardState.getState(bot.get_game_state())
            else:
                time.sleep(0.5)
                gameState = stateObj.GameBoardState.getState(bot.get_game_state())
    except KeyboardInterrupt:
        print("\nBot stopped by user")

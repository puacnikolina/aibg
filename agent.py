import random
from abc import abstractmethod

from game_algorithms.interfaces import GameState, Action
from game_definition import XOState, XOAction
from abc import ABC, abstractmethod

class Agent(ABC):
    """Abstract base class for all XO agents. Equivalent to Agent in exercise-07."""

    def __init__(self, game, player_id: int, name: str) -> None:
        """Initializes the Agent.
        Args:
            game: The XOGame instance.
            player_id (int): This agent's player id (0 or 1).
            name (str): Display name of the agent.
        """
        self.game = game
        self.player_id = player_id
        self.name = name

    @abstractmethod
    def make_move(self, game_state: XOState) -> XOAction:
        """Returns the action this agent wants to take.
        Args:
            game_state (XOState): The current game state.
        Returns:
            XOAction: The chosen action.
        """
        pass

    def __str__(self) -> str:
        return self.name


class AIAgent(Agent):
    """
    Minimax agent that uses game.minimax_decision() to choose actions.
    Equivalent to AI in exercise-07.
    """

    def make_move(self, game_state: XOState) -> XOAction:
        """Runs minimax search and returns the best action.
        Args:
            game_state (XOState): The current game state.
        Returns:
            XOAction: The best action found by minimax.
        """
        print(f"[{self.name}] Running minimax (depth={self.game.max_depth}, "
              f"alpha-beta={self.game.alpha_beta_prunning})...")
        action = self.game.minimax_decision(game_state)
        print(f"[{self.name}] Chose: {action}")
        return action


class RandomAgent(Agent):
    """
    Agent that picks a random valid action each turn.
    Useful as a baseline opponent for testing.
    """

    def make_move(self, game_state: XOState) -> XOAction:
        """Returns a randomly chosen valid action.
        Args:
            game_state (XOState): The current game state.
        Returns:
            XOAction: A random valid action.
        """
        actions = self.game.actions_function.actions(game_state)
        chosen = random.choice(actions)
        print(f"[{self.name}] Chose: {chosen}")
        return chosen

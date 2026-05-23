import random
from abc import ABC, abstractmethod

from game_algorithms.interfaces import Action
from game_definition import MonsterHuntState, MonsterHuntAction


class Agent(ABC):
    """Abstract base class for all Monster Hunt agents. Equivalent to Agent in exercise-07."""

    def __init__(self, game, player_id: int, name: str) -> None:
        """Initializes the Agent.
        Args:
            game: The MonsterHuntGame instance.
            player_id (int): This agent's player ID.
            name (str): Display name of the agent.
        """
        self.game = game
        self.player_id = player_id
        self.name = name

    @abstractmethod
    def make_move(self, game_state: MonsterHuntState) -> MonsterHuntAction:
        """Returns the action this agent wants to take.
        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            MonsterHuntAction: The chosen action.
        """
        pass

    def __str__(self) -> str:
        return self.name


class AIAgent(Agent):
    """
    Minimax agent that uses game.minimax_decision() to choose actions.
    Equivalent to AI in exercise-07.
    """

    def make_move(self, game_state: MonsterHuntState) -> MonsterHuntAction:
        """Runs minimax search and returns the best action.
        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            MonsterHuntAction: The best action found by minimax.
        """
        print(f"[{self.name}] Running minimax "
              f"(depth={self.game.max_depth}, alpha-beta={self.game.alpha_beta_prunning})...")
        action = self.game.minimax_decision(game_state)
        if action is None:
            from game_definition import SkipAction
            action = SkipAction()
        print(f"[{self.name}] Decision: {action}")
        return action


class RandomAgent(Agent):
    """Random agent for testing — picks a random valid action each turn."""

    def make_move(self, game_state: MonsterHuntState) -> MonsterHuntAction:
        """Returns a randomly chosen valid action.
        Args:
            game_state (MonsterHuntState): The current game state.
        Returns:
            MonsterHuntAction: A random valid action.
        """
        actions = self.game.actions_function.actions(game_state)
        chosen = random.choice(actions)
        print(f"[{self.name}] Random: {chosen}")
        return chosen

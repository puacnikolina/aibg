from abc import ABC, abstractmethod

from game_algorithms.interfaces import Action
from game_definition import MonsterHuntState, MonsterHuntAction


class Agent(ABC):
    """Abstract base class for all Monster Hunt agents."""

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
        self.recently_picked_items = []

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
    Minimax agent that uses `game.minimax_decision()` to choose actions.
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
            return None
        print(f"[{self.name}] Decision: {action}")
        return action
    

from typing import List, Tuple, Optional

from search_algorithms.interfaces import (State, Action, ActionsFunction, ResultFunction,
                                          GoalTestFunction, StepCostFunction, HeuristicFunction)
from search_algorithms.problem import Problem
from search_algorithms.astar import AStar
from search_algorithms.bfs import BFS


# ─── Search State ─────────────────────────────────────────────────────────────

class HexPosition(State):
    """Represents a position on the hex grid as a single-agent search state."""

    def __init__(self, row: int, col: int) -> None:
        """Initializes the HexPosition.
        Args:
            row (int): Row index.
            col (int): Column index.
        """
        self.row = row
        self.col = col

    def __eq__(self, other: object) -> bool:
        return isinstance(other, HexPosition) and self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def __str__(self) -> str:
        return f"({self.row}, {self.col})"

    def __lt__(self, other: "HexPosition") -> bool:
        # Required for heapq when f-values are equal
        return (self.row, self.col) < (other.row, other.col)


# ─── Action ───────────────────────────────────────────────────────────────────

class HexMoveAction(Action):
    """Represents moving to an adjacent hex cell in pathfinding."""

    def __init__(self, to_row: int, to_col: int) -> None:
        """Initializes the HexMoveAction.
        Args:
            to_row (int): Destination row.
            to_col (int): Destination column.
        """
        self.to_row = to_row
        self.to_col = to_col

    def __str__(self) -> str:
        return f"Move to ({self.to_row}, {self.to_col})"


# ─── Actions Function ─────────────────────────────────────────────────────────

class HexActionsFunction(ActionsFunction):
    """Returns all passable neighbor positions as move actions."""

    def __init__(self, board: HexBoard, blocked_positions: set = None) -> None:
        """Initializes the HexActionsFunction.
        Args:
            board (HexBoard): The game board.
            blocked_positions (set): Extra positions to treat as blocked (e.g. opponent location).
        """
        self.board = board
        self.blocked_positions = blocked_positions or set()

    def actions(self, state: HexPosition) -> List[HexMoveAction]:
        """Returns all valid move actions from the given position.
        Args:
            state (HexPosition): The current position.
        Returns:
            List[HexMoveAction]: List of valid moves.
        """
        return [HexMoveAction(r, c)
                for r, c in self.board.get_neighbors(state.row, state.col)
                if (r, c) not in self.blocked_positions]


# ─── Result Function ──────────────────────────────────────────────────────────

class HexResultFunction(ResultFunction):
    """Applies a move action to a hex position."""

    def result(self, state: HexPosition, action: HexMoveAction) -> HexPosition:
        """Returns the new position after applying the move.
        Args:
            state (HexPosition): The current position.
            action (HexMoveAction): The move to apply.
        Returns:
            HexPosition: The new position.
        """
        return HexPosition(action.to_row, action.to_col)


# ─── Goal Test ────────────────────────────────────────────────────────────────

class HexGoalTest(GoalTestFunction):
    """Checks whether the current position equals the goal."""

    def __init__(self, goal: Tuple[int, int]) -> None:
        """Initializes the HexGoalTest.
        Args:
            goal (Tuple[int, int]): The goal position (row, col).
        """
        self.goal = goal

    def is_goal_state(self, state: HexPosition) -> bool:
        """Returns True if the current position is the goal.
        Args:
            state (HexPosition): The current position.
        Returns:
            bool: True if at goal.
        """
        return (state.row, state.col) == self.goal
    
    
class HexNearestResourceGoalTest(GoalTestFunction):
    """Goal test for reaching any cell containing resource."""

    def __init__(self, board: HexBoard) -> None:
        self.board = board

    def is_goal_state(self, state: HexPosition) -> bool:
        return self.board.get_cell(state.row, state.col).resource_value > 0


# ─── Step Cost ────────────────────────────────────────────────────────────────

class HexStepCost(StepCostFunction):
    """Each step costs 1 (uniform cost)."""

    def cost(self, state: HexPosition, action: HexMoveAction, state1: HexPosition) -> float:
        """Returns the cost of taking the given action.
        Args:
            state (HexPosition): The current position.
            action (HexMoveAction): The action taken.
            state1 (HexPosition): The resulting position.
        Returns:
            float: The step cost (always 1).
        """
        return 1


# ─── Heuristic ────────────────────────────────────────────────────────────────

class HexHeuristic(HeuristicFunction):
    """
    Admissible and consistent heuristic using exact hex distance
    (cube coordinate conversion). Never overestimates the true cost.
    """

    def __init__(self, goal: Tuple[int, int]) -> None:
        """Initializes the HexHeuristic.
        Args:
            goal (Tuple[int, int]): The goal position (row, col).
        """
        self.goal = goal

    def h(self, state: HexPosition) -> float:
        """Returns the hex distance from state to goal.
        Args:
            state (HexPosition): The current position.
        Returns:
            float: Estimated cost to goal.
        """
        return hex_distance(state.row, state.col, self.goal[0], self.goal[1])


# ─── Utility Functions ────────────────────────────────────────────────────────

def hex_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    """Computes the exact hex grid distance using cube coordinate conversion.
    Args:
        r1, c1 (int): Source position.
        r2, c2 (int): Destination position.
    Returns:
        int: Minimum number of hex steps between the two positions.
    """
    x1 = c1 - (r1 - (r1 & 1)) // 2
    z1 = r1
    y1 = -x1 - z1
    x2 = c2 - (r2 - (r2 & 1)) // 2
    z2 = r2
    y2 = -x2 - z2
    return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))

def find_distance_with_search(board: HexBoard,
                              start: Tuple[int, int],
                              goal_test: GoalTestFunction,
                              blocked_positions: set = None,
                              search_algorithm: str = "astar",
                              heuristic_function: HeuristicFunction = None) -> Optional[int]:
    """Shared distance routine using either A* or BFS over the same problem setup."""
    problem = Problem(
        initial_state=HexPosition(*start),
        actions_function=HexActionsFunction(board, blocked_positions),
        result_function=HexResultFunction(),
        goal_test=goal_test,
        step_cost_function=HexStepCost(),
        heuristic_function=heuristic_function
    )

    if search_algorithm == "astar":
        searcher = AStar(problem)
        actions, _ = searcher.search()
    elif search_algorithm == "bfs":
        searcher = BFS(problem)
        actions = searcher.search()
    else:
        raise ValueError(f"Unsupported search algorithm: {search_algorithm}")

    return len(actions) if actions is not None else None
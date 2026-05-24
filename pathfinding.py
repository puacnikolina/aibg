from typing import List, Tuple, Optional, Set

from search_algorithms.interfaces import (State, Action, ActionsFunction, ResultFunction,
                                          GoalTestFunction, StepCostFunction, HeuristicFunction)
from search_algorithms.problem import Problem
from search_algorithms.astar import AStar
from models import Map, Tile, FIELD_OBSTACLE, FIELD_OBSTACLE_SLOW


# ─── Search State ─────────────────────────────────────────────────────────────

class GridPosition(State):
    """Represents an (X, Y) position on the square grid as a search state."""

    def __init__(self, x: int, y: int) -> None:
        """Initializes the GridPosition.
        Args:
            x (int): X coordinate (column, 0..31).
            y (int): Y coordinate (row, 0..15).
        """
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GridPosition) and self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __lt__(self, other: "GridPosition") -> bool:
        return (self.x, self.y) < (other.x, other.y)


# ─── Action ───────────────────────────────────────────────────────────────────

class GridMoveAction(Action):
    """Represents moving to an adjacent grid tile."""

    def __init__(self, to_x: int, to_y: int) -> None:
        """Initializes the GridMoveAction.
        Args:
            to_x (int): Destination X.
            to_y (int): Destination Y.
        """
        self.to_x = to_x
        self.to_y = to_y

    def __str__(self) -> str:
        return f"Move to ({self.to_x}, {self.to_y})"


# ─── Actions Function ─────────────────────────────────────────────────────────

class GridActionsFunction(ActionsFunction):
    """Returns passable 4-directional neighbors as move actions."""

    def __init__(self, game_map: Map, blocked: Set[Tuple[int, int]] = None) -> None:
        """Initializes the GridActionsFunction.
        Args:
            game_map (Map): The game map.
            blocked (Set): Extra positions to treat as blocked (e.g. walls, entities).
        """
        self.game_map = game_map
        self.blocked = blocked or set()

    def actions(self, state: GridPosition) -> List[GridMoveAction]:
        """Returns all valid move actions from the given position.
        Args:
            state (GridPosition): The current position.
        Returns:
            List[GridMoveAction]: Valid moves.
        """
        result = []
        for _, nx, ny in self.game_map.get_passable_neighbors(state.x, state.y):
            if (nx, ny) not in self.blocked:
                result.append(GridMoveAction(nx, ny))
        return result


# ─── Result Function ──────────────────────────────────────────────────────────

class GridResultFunction(ResultFunction):
    """Applies a move action to a grid position."""

    def result(self, state: GridPosition, action: GridMoveAction) -> GridPosition:
        """Returns the new position after applying the move.
        Args:
            state (GridPosition): The current position.
            action (GridMoveAction): The move to apply.
        Returns:
            GridPosition: The new position.
        """
        return GridPosition(action.to_x, action.to_y)


# ─── Goal Tests ───────────────────────────────────────────────────────────────

class GridGoalTest(GoalTestFunction):
    """Checks whether the current position equals the target."""

    def __init__(self, goal_x: int, goal_y: int) -> None:
        """Initializes the GridGoalTest.
        Args:
            goal_x (int): Goal X coordinate.
            goal_y (int): Goal Y coordinate.
        """
        self.goal_x = goal_x
        self.goal_y = goal_y

    def is_goal_state(self, state: GridPosition) -> bool:
        return state.x == self.goal_x and state.y == self.goal_y


class GridNearestItemGoalTest(GoalTestFunction):
    """Goal test: reach any tile that has an item/powerup."""

    def __init__(self, game_map: Map) -> None:
        self.game_map = game_map

    def is_goal_state(self, state: GridPosition) -> bool:
        tile = self.game_map.get_tile(state.x, state.y)
        return tile is not None and tile.Item is not None


class GridNearestCardGoalTest(GoalTestFunction):
    """Goal test: reach any tile that has a monster card."""

    def __init__(self, game_map: Map) -> None:
        self.game_map = game_map

    def is_goal_state(self, state: GridPosition) -> bool:
        tile = self.game_map.get_tile(state.x, state.y)
        return tile is not None and tile.MonsterCard is not None


# ─── Step Cost ────────────────────────────────────────────────────────────────

class GridStepCost(StepCostFunction):
    """Step cost: 1 normally, 2 for OBSTACLE_SLOW (Snow) tiles."""

    def __init__(self, game_map: Map) -> None:
        self.game_map = game_map

    def cost(self, state: GridPosition, action: GridMoveAction, state1: GridPosition) -> float:
        """Returns the movement cost to enter state1.
        Args:
            state (GridPosition): The current position.
            action (GridMoveAction): The action taken.
            state1 (GridPosition): The resulting position.
        Returns:
            float: Movement cost (1 or 2).
        """
        tile = self.game_map.get_tile(state1.x, state1.y)
        if not tile:
            return 999999
        if tile.FieldType == FIELD_OBSTACLE_SLOW:
            return 2
        if tile.FieldType == FIELD_OBSTACLE:
            return 999999
        if not tile.is_passable():
            return 999999
        return 1


# ─── Heuristic ────────────────────────────────────────────────────────────────

class ManhattanHeuristic(HeuristicFunction):
    """
    Admissible Manhattan distance heuristic for 4-directional grid movement.
    Never overestimates the true cost (since min cost per step is 1).
    """

    def __init__(self, goal_x: int, goal_y: int) -> None:
        """Initializes the ManhattanHeuristic.
        Args:
            goal_x (int): Goal X coordinate.
            goal_y (int): Goal Y coordinate.
        """
        self.goal_x = goal_x
        self.goal_y = goal_y

    def h(self, state: GridPosition) -> float:
        """Returns the Manhattan distance from state to goal.
        Args:
            state (GridPosition): The current position.
        Returns:
            float: Estimated cost to goal.
        """
        return manhattan_distance(state.x, state.y, self.goal_x, self.goal_y)


# ─── Utility Functions ────────────────────────────────────────────────────────

def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Manhattan distance between two grid positions.
    Args:
        x1, y1: Source coordinates.
        x2, y2: Destination coordinates.
    Returns:
        int: Manhattan distance.
    """
    return abs(x1 - x2) + abs(y1 - y2)


def is_in_attack_range(ax: int, ay: int, tx: int, ty: int, attack_range: int) -> bool:
    """Checks whether an attacker at (ax, ay) can reach target at (tx, ty).
    Uses Chebyshev distance (allows diagonal reach within range).
    Args:
        ax, ay: Attacker position.
        tx, ty: Target position.
        attack_range: Attacker's range.
    Returns:
        bool: True if target is within range.
    """
    return max(abs(ax - tx), abs(ay - ty)) <= attack_range


def find_path(game_map: Map, start_x: int, start_y: int,
              goal_x: int, goal_y: int,
              blocked: Set[Tuple[int, int]] = None) -> Optional[List[GridMoveAction]]:
    """
    Finds the shortest path from start to goal using A*.
    Uses the search_algorithms framework from exercise-08.

    Args:
        game_map (Map): The game map.
        start_x, start_y: Starting position.
        goal_x, goal_y: Goal position.
        blocked (Set): Extra blocked positions (e.g. opponent).
    Returns:
        Optional[List[GridMoveAction]]: List of move actions, or None if unreachable.
    """
    if start_x == goal_x and start_y == goal_y:
        return []

    initial_state = GridPosition(start_x, start_y)
    problem = Problem(
        initial_state=initial_state,
        actions_function=GridActionsFunction(game_map, blocked),
        result_function=GridResultFunction(),
        goal_test=GridGoalTest(goal_x, goal_y),
        step_cost_function=GridStepCost(game_map),
        heuristic_function=ManhattanHeuristic(goal_x, goal_y)
    )
    actions, _ = AStar(problem).search()
    return actions


def find_legal_move_positions(game_map: Map, start_x: int, start_y: int,
                              max_move_distance: int,
                              blocked: Set[Tuple[int, int]] = None) -> Set[Tuple[int, int]]:
    """
    Returns positions reachable by moving in a straight cardinal line.

    This matches the game rule where a move may go up, down, left, or right
    for up to max_move_distance tiles, but only if every tile on that line is
    passable and unblocked.
    """
    blocked = blocked or set()
    reachable = set()

    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        spent = 0
        for step in range(1, max_move_distance + 1):
            nx = start_x + dx * step
            ny = start_y + dy * step
            tile = game_map.get_tile(nx, ny)
            if not tile or (nx, ny) in blocked:
                break
            if tile.FieldType == FIELD_OBSTACLE:
                break
            if not tile.is_passable():
                break
            step_cost = 2 if tile.FieldType == FIELD_OBSTACLE_SLOW else 1
            spent += step_cost
            if spent > max_move_distance:
                break
            reachable.add((nx, ny))

    return reachable




from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional, Union

# ─── Field Type Constants ──────────────────────────────────────────────────────
FIELD_BASE         = 0
FIELD_NORMAL       = 1
FIELD_OBSTACLE_SLOW = 2  # Snow: +1 movement cost
FIELD_OBSTACLE     = 3  # Ice Spikes: 10 DMG, impassable
FIELD_POWERUP      = 4
FIELD_WALL         = 5  # impassable
FIELD_EMPTY        = 6  # impassable (shrinking map)

PASSABLE_FIELDS = {FIELD_BASE, FIELD_NORMAL, FIELD_OBSTACLE_SLOW, FIELD_POWERUP}


@dataclass
class Position:
    X: int
    Y: int

    @staticmethod
    def getPosition(positionData):
        if positionData is None:
            return Position(X=0, Y=0)
        return Position(X=positionData.get("X", 0), Y=positionData.get("Y", 0))

    def __eq__(self, other):
        return isinstance(other, Position) and self.X == other.X and self.Y == other.Y

    def __hash__(self):
        return hash((self.X, self.Y))


@dataclass
class Item:
    Id: int
    Name: str
    Uses: int
    Effect: str
    Power: int
    Duration: int
    ItemType: int
    Range: Optional[str] = None

    @staticmethod
    def getItem(data):
        return Item(
            Id=data.get("Id"),
            Name=data.get("Name"),
            Uses=data.get("Uses", 1),
            Effect=data.get("Effect", ""),
            Power=data.get("Power", 0),
            Duration=data.get("Duration", 0),
            ItemType=data.get("ItemType", 0),
            Range=data.get("Range"),
        )


@dataclass
class Obstacle:
    Type: int
    Damage: int
    Cooldown: int
    CurrentCooldown: int

    @staticmethod
    def getObstacle(data):
        return Obstacle(
            Type=data.get("Type", 0),
            Damage=data.get("Damage", 0),
            Cooldown=data.get("Cooldown", 0),
            CurrentCooldown=data.get("CurrentCooldown", 0),
        )


@dataclass
class Monster:
    Id: int
    Name: str
    Health: int
    MaxHealth: int
    AttackPower: int
    AttackRange: int
    MaxMoveDistance: int
    Position: Position
    SummonedByPlayerId: Optional[int] = None
    ActiveStatuses: dict = field(default_factory=dict)
    xPattern: list = field(default_factory=list)
    yPattern: list = field(default_factory=list)

    @staticmethod
    def getMonster(data):
        return Monster(
            Id=data.get("Id"),
            Name=data.get("Name"),
            Health=data.get("Health"),
            MaxHealth=data.get("MaxHealth"),
            AttackPower=data.get("AttackPower"),
            AttackRange=data.get("AttackRange", 1),
            MaxMoveDistance=data.get("MaxMoveDistance", 2),
            Position=Position.getPosition(data.get("Position")),
            SummonedByPlayerId=data.get("SummonedByPlayerId"),
            ActiveStatuses=data.get("ActiveStatuses", {}),
            xPattern=data.get("xPattern", []),
            yPattern=data.get("yPattern", []),
        )


@dataclass
class MonsterCard:
    Id: int
    Name: str
    Uses: int
    Effect: str
    Power: int
    OnCooldown: bool
    Cooldown: int
    CooldownCounter: int
    Monster: Monster

    @staticmethod
    def getCard(data):
        return MonsterCard(
            Id=data.get("Id"),
            Name=data.get("Name"),
            Uses=data.get("Uses", 1),
            Effect=data.get("Effect", ""),
            Power=data.get("Power", 1),
            OnCooldown=data.get("OnCooldown", False),
            Cooldown=data.get("Cooldown", 7),
            CooldownCounter=data.get("CooldownCounter", 0),
            Monster=Monster.getMonster(data.get("Monster", {})),
        )


# Item type IDs (match C# enum)
ITEM_NONE        = 0
ITEM_HEALING     = 1   # Healing Potion: +50 HP
ITEM_MOVEMENT    = 2   # Boots / Teleport stone
ITEM_DEFENSE     = 3   # Invisibility cloak
ITEM_UTILITY     = 4   # Magnetic / Hunter's net
ITEM_CROWD_CTRL  = 5   # Freeze scroll / Confusion scroll
ITEM_ATTACK      = 6   # Sword of destiny


@dataclass
class Player:
    Id: int
    Name: str
    Health: int
    MaxHealth: int
    AttackPower: int
    AttackRange: int
    MaxMoveDistance: int
    Level: int
    Xp: int
    First: bool
    Position: Position
    Inventory: list = field(default_factory=list)
    Cards: list = field(default_factory=list)
    SummonedByPlayerId: Optional[int] = None
    ActiveStatuses: dict = field(default_factory=dict)
    xPattern: list = field(default_factory=list)
    yPattern: list = field(default_factory=list)

    @staticmethod
    def getPlayer(p):
        return Player(
            Id=p.get("Id"),
            Name=p.get("Name"),
            Health=p.get("Health"),
            MaxHealth=p.get("MaxHealth"),
            AttackPower=p.get("AttackPower"),
            AttackRange=p.get("AttackRange", 1),
            MaxMoveDistance=p.get("MaxMoveDistance", 4),
            Level=p.get("Level", 1),
            Xp=p.get("Xp", 0),
            First=p.get("First", False),
            Position=Position.getPosition(p.get("Position")),
            Inventory=[Item.getItem(i) for i in p.get("Inventory", [])],
            Cards=[MonsterCard.getCard(c) for c in p.get("Cards", [])],
            SummonedByPlayerId=p.get("SummonedByPlayerId"),
            ActiveStatuses=p.get("ActiveStatuses", {}),
            xPattern=p.get("xPattern", []),
            yPattern=p.get("yPattern", []),
        )

    def getPosition(self):
        return self.Position

    def is_alive(self):
        return self.Health > 0

    def has_status(self, status_name: str) -> bool:
        return status_name in self.ActiveStatuses


@dataclass
class Tile:
    Position: Position
    FieldType: int
    Owner: Optional[str] = None
    Entity: Optional[Union[Player, Monster]] = None
    Item: Optional[Item] = None
    MonsterCard: Optional[MonsterCard] = None
    Obstacle: Optional[Obstacle] = None

    def is_passable(self) -> bool:
        return self.FieldType in PASSABLE_FIELDS

    def move_cost(self) -> int:
        """Returns the movement cost to enter this tile."""
        return 2 if self.FieldType == FIELD_OBSTACLE_SLOW else 1

    @staticmethod
    def getGrid(gridData):
        return [Tile.getTile(tile) for tile in gridData]

    @staticmethod
    def getTile(gridData):
        entity = None
        if gridData.get("Entity") is not None:
            e = gridData.get("Entity")
            if "Level" in e:
                entity = Player.getPlayer(e)
            elif e.get("Position") is not None:
                entity = Monster.getMonster(e)
        return Tile(
            Position=Position.getPosition(gridData.get("Position")),
            FieldType=gridData.get("FieldType", FIELD_NORMAL),
            Owner=gridData.get("Owner"),
            Entity=entity,
            Item=Item.getItem(gridData.get("Item")) if gridData.get("Item") else None,
            MonsterCard=MonsterCard.getCard(gridData.get("MonsterCard")) if gridData.get("MonsterCard") else None,
            Obstacle=Obstacle.getObstacle(gridData.get("Obstacle")) if gridData.get("Obstacle") else None,
        )


@dataclass
class Map:
    X: int   # width (0..X-1)
    Y: int   # height (0..Y-1)
    Name: str
    Grid: list = field(default_factory=list)  # List[Tile]

    @staticmethod
    def getMap(mapData):
        return Map(
            X=mapData.get("X", 32),
            Y=mapData.get("Y", 16),
            Name=mapData.get("Name", ""),
            Grid=Tile.getGrid(mapData.get("Grid", []))
        )

    def get_tile(self, x: int, y: int) -> Optional[Tile]:
        """Returns the tile at (x, y), or None if out of bounds."""
        if not (0 <= x < self.X and 0 <= y < self.Y):
            return None
        idx = x * self.Y + y
        if idx < len(self.Grid):
            return self.Grid[idx]
        return None

    def get_passable_neighbors(self, x: int, y: int) -> list:
        """Returns list of (tile, x, y) for passable adjacent tiles."""
        result = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            tile = self.get_tile(nx, ny)
            if tile and tile.is_passable():
                result.append((tile, nx, ny))
        return result


@dataclass
class GameBoardState:
    GameState: str
    GameId: str
    TurnCounter: int
    Players: list = field(default_factory=list)  # List[Player]
    Map: Optional[Map] = None

    @staticmethod
    def getState(data: dict) -> GameBoardState:
        return GameBoardState(
            GameState=data.get("GameState", ""),
            GameId=data.get("GameId", ""),
            TurnCounter=data.get("TurnCounter", 0),
            Players=[Player.getPlayer(p) for p in data.get("Players", {}).values()],
            Map=Map.getMap(data.get("Map")) if data.get("Map") else None
        )

    def clone(self) -> GameBoardState:
        """Deep copy the board state for minimax simulation."""
        return copy.deepcopy(self)

    def getPlayerById(self, player_id: int) -> Optional[Player]:
        for p in self.Players:
            if p.Id == player_id:
                return p
        return None

    def getOpponentOf(self, player_id: int) -> Optional[Player]:
        for p in self.Players:
            if p.Id != player_id:
                return p
        return None

    def get_all_monsters(self) -> list:
        """Returns all Monster entities currently on the map."""
        monsters = []
        if self.Map:
            for tile in self.Map.Grid:
                if tile.Entity and isinstance(tile.Entity, Monster):
                    monsters.append(tile.Entity)
        return monsters

    def get_cards_on_map(self) -> list:
        """Returns list of (MonsterCard, x, y) for all cards on the map."""
        cards = []
        if self.Map:
            for tile in self.Map.Grid:
                if tile.MonsterCard:
                    cards.append((tile.MonsterCard, tile.Position.X, tile.Position.Y))
        return cards

    def get_items_on_map(self) -> list:
        """Returns list of (Item, x, y) for all items/powerups on the map."""
        items = []
        if self.Map:
            for tile in self.Map.Grid:
                if tile.Item:
                    items.append((tile.Item, tile.Position.X, tile.Position.Y))
        return items

    def isMyTurn(self, player_id: int) -> bool:
        my_player = self.getPlayerById(player_id)
        if not my_player:
            return False
        is_first = my_player.First
        return (is_first and self.GameState == 'Player1Turn') or \
               (not is_first and self.GameState == 'Player2Turn')

    def isGameOver(self) -> bool:
        return self.GameState == "Ending"

    def __str__(self) -> str:
        player_strs = [f"P{p.Id}({p.Health}HP,Lv{p.Level})" for p in self.Players]
        return (f"Turn={self.TurnCounter} State={self.GameState} "
                f"Players=[{', '.join(player_strs)}]")

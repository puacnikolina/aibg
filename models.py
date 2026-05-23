from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass
class Position:
    X: int
    Y: int

    @staticmethod
    def getPosition(positionData):
        if positionData is None:
            return Position(X=0, Y=0)
        return Position(
            X=positionData.get("X"),
            Y=positionData.get("Y"),
        )


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
            Uses=data.get("Uses"),
            Effect=data.get("Effect"),
            Power=data.get("Power"),
            Duration=data.get("Duration"),
            ItemType=data.get("ItemType"),
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
            Type=data.get("Type"),
            Damage=data.get("Damage"),
            Cooldown=data.get("Cooldown"),
            CurrentCooldown=data.get("CurrentCooldown"),
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
    xPattern: list[int] = field(default_factory=list)
    yPattern: list[int] = field(default_factory=list)

    @staticmethod
    def getMonster(data):
        return Monster(
            Id=data.get("Id"),
            Name=data.get("Name"),
            Health=data.get("Health"),
            MaxHealth=data.get("MaxHealth"),
            AttackPower=data.get("AttackPower"),
            AttackRange=data.get("AttackRange"),
            MaxMoveDistance=data.get("MaxMoveDistance"),
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
            Uses=data.get("Uses"),
            Effect=data.get("Effect"),
            Power=data.get("Power"),
            OnCooldown=data.get("OnCooldown"),
            Cooldown=data.get("Cooldown"),
            CooldownCounter=data.get("CooldownCounter"),
            Monster=Monster.getMonster(data.get("Monster")),
        )



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
    Inventory: list[Item] = field(default_factory=list)
    Cards: list[MonsterCard] = field(default_factory=list)
    SummonedByPlayerId: Optional[int] = None
    ActiveStatuses: dict = field(default_factory=dict)
    xPattern: list[int] = field(default_factory=list)
    yPattern: list[int] = field(default_factory=list)

    @staticmethod
    def getPlayer(p):
        return Player(
            Id=p.get("Id"),
            Name=p.get("Name"),
            Health=p.get("Health"),
            MaxHealth=p.get("MaxHealth"),
            AttackPower=p.get("AttackPower"),
            AttackRange=p.get("AttackRange"),
            MaxMoveDistance=p.get("MaxMoveDistance"),
            Level=p.get("Level"),
            Xp=p.get("Xp"),
            First=p.get("First"),
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


@dataclass
class Tile:
    Position: Position
    FieldType: int
    Owner: Optional[str] = None
    Entity: Optional[Union[Player, Monster]] = None
    Item: Optional[Item] = None
    MonsterCard: Optional[MonsterCard] = None
    Obstacle: Optional[Obstacle] = None

    @staticmethod
    def getGrid(gridData):
        return [Tile.getTile(tile) for tile in gridData]

    @staticmethod
    def getTile(gridData):
        entity = None
        if gridData.get("Entity") is not None:
            e = gridData.get("Entity")
            # Players have a Level field; monsters do not
            if "Level" in e:
                entity = Player.getPlayer(e)
            elif "Position" in e:
                entity = Monster.getMonster(e)
            else:
                entity = None

        return Tile(
            Position=Position.getPosition(gridData.get("Position")),
            FieldType=gridData.get("FieldType"),
            Owner=gridData.get("Owner"),
            Entity=entity,
            Item=Item.getItem(gridData.get("Item")) if gridData.get("Item") else None,
            MonsterCard=MonsterCard.getCard(gridData.get("MonsterCard")) if gridData.get("MonsterCard") else None,
            Obstacle=Obstacle.getObstacle(gridData.get("Obstacle")) if gridData.get("Obstacle") else None,
        )



@dataclass
class Map:
    X: int
    Y: int
    Name: str
    Grid: list[Tile] = field(default_factory=list)

    @staticmethod
    def getMap(mapData):
        return Map(
            X=mapData.get("X"),
            Y=mapData.get("Y"),
            Name=mapData.get("Name"),
            Grid=Tile.getGrid(mapData.get("Grid",[]))
        )

   
@dataclass
class GameBoardState:
    GameState: str
    GameId: str
    TurnCounter: int
    Players: list[Player] = field(default_factory=list)
    Map: Optional[Map] = None

    @staticmethod
    def getState(data: dict) -> GameBoardState:
        return GameBoardState(
            GameState=data.get("GameState"),
            GameId=data.get("GameId"),
            TurnCounter=data.get("TurnCounter"),
            Players=[
            Player.getPlayer(p)
            for p in data.get("Players", {}).values()
            ],
            Map= Map.getMap(data.get("Map"))
        )

    def get_neighboring_tiles(self, position: Position) -> list[Tile]:
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        for dx, dy in directions:
            new_x = position.X + dx
            new_y = position.Y + dy
            if 0 <= new_x < self.Map.X and 0 <= new_y < self.Map.Y:
                tile = self.get_tile_at_position(Position(X=new_x, Y=new_y))
                if tile:
                    neighbors.append(tile)
        return neighbors

    def getPlayerById(self, player_id):
        if not self or not player_id:
            return None
        players = self.Players
        for p in players:
            if p.Id == player_id:
                return p
        return None
    
    def isMyTurn(state, player_id):
        if not state or not player_id:
            return False
        players = state.Players
        my_player = next((p for p in players if p.Id == player_id), None)
        if not my_player:
            return False
        is_first = my_player.First
        game_state_str = state.GameState
        return (is_first and game_state_str == 'Player1Turn') or (not is_first and game_state_str == 'Player2Turn')

    def isGameOver(state):
        if not state.GameState:
            return False
        return state.GameState == "Ending"

    def __str__(self) -> str:
        return f"GameState(GameState={self.GameState}, GameId={self.GameId}, TurnCounter={self.TurnCounter}, Players=[{', '.join(str(p) for p in self.Players)}], Map={self.Map})"
    
    def __clone__(self):
        return GameBoardState(
            GameState=self.GameState,
            GameId=self.GameId,
            TurnCounter=self.TurnCounter,
            Players=[Player.getPlayer(p.__dict__) for p in self.Players],
            Map=Map.getMap(self.Map.__dict__) if self.Map else None
        )
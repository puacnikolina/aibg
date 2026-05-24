# Monster Hunt Bot - Dokumentacija

## Preuzimanje sa Git Repozitorijuma

Klonirate verziju sa GitHub repozitorijuma:

```bash
git clone https://github.com/ParadoxBosmer/TEST-BOT.git
```
Unutra postoje modeli koji vam mogu poslužiti za rad kao i kosturi za dozvoljene programske jezike. 


## Objašnjenje toka poteza

Svaki igrač ima `First` property (boolean):
- **Igrač 1** (`First=true`): Igra kada je `GameState="Player1Turn"`
- **Igrač 2** (`First=false`): Igra kada je `GameState="Player2Turn"`

Ciklus poteza: **Player1Turn → Player2Turn → MonsterTurn → Player1Turn**


## HTTP Pozivi

**VAŽNO**: Svaki od sledećih PUT endpoints **automatski vraća kompletno stanje igre** u response-u, tako da nije potrebno eksplicitno pozivati GET /game/state.

### 1. PUT /player/move/gameId/{gameId}

Pomera igrača na novu poziciju.

**URL**: `PUT http://localhost:8080/player/move/gameId/{gameId}`

**Request Body**:
```json
{
  "playerId": 1,
  "newPosition": { "X": 5, "Y": 7 }
}
```
---

### 2. PUT /player/{attackerId}/attack/{attackedId}/gameId/{gameId}

Napadni drugog igrača ili monstruma.

**URL**: `PUT http://localhost:8080/player/{attackerId}/attack/{attackedId}/gameId/{gameId}`

**Request Body**: Nije potreban (ID-ovi su u URL-u)

**Response** (200 OK):
```json
{
  "success": true,
  "damage": 25
}
```

---

### 3. PUT /player/{playerId}/use-item/{itemId}/gameId/{gameId}

Koristi item iz inventara.

**URL**: `PUT http://localhost:8080/player/{playerId}/use-item/{itemId}/gameId/{gameId}`

**Response** (200 OK):
```json
{
  "success": true
}
```

---

### 4. PUT /player/pickup/{playerId}/gameId/{gameId}

Pokupite karticu sa mape.

**URL**: `PUT http://localhost:8080/player/pickup/{playerId}/gameId/{gameId}`

**Request Body**:
```json
{
  "Position": { "X": 5, "Y": 7 }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "card": { "Id": 123, "Name": "FireMonster" }
}
```

---

### 5. PUT /map/{playerId}/summon/{cardId}/gameId/{gameId}

Prizovite monstruma iz kartice.

**URL**: `PUT http://localhost:8080/map/{playerId}/summon/{cardId}/gameId/{gameId}`

**Request Body**:
```json
{
  "X": 6,
  "Y": 8
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "monsterId": 456
}
```

# FieldInfo Dokumentacija

## Struktura FieldInfo

```csharp
public class FieldInfo
{
    public Position? Position;
    [JsonProperty(TypeNameHandling = TypeNameHandling.Auto)]
    public Entity? Entity;
    public Field FieldType;
    public Player? Owner;
    public Item? Item;
    public MonsterCard? MonsterCard;
    public Obstacle? Obstacle;
}
```

### Svojstva:
- **Position**: Koordinate polja (X, Y)
- **Entity**: Bilo koji entitet na tom polju (igrač/čudovište)
- **FieldType**: Tip polja (NORMAL, itd.)
- **Owner**: Igrač koji poseduje polje
- **Item**: Predmet prisutan na polju
- **MonsterCard**: Karta čudovišta na polju
- **Obstacle**: Bilo koja prepreka

## Kako se poziva

### 1. MapController - PickUpCard
```csharp
[HttpPut("pickup/{playerId}/gameId/{gameId}")]
public async Task<IActionResult> PickUpCard(
    [FromRoute] int playerId, 
    [FromRoute] string gameId,
    [FromBody] FieldInfo fieldInfo, 
    CancellationToken cancellationToken)
{
    _playerServices.PickupCard(gameId, playerId, fieldInfo);
}
```

### 2. PlayerController - PickUpItem
```csharp
[HttpPut("pickup/{playerId}/gameId/{gameId}")]
public async Task<IActionResult> PickUpItem(
    [FromRoute] string gameId,
    [FromBody] FieldInfo fieldInfo, 
    [FromRoute] int playerId, 
    CancellationToken cancellationToken)
{
    _playerServices.PickupItem(gameId, player.Id, fieldInfo);
}
```

## Primer strukture povratka

Kada se vraća kao JSON, FieldInfo izgleda ovako:

```json
{
  "Position": {
    "X": 5,
    "Y": 3
  },
  "Entity": null,
  "FieldType": "NORMAL",
  "Owner": null,
  "Item": {
    "ItemType": "HEALTH_POTION",
    "Value": 50
  },
  "MonsterCard": null,
  "Obstacle": null
}
```

Ili sa entitetom:

```json
{
  "Position": {
    "X": 2,
    "Y": 7
  },
  "Entity": {
    "$type": "Player",
    "Id": 1,
    "Name": "PlayerOne",
    "Health": 100
  },
  "FieldType": "NORMAL",
  "Owner": {
    "Id": 1,
    "Name": "PlayerOne"
  },
  "Item": null,
  "MonsterCard": null,
  "Obstacle": null
}
```

---

## Sadržajmape

**Svaki PUT endpoint automatski vraća kompletno stanje igre** koje sadrži:

### Map.Grid
Lista svih polja na mapi sa informacijama o preprekama:


**FieldType vrednosti**:
- `0` = **BASE** (baza)
- `1` = **NORMAL** (obično polje, može se hodati)
- `2` = **OBSTACLE_SLOW** (usporava kretanje)
- `3` = **OBSTACLE** (prepreka)
- `4` = **POWERUP** (power-up)
- `5` = **WALL** (zid)
- `6` = **EMPTY** (prazno)


**Mapa je 32×16** (X: 0-31, Y: 0-15)

---

## Šta Morate Instalirati i Pokrenuti

### Python
```bash
pip install requests
python bot_template.py http://localhost:8080 game123 MojBot
```

### JavaScript
```bash

npm install axios
node bot_template.js http://localhost:8080 game123 MojBot
```

### C#
```bash
dotnet run http://localhost:8080 game123 MojBot
```

### Java
```bash
mvn clean package
java -jar target/bot-template-1.0-SNAPSHOT.jar http://localhost:8080 game123 MojBot
```

### Go
```bash
go run bot_template.go http://localhost:8080 game123 MojBot
```

### C++
```bash
mkdir build && cd build
cmake ..
make
./bot_template http://localhost:8080 game123 MojBot
```

## **VAŽNO - Pravila za Predaju Fajlova**

**Prilikom predaje fajlova, obavezno dodajte sufiks sa imenom programskog jezika:**
- Format: `naziv_fajla_{programski_jezik}.ekstenzija`
- Primeri:
  - `bot_template_python.py`
  - `bot_template_java.jar`
  - `bot_template_csharp.exe`
  - `bot_template_cplusplus.exe`
  - `bot_template_javascript.js`
  - `bot_template_cpp.exe`
  - `bot_template_go.exe`

---
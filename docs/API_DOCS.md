# Warframe Damage Calculator API Documentation

## Getting Started

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Start the Flask development server
python app.py
```

The server will start at `http://localhost:5000`

### Testing the API

```bash
# Run API tests
python test_api.py
```

---

## API Endpoints

### 1. Get Available Mods

**Endpoint:** `GET /api/mods`

**Description:** Returns a list of all available mods with their stats.

**Response:**
```json
{
  "success": true,
  "mods": [
    {
      "id": "hornet_strike",
      "name": "hornet_strike",
      "max_level": 10,
      "stats": {
        "damage": 2.2
      }
    },
    {
      "id": "primed_pistol_gambit",
      "name": "primed_pistol_gambit",
      "max_level": 10,
      "stats": {
        "critical_chance": 1.87
      }
    }
  ],
  "count": 60
}
```

**Example:**
```bash
curl http://localhost:5000/api/mods
```

---

### 2. Search Mods

**Endpoint:** `GET /api/search-mods?q={query}`

**Description:** Search for mods by name.

**Query Parameters:**
- `q` (string, required): Search query (minimum 2 characters)

**Response:**
```json
{
  "success": true,
  "mods": [
    {
      "id": "hornet_strike",
      "name": "hornet_strike",
      "max_level": 10
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:5000/api/search-mods?q=hornet"
```

---

### 3. Get Enemy Types

**Endpoint:** `GET /api/enemy-types`

**Description:** Returns all available enemy faction types from the EnemyType enum.

**Response:**
```json
{
  "success": true,
  "enemy_types": [
    "none",
    "grineer",
    "corpus",
    "tridolon"
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/enemy-types
```

---

### 4. Get In-Game Buffs

**Endpoint:** `GET /api/ingame-buffs`

**Description:** Returns all available in-game buff fields from the InGameBuff dataclass.

**Response:**
```json
{
  "success": true,
  "buffs": [
    {
      "name": "galvanized_shot",
      "type": "int",
      "default": 0
    },
    {
      "name": "galvanized_aptitude",
      "type": "int",
      "default": 0
    },
    {
      "name": "final_additive_cd",
      "type": "float",
      "default": 0
    },
    {
      "name": "attack_speed",
      "type": "float",
      "default": 0.0
    },
    {
      "name": "num_debuffs",
      "type": "int",
      "default": 0
    },
    {
      "name": "final_multiplier",
      "type": "float",
      "default": 1.0
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/ingame-buffs
```

---

### 5. Calculate Damage (Main Endpoint)

**Endpoint:** `POST /api/calculate-damage`

**Description:** Calculate damage based on weapon stats, mods, enemy type, and in-game buffs.

**Request Body:**
```json
{
  "weapon": {
    "damage": 1,
    "attack_speed": 1,
    "multishot": 1,
    "critical_chance": 0.31,
    "critical_damage": 4.2,
    "status_chance": 0.43,
    "status_duration": 1,
    "elements": {
      "impact": 1,
      "puncture": 0,
      "slash": 0,
      "cold": 0,
      "electricity": 0,
      "heat": 0,
      "toxin": 0
    }
  },
  "mods": [
    "hornet_strike",
    "primed_pistol_gambit",
    "barrel_diffusion",
    "lethal_torrent"
  ],
  "enemy": {
    "faction": "tridolon"
  },
  "in_game_buffs": {
    "galvanized_shot": 0,
    "galvanized_aptitude": 0,
    "final_additive_cd": 1.2,
    "attack_speed": 0.6,
    "num_debuffs": 0,
    "final_multiplier": 1.0,
    "elements": {
      "radiation": 3.3,
      "toxin": 1.0
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "damage": {
    "single_hit": 3656.28,
    "direct_dps": 10018.20,
    "fire_dot_dps": 0.0,
    "total_dps": 10018.20
  },
  "stats": {
    "base_damage": 3.2,
    "critical_multiplier": 13.84,
    "multishot": 3.3,
    "attack_speed": 2.1,
    "status_chance": 1.204,
    "elemental_total": 5.3
  },
  "buffs_applied": {
    "static": {
      "damage": 2.2,
      "critical_chance": 1.87,
      "critical_damage": 1.1,
      "multishot": 1.8,
      "attack_speed": 0.6,
      "status_chance": 0.0,
      "elements": {},
      "prejudice": {}
    },
    "in_game": {
      "galvanized_shot": 0,
      "galvanized_aptitude": 0,
      "final_additive_cd": 1.2,
      "attack_speed": 0.6,
      "num_debuffs": 0,
      "final_multiplier": 1.0,
      "elements": {
        "radiation": 3.3,
        "toxin": 1.0
      }
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/calculate-damage \
  -H "Content-Type: application/json" \
  -d '{
    "weapon": {
      "damage": 1,
      "attack_speed": 1,
      "multishot": 1,
      "critical_chance": 0.31,
      "critical_damage": 4.2,
      "status_chance": 0.43,
      "elements": {"impact": 1}
    },
    "mods": ["hornet_strike", "barrel_diffusion"],
    "enemy": {"faction": "grineer"},
    "in_game_buffs": {"num_debuffs": 0}
  }'
```

---

### 6. Health Check

**Endpoint:** `GET /api/health`

**Description:** Health check endpoint to verify the API is running.

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "message": "Warframe Damage Calculator API is running"
}
```

**Example:**
```bash
curl http://localhost:5000/api/health
```

---

## Data Types

### Weapon Stats

| Field | Type | Description |
|-------|------|-------------|
| damage | float | Base damage multiplier (default: 1) |
| attack_speed | float | Fire rate/attack speed (default: 1) |
| multishot | float | Number of projectiles per shot (default: 1) |
| critical_chance | float | Critical hit chance (0.0 to 1.0+) |
| critical_damage | float | Critical damage multiplier (default: 1) |
| status_chance | float | Status proc chance (0.0 to 1.0+) |
| status_duration | float | Status effect duration multiplier (default: 1) |
| elements | object | Elemental damage breakdown |

### Elements Object

| Field | Type | Description |
|-------|------|-------------|
| impact | float | Impact (physical) damage |
| puncture | float | Puncture (physical) damage |
| slash | float | Slash (physical) damage |
| cold | float | Cold elemental damage |
| electricity | float | Electricity elemental damage |
| heat | float | Heat elemental damage |
| toxin | float | Toxin elemental damage |
| blast | float | Blast combined damage |
| corrosive | float | Corrosive combined damage |
| gas | float | Gas combined damage |
| magnetic | float | Magnetic combined damage |
| radiation | float | Radiation combined damage |
| viral | float | Viral combined damage |
| void | float | Void damage |
| tau | float | Tau damage |

### Enemy Factions

- `none` - No specific faction
- `grineer` - Grineer faction
- `corpus` - Corpus faction
- `tridolon` - Eidolon (special bonuses for radiation/cold)

### In-Game Buffs

| Field | Type | Description |
|-------|------|-------------|
| galvanized_shot | int | Number of Galvanized Shot stacks (0-3) |
| galvanized_aptitude | int | Number of Galvanized Aptitude stacks |
| final_additive_cd | float | Additional critical damage (e.g., from pets) |
| attack_speed | float | Additional attack speed bonus (e.g., from pets) |
| num_debuffs | int | Number of debuffs on enemy |
| final_multiplier | float | Final damage multiplier (default: 1.0) |
| elements | object | Additional elemental damage from buffs |

---

## Error Responses

All endpoints return error responses in this format:

```json
{
  "success": false,
  "error": "Error message description",
  "traceback": "Detailed error trace (only in debug mode)"
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `500` - Internal Server Error

---

## Frontend Integration

The HTML page at `/` (served from `client/wf_dmg_calc.html`) uses these endpoints.

Example JavaScript fetch:

```javascript
// Search for mods
fetch('/api/search-mods?q=hornet')
  .then(response => response.json())
  .then(data => {
    console.log(data.mods);
  });

// Calculate damage
fetch('/api/calculate-damage', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    weapon: { /* weapon stats */ },
    mods: ['hornet_strike'],
    enemy: { faction: 'grineer' },
    in_game_buffs: { num_debuffs: 0 }
  })
})
  .then(response => response.json())
  .then(data => {
    console.log(data.damage.total_dps);
  });
```

---

## Notes

- All damage calculations are based on the game mechanics implemented in `src/damage_calculator.py`
- Mod data is loaded from `data/mod_data.txt`
- Special mod effects (callbacks) are not yet implemented
- The API uses CORS to allow cross-origin requests

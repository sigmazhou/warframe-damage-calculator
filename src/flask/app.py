from flask import Flask, jsonify, request
from flask_cors import CORS
from dataclasses import fields, MISSING
import logging
from collections import OrderedDict
from src.calculator.mod_parser import ModParser
from src.calculator.damage_calculator import DamageCalculator
from src.calculator.wf_dataclasses import (
    WeaponStat,
    StaticBuff,
    InGameBuff,
    EnemyStat,
    EnemyFaction,
    EnemyType,
    Elements,
    DotState,
)
from src.data.enemy_data import get_enemy_stat

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


app = Flask(__name__, static_folder="../client", static_url_path="")
CORS(app)  # Enable CORS for all routes

# Initialize parser
parser = ModParser()


# Helper functions for flattening/unflattening buff fields
def flatten_buff_fields(buff_fields):
    """
    Flatten InGameBuff fields by expanding faction and elements into individual fields.

    Args:
        buff_fields: List of field dictionaries from InGameBuff dataclass

    Returns:
        List of flattened field dictionaries
    """
    flattened = []

    for field in buff_fields:
        if field["name"] == "faction":
            # Get faction names from EnemyFaction enum (exclude NONE)
            factions = [
                faction.value
                for faction in EnemyFaction
                if faction != EnemyFaction.NONE
            ]
            for faction in factions:
                flattened.append(
                    {"name": f"faction_{faction}", "type": "float", "default": 0.0}
                )
        elif field["name"] == "elements":
            # Get element names from Elements dataclass
            # Format: {element}_damage (e.g., heat_damage, cold_damage)
            # For standalone elements: {element}_damage_standalone (e.g., heat_damage_standalone)
            element_names = [f.name for f in fields(Elements)]
            for element in element_names:
                if element.endswith("_standalone"):
                    # Convert heat_standalone -> heat_damage_standalone
                    base_element = element.replace("_standalone", "")
                    display_name = f"{base_element}_damage_standalone"
                else:
                    display_name = f"{element}_damage"
                flattened.append(
                    {"name": display_name, "type": "float", "default": 0.0}
                )
        elif field["name"] != "callbacks":
            # Keep regular fields (exclude callbacks)
            flattened.append(field)

    return flattened


@app.route("/")
def index():
    """Serve the main HTML page."""
    return app.send_static_file("wf_dmg_calc.html")


@app.route("/api/mods", methods=["GET"])
def get_available_mods():
    """
    Get list of all available mods.

    Returns:
        JSON array of mod objects with name and details
    """
    try:
        mod_names = parser.get_available_mods()
        mods_list = []

        for mod_name in mod_names:
            mod_info = parser.get_mod_info(mod_name)
            mods_list.append(
                {
                    "id": mod_name,
                    "name": mod_name,
                    "max_level": mod_info.get("max_level", 0),
                    "stats": {
                        k: v
                        for k, v in mod_info.items()
                        if k not in ["max_level", "special_notes"]
                    },
                }
            )

        return jsonify({"success": True, "mods": mods_list, "count": len(mods_list)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_search_match_priority(name: str, query: str) -> int:
    """
    Get match priority for search (lower = better match).

    Args:
        name: The internal mod name (e.g., "hornet_strike")
        query: The search query (may contain spaces or underscores)

    Returns:
        Match priority: 0 = prefix match, 1 = contains match, -1 = no match
    """
    normalized_name = name.lower()
    normalized_query = query.lower()
    query_with_underscores = normalized_query.replace(" ", "_")
    name_with_spaces = normalized_name.replace("_", " ")

    # Check prefix match (highest priority)
    if normalized_name.startswith(query_with_underscores) or name_with_spaces.startswith(normalized_query):
        return 0

    # Check contains match (lower priority)
    if query_with_underscores in normalized_name or normalized_query in name_with_spaces:
        return 1

    return -1  # No match


@app.route("/api/search-mods", methods=["GET"])
def search_mods():
    """
    Search for mods by name. Supports both spaces and underscores in query.

    Query params:
        q: Search query string (e.g., "hornet strike" or "hornet_strike")

    Returns:
        JSON array of matching mods
    """
    try:
        query = request.args.get("q", "").lower()

        if len(query) < 2:
            return jsonify({"success": True, "mods": []})

        mod_names = parser.get_available_mods()
        matching_mods = []

        for mod_name in mod_names:
            priority = get_search_match_priority(mod_name, query)
            if priority >= 0:
                mod_info = parser.get_mod_info(mod_name)
                matching_mods.append(
                    {
                        "id": mod_name,
                        "name": mod_name,
                        "max_level": mod_info.get("max_level", 0),
                        "_priority": priority,  # For sorting
                    }
                )

        # Sort by priority (prefix matches first)
        matching_mods.sort(key=lambda x: x["_priority"])
        # Remove priority from response
        for mod in matching_mods:
            del mod["_priority"]

        return jsonify({"success": True, "mods": matching_mods})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/enemy-factions", methods=["GET"])
def get_enemy_factions():
    """
    Get list of available enemy factions from EnemyFaction enum.

    Returns:
        JSON array of enemy faction strings
    """
    try:
        enemy_factions = [enemy_faction.value for enemy_faction in EnemyFaction]

        return jsonify({"success": True, "enemy_factions": enemy_factions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/enemy-types", methods=["GET"])
def get_enemy_types():
    """
    Get list of available enemy types from EnemyType enum.

    Returns:
        JSON array of enemy type strings
    """
    try:
        enemy_types = [enemy_type.value for enemy_type in EnemyType]

        return jsonify({"success": True, "enemy_types": enemy_types})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/riven-stats", methods=["GET"])
def get_riven_stats():
    """
    Get riven base stats by weapon type.

    Returns:
        JSON object with weapon types as keys and their riven stats as values
    """
    try:
        import orjson
        import os

        # Load riven stats from file
        riven_stats_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "riven_stats.txt"
        )
        with open(riven_stats_path, "rb") as f:
            riven_stats = orjson.loads(f.read())

        return jsonify({"success": True, "riven_stats": riven_stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/ingame-buffs", methods=["GET"])
def get_ingame_buffs():
    """
    Get list of available in-game buff fields from InGameBuff dataclass.
    Returns flattened fields with faction_* and {element}_damage expanded.

    Returns:
        JSON object with buff field names and their types
    """
    try:
        buff_fields = []

        for field in fields(InGameBuff):
            # Get default value, handling MISSING and default_factory
            default_value = None
            if field.default is not MISSING:
                default_value = field.default
            elif field.default_factory is not MISSING:
                # For factory defaults, we can't easily serialize, so skip
                default_value = None

            buff_fields.append(
                {
                    "name": field.name,
                    "type": field.type.__name__
                    if hasattr(field.type, "__name__")
                    else str(field.type),
                    "default": default_value,
                }
            )

        # Flatten the fields (expand faction and elements)
        flattened_fields = flatten_buff_fields(buff_fields)

        return jsonify({"success": True, "buffs": flattened_fields})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/calculate-damage", methods=["POST"])
def calculate_damage():
    """
    Calculate damage based on weapon stats, mods, rivens, enemy type, and buffs.

    Request body:
        {
            "weapon": {
                "damage": float,
                "attack_speed": float,
                "multishot": float,
                "critical_chance": float,
                "critical_damage": float,
                "status_chance": float,
                "elements": {
                    "impact": float,
                    "puncture": float,
                    "slash": float,
                    ...
                }
            },
            "mods": ["mod_name1", "riven_1", "mod_name2", ...],
            "rivens": {
                "riven_1": {
                    "damage": 2.15,
                    "critical_chance": 1.38,
                    "heat_damage": 1.20
                }
            },
            "enemy": {
                "faction": str,  # EnemyFaction value (grineer, corpus, etc)
                "type": str      # EnemyType value (tridolon, etc)
            },
            "in_game_buffs": {
                "galvanized_shot": int,
                "galvanized_aptitude": int,
                "final_additive_cd": float,
                "attack_speed": float,
                "num_debuffs": int,
                "final_multiplier": float,
                "elements": {...}
            },
            "element_order": ["heat", "toxin"],
            "simulation": {
                "duration": 10.0,
                "num_simulations": 10
            }
        }

    Returns:
        JSON object with calculated damage values
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Log raw incoming request data
        logger.info("=== Calculate Damage Request ===")
        logger.info(f"Raw request data: {data}")

        # Parse weapon stats
        weapon_data = data.get("weapon", {})

        # Extract element order from weapon_data before creating WeaponStat
        # Dictionary maintains insertion order in Python 3.7+, preserving user's selection order
        # Skip elements with 0 value
        weapon_elements_dict = weapon_data.get("elements", {})
        element_order_from_weapon = [
            k for k, v in weapon_elements_dict.items() if v > 0
        ]

        weapon = WeaponStat(
            damage=weapon_data.get("damage", 1),
            attack_speed=weapon_data.get("attack_speed", 1),
            multishot=weapon_data.get("multishot", 1),
            critical_chance=weapon_data.get("critical_chance", 0),
            critical_damage=weapon_data.get("critical_damage", 1),
            status_chance=weapon_data.get("status_chance", 0),
            status_duration=weapon_data.get("status_duration", 1),
            elements=Elements(**weapon_elements_dict),
        )

        logger.info(
            f"Parsed weapon stats: damage={weapon.damage}, attack_speed={weapon.attack_speed}, "
            f"multishot={weapon.multishot}, crit_chance={weapon.critical_chance}, "
            f"crit_damage={weapon.critical_damage}, status_chance={weapon.status_chance}"
        )
        logger.info(f"Weapon elements: {weapon.elements.to_dict()}")

        # Parse mods (filter out None/null/empty values)
        mod_list = [mod for mod in data.get("mods", []) if mod]
        logger.info(f"Mods applied: {mod_list}")

        # Parse rivens
        rivens_data = data.get("rivens", {})
        logger.info(f"Rivens data: {rivens_data}")

        # Parse in-game buffs
        in_game_buffs_data = data.get("in_game_buffs", {})
        logger.info(f"In-game buffs: {in_game_buffs_data}")

        # Parse mods, rivens, and buffs - handles all formats (flat keys and nested dicts)
        in_game_buff, element_order_from_mods, element_order_from_igb = (
            parser.parse_mods_and_stats(mod_list, in_game_buffs_data, rivens_data)
        )
        logger.info(
            f"InGameBuff - damage: {in_game_buff.damage}, multishot: {in_game_buff.multishot}, "
            f"crit_chance: {in_game_buff.critical_chance}, crit_damage: {in_game_buff.critical_damage}"
        )
        logger.info(f"Element order from mods: {element_order_from_mods}")
        logger.info(f"Element order from weapon: {element_order_from_weapon}")
        logger.info(f"Element order from IGB: {element_order_from_igb}")

        # Combine element orders: mods -> weapon -> in-game buffs
        element_order = (
            element_order_from_mods + element_order_from_weapon + element_order_from_igb
        )
        logger.info(f"Final element order: {element_order}")

        # Parse enemy
        enemy_data = data.get("enemy", {})
        enemy = get_enemy_stat(
            enemy_data.get("faction", EnemyFaction.NONE),
            enemy_data.get("type", EnemyType.NONE),
        )
        enemy.dot_state = DotState()

        logger.info(f"Enemy faction: {enemy.faction.value}, type: {enemy.type.value}")

        # Create calculator with element order
        calculator = DamageCalculator(
            weapon_stat=weapon,
            static_buff=StaticBuff(),  # Empty static buff for now (will be removed in future refactor)
            in_game_buff=in_game_buff,
            enemy_stat=enemy,
            element_order=element_order,
        )

        simulation_config = data.get("simulation", {})

        # Calculate damage
        logger.info("--- Starting damage calculations ---")

        single_hit = calculator.calc_single_hit()
        logger.info(f"Single hit damage: {single_hit}")

        direct_dps = calculator.calc_direct_dps()
        logger.info(f"Direct DPS: {direct_dps}")

        dots_dps = calculator.calc_dots()
        logger.info(f"DOTs DPS: {dots_dps}")

        # Get elemental breakdown
        elem_total = calculator.calc_elem()
        logger.info(f"Elemental total: {elem_total}")

        # Log intermediate calculations
        base_damage = calculator._get_base()
        crit_multiplier = calculator._get_crit()
        multishot = calculator._get_ms()
        attack_speed = calculator._get_as()
        status_chance = calculator._get_sc()
        crit_chance = calculator._get_cc()
        crit_damage = calculator._get_cd()

        logger.info(
            f"Intermediate calculations - base: {base_damage}, crit_mult: {crit_multiplier}, "
            f"multishot: {multishot}, attack_speed: {attack_speed}, status_chance: {status_chance}, "
            f"crit_chance: {crit_chance}, crit_damage: {crit_damage}"
        )

        logger.info("=== Calculation Complete ===")

        duration = simulation_config.get("duration", 10.0)
        num_simulations = simulation_config.get("num_simulations", 10)

        simulation_result = calculator.simulate_combat_multiple(
            duration=duration, num_simulations=num_simulations, verbose=False
        )

        # Get final element breakdown after combination
        # combined_elements contains the combined elements with weapon
        element_breakdown = calculator.combined_elements.to_dict()
        logger.info(f"Final element breakdown: {element_breakdown}")

        # Build response with ordered dictionaries for consistent display order
        damage = OrderedDict(
            [
                ("direct_dps", direct_dps),
                ("single_hit", single_hit),
            ]
            + [("dot_" + elem + "_dps", dps) for elem, dps in dots_dps.items()]
        )

        stats = OrderedDict(
            [
                ("base_damage_multiplier", base_damage),
                ("multishot", multishot),
                ("critical_chance", crit_chance),
                ("critical_damage", crit_damage),
                ("combined_crit_multiplier", crit_multiplier),
                ("attack_speed", attack_speed),
                ("status_chance", status_chance),
                ("elemental_damage_multiplier", elem_total),
            ]
        )

        result = {
            "success": True,
            "damage": damage,
            "stats": stats,
            "element_breakdown": element_breakdown,
            "simulation_result": simulation_result,
        }

        return jsonify(result)

    except Exception as e:
        import traceback

        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "success": True,
            "status": "healthy",
            "message": "Warframe Damage Calculator API is running",
        }
    )


if __name__ == "__main__":
    import os

    port = int(
        os.environ.get("PORT", 5001)
    )  # Use 5001 by default (5000 conflicts with AirPlay on macOS)
    app.run(debug=True, host="0.0.0.0", port=port)

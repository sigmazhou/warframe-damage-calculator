from flask import Flask, jsonify, request
from flask_cors import CORS
from dataclasses import fields, MISSING
import logging
from collections import OrderedDict
from src.calculator.mod_translator import ModTranslator
from src.calculator.damage_calculator import DamageCalculator
from src.calculator.wf_dataclasses import (
    WeaponStat,
    StaticBuff,
    InGameBuff,
    EnemyStat,
    EnemyFaction,
    EnemyType,
    Elements,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Initialize translator
translator = ModTranslator()


# Helper functions for flattening/unflattening buff fields
def flatten_buff_fields(buff_fields):
    """
    Flatten InGameBuff fields by expanding prejudice and elements into individual fields.

    Args:
        buff_fields: List of field dictionaries from InGameBuff dataclass

    Returns:
        List of flattened field dictionaries
    """
    flattened = []

    for field in buff_fields:
        if field['name'] == 'prejudice':
            # Get faction names from EnemyFaction enum (exclude NONE)
            factions = [faction.value for faction in EnemyFaction if faction != EnemyFaction.NONE]
            for faction in factions:
                flattened.append({
                    'name': f'prejudice_{faction}',
                    'type': 'float',
                    'default': 0.0
                })
        elif field['name'] == 'elements':
            # Get element names from Elements dataclass
            element_names = [f.name for f in fields(Elements)]
            for element in element_names:
                flattened.append({
                    'name': f'element_{element}',
                    'type': 'float',
                    'default': 0.0
                })
        elif field['name'] != 'callbacks':
            # Keep regular fields (exclude callbacks)
            flattened.append(field)

    return flattened


def unflatten_buff_data(buff_data):
    """
    Unflatten buff data by reconstructing prejudice dict and elements dict.

    Args:
        buff_data: Dictionary with flattened keys (e.g., prejudice_grineer, element_heat)

    Returns:
        Dictionary with nested prejudice and elements structures
    """
    processed = {}
    prejudice_dict = {}
    elements_dict = {}

    for key, value in buff_data.items():
        if key.startswith('prejudice_'):
            # Extract faction name (e.g., prejudice_grineer -> grineer)
            faction = key[len('prejudice_'):]
            prejudice_dict[faction] = value
        elif key.startswith('element_'):
            # Extract element name (e.g., element_heat -> heat)
            element = key[len('element_'):]
            elements_dict[element] = value
        else:
            # Regular buff field
            processed[key] = value

    # Add reconstructed nested structures if they have values
    if prejudice_dict:
        processed['prejudice'] = prejudice_dict
    if elements_dict:
        processed['elements'] = elements_dict

    return processed


@app.route('/')
def index():
    """Serve the main HTML page."""
    return app.send_static_file('wf_dmg_calc.html')


@app.route('/api/mods', methods=['GET'])
def get_available_mods():
    """
    Get list of all available mods.

    Returns:
        JSON array of mod objects with name and details
    """
    try:
        mod_names = translator.get_available_mods()
        mods_list = []

        for mod_name in mod_names:
            mod_info = translator.get_mod_info(mod_name)
            mods_list.append({
                'id': mod_name,
                'name': mod_name,
                'max_level': mod_info.get('max_level', 0),
                'stats': {k: v for k, v in mod_info.items()
                         if k not in ['max_level', 'special_notes']}
            })

        return jsonify({
            'success': True,
            'mods': mods_list,
            'count': len(mods_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search-mods', methods=['GET'])
def search_mods():
    """
    Search for mods by name.

    Query params:
        q: Search query string

    Returns:
        JSON array of matching mods
    """
    try:
        query = request.args.get('q', '').lower()

        if len(query) < 2:
            return jsonify({
                'success': True,
                'mods': []
            })

        mod_names = translator.get_available_mods()
        matching_mods = []

        for mod_name in mod_names:
            if query in mod_name.lower():
                mod_info = translator.get_mod_info(mod_name)
                matching_mods.append({
                    'id': mod_name,
                    'name': mod_name,
                    'max_level': mod_info.get('max_level', 0)
                })

        return jsonify({
            'success': True,
            'mods': matching_mods
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/enemy-factions', methods=['GET'])
def get_enemy_factions():
    """
    Get list of available enemy factions from EnemyFaction enum.

    Returns:
        JSON array of enemy faction strings
    """
    try:
        enemy_factions = [enemy_faction.value for enemy_faction in EnemyFaction]

        return jsonify({
            'success': True,
            'enemy_factions': enemy_factions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/enemy-types', methods=['GET'])
def get_enemy_types():
    """
    Get list of available enemy types from EnemyType enum.

    Returns:
        JSON array of enemy type strings
    """
    try:
        enemy_types = [enemy_type.value for enemy_type in EnemyType]

        return jsonify({
            'success': True,
            'enemy_types': enemy_types
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ingame-buffs', methods=['GET'])
def get_ingame_buffs():
    """
    Get list of available in-game buff fields from InGameBuff dataclass.
    Returns flattened fields with prejudice_* and element_* expanded.

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

            buff_fields.append({
                'name': field.name,
                'type': field.type.__name__ if hasattr(field.type, '__name__') else str(field.type),
                'default': default_value
            })

        # Flatten the fields (expand prejudice and elements)
        flattened_fields = flatten_buff_fields(buff_fields)

        return jsonify({
            'success': True,
            'buffs': flattened_fields
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/calculate-damage', methods=['POST'])
def calculate_damage():
    """
    Calculate damage based on weapon stats, mods, enemy type, and buffs.

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
            "mods": ["mod_name1", "mod_name2", ...],
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
            }
        }

    Returns:
        JSON object with calculated damage values
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        # Log raw incoming request data
        logger.info("=== Calculate Damage Request ===")
        logger.info(f"Raw request data: {data}")

        # Parse weapon stats
        weapon_data = data.get('weapon', {})
        weapon = WeaponStat()
        weapon.damage = weapon_data.get('damage', 1)
        weapon.attack_speed = weapon_data.get('attack_speed', 1)
        weapon.multishot = weapon_data.get('multishot', 1)
        weapon.critical_chance = weapon_data.get('critical_chance', 0)
        weapon.critical_damage = weapon_data.get('critical_damage', 1)
        weapon.status_chance = weapon_data.get('status_chance', 0)
        weapon.status_duration = weapon_data.get('status_duration', 1)

        # Parse weapon elements
        weapon_elements = weapon_data.get('elements', {})
        weapon.elements = Elements(**weapon_elements) if weapon_elements else Elements()

        logger.info(f"Parsed weapon stats: damage={weapon.damage}, attack_speed={weapon.attack_speed}, "
                   f"multishot={weapon.multishot}, crit_chance={weapon.critical_chance}, "
                   f"crit_damage={weapon.critical_damage}, status_chance={weapon.status_chance}")
        logger.info(f"Weapon elements: {weapon.elements.to_dict()}")

        # Parse mods (filter out None/null/empty values)
        mod_list = [mod for mod in data.get('mods', []) if mod]
        logger.info(f"Mods applied: {mod_list}")

        # Parse in-game buffs
        in_game_buffs_data = data.get('in_game_buffs', {})
        logger.info(f"In-game buffs (raw): {in_game_buffs_data}")

        # Unflatten buff data (reconstruct prejudice and elements)
        processed_buffs = unflatten_buff_data(in_game_buffs_data)
        logger.info(f"In-game buffs (processed): {processed_buffs}")

        # Translate mods and buffs
        static_buff, in_game_buff = translator.translate_mods(mod_list, processed_buffs)
        logger.info(f"Static buff - damage: {static_buff.damage}, multishot: {static_buff.multishot}, "
                   f"crit_chance: {static_buff.critical_chance}, crit_damage: {static_buff.critical_damage}")

        # Parse enemy
        enemy_data = data.get('enemy', {})
        enemy = EnemyStat()

        # Parse faction
        faction_str = enemy_data.get('faction', 'none')
        try:
            enemy.faction = EnemyFaction(faction_str.lower())
        except ValueError:
            enemy.faction = EnemyFaction.NONE

        # Parse type
        type_str = enemy_data.get('type', 'none')
        try:
            enemy.type = EnemyType(type_str.lower())
        except ValueError:
            enemy.type = EnemyType.NONE

        logger.info(f"Enemy faction: {enemy.faction.value}, type: {enemy.type.value}")

        # Create calculator
        calculator = DamageCalculator(
            weapon_stat=weapon,
            static_buff=static_buff,
            in_game_buff=in_game_buff,
            enemy_stat=enemy
        )

        # Calculate damage
        logger.info("--- Starting damage calculations ---")

        single_hit = calculator.calc_single_hit()
        logger.info(f"Single hit damage: {single_hit}")

        direct_dps = calculator.calc_direct()
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

        logger.info(f"Intermediate calculations - base: {base_damage}, crit_mult: {crit_multiplier}, "
                   f"multishot: {multishot}, attack_speed: {attack_speed}, status_chance: {status_chance}")

        logger.info("=== Calculation Complete ===")

        # Build response with ordered dictionaries for consistent display order
        damage = OrderedDict([
            ('direct_dps', direct_dps),
            ('single_hit', single_hit),
        ] + [('dot_' + elem + '_dps', dps) for elem, dps in dots_dps.items()])

        stats = OrderedDict([
            ('base_damage', base_damage),
            ('multishot', multishot),
            ('critical_multiplier', crit_multiplier),
            ('attack_speed', attack_speed),
            ('status_chance', status_chance),
            ('elemental_total', elem_total)
        ])

        result = {
            'success': True,
            'damage': damage,
            'stats': stats
        }

        return jsonify(result)

    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'Warframe Damage Calculator API is running'
    })


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))  # Use 5001 by default (5000 conflicts with AirPlay on macOS)
    app.run(debug=True, host='0.0.0.0', port=port)

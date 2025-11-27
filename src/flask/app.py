from flask import Flask, jsonify, request
from flask_cors import CORS
from dataclasses import fields
from src.calculator.mod_translator import ModTranslator
from src.calculator.damage_calculator import DamageCalculator
from src.calculator.dataclasses import (
    WeaponStat,
    StaticBuff,
    InGameBuff,
    EnemyStat,
    EnemyType,
    Elements,
)

app = Flask(__name__, static_folder='../client', static_url_path='')
CORS(app)  # Enable CORS for all routes

# Initialize translator
translator = ModTranslator()


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

    Returns:
        JSON object with buff field names and their types
    """
    try:
        buff_fields = []

        for field in fields(InGameBuff):
            buff_fields.append({
                'name': field.name,
                'type': field.type.__name__ if hasattr(field.type, '__name__') else str(field.type),
                'default': field.default if field.default is not field.default_factory else None
            })

        return jsonify({
            'success': True,
            'buffs': buff_fields
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
                "faction": str  # EnemyType value
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

        # Parse mods
        mod_list = data.get('mods', [])

        # Parse in-game buffs
        in_game_buffs_data = data.get('in_game_buffs', {})

        # Translate mods and buffs
        static_buff, in_game_buff = translator.translate_mods(mod_list, in_game_buffs_data)

        # Parse enemy
        enemy_data = data.get('enemy', {})
        enemy = EnemyStat()
        faction_str = enemy_data.get('faction', 'grineer')

        # Convert faction string to EnemyType enum
        try:
            enemy.faction = EnemyType(faction_str.lower())
        except ValueError:
            enemy.faction = EnemyType.GRINEER

        # Create calculator
        calculator = DamageCalculator(
            weapon_stat=weapon,
            static_buff=static_buff,
            in_game_buff=in_game_buff,
            enemy_stat=enemy
        )

        # Calculate damage
        single_hit = calculator.calc_single_hit()
        direct_dps = calculator.calc_direct()
        fire_dot_dps = calculator.calc_fire_dot()

        # Get elemental breakdown
        elem_total = calculator.calc_elem()

        # Build response
        result = {
            'success': True,
            'damage': {
                'single_hit': single_hit,
                'direct_dps': direct_dps,
                'fire_dot_dps': fire_dot_dps,
                'total_dps': direct_dps + fire_dot_dps
            },
            'stats': {
                'base_damage': calculator._get_base(),
                'critical_multiplier': calculator._get_crit(),
                'multishot': calculator._get_ms(),
                'attack_speed': calculator._get_as(),
                'status_chance': calculator._get_sc(),
                'elemental_total': elem_total
            },
            'buffs_applied': {
                'static': {
                    'damage': static_buff.damage,
                    'critical_chance': static_buff.critical_chance,
                    'critical_damage': static_buff.critical_damage,
                    'multishot': static_buff.multishot,
                    'attack_speed': static_buff.attack_speed,
                    'status_chance': static_buff.status_chance,
                    'elements': static_buff.elements.to_dict(),
                    'prejudice': static_buff.prejudice
                },
                'in_game': {
                    'galvanized_shot': in_game_buff.galvanized_shot,
                    'galvanized_aptitude': in_game_buff.galvanized_aptitude,
                    'final_additive_cd': in_game_buff.final_additive_cd,
                    'attack_speed': in_game_buff.attack_speed,
                    'num_debuffs': in_game_buff.num_debuffs,
                    'final_multiplier': in_game_buff.final_multiplier,
                    'elements': in_game_buff.elements.to_dict()
                }
            }
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

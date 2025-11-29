import json
from dataclasses import fields
from pathlib import Path
from src.calculator.wf_dataclasses import StaticBuff, InGameBuff, Elements
from src.data.mod_callbacks import CALLBACK_MAPPING


# Mapping from mod stat names to our dataclass field names
STAT_MAPPING = {
    "damage": "damage",
    "critical_chance": "critical_chance",
    "critical_damage": "critical_damage",
    "status_chance": "status_chance",
    "status_duration": "status_duration",
    "multishot": "multishot",
    "fire_rate": "attack_speed",
    "attack_speed": "attack_speed",
    "melee_damage": "damage",  # Melee damage is just base damage
}

# Mapping for element damage types
ELEMENT_MAPPING = {
    "impact_damage": "impact",
    "puncture_damage": "puncture",
    "slash_damage": "slash",
    "cold_damage": "cold",
    "electricity_damage": "electricity",
    "heat_damage": "heat",
    "toxin_damage": "toxin",
    "blast_damage": "blast",
    "corrosive_damage": "corrosive",
    "gas_damage": "gas",
    "magnetic_damage": "magnetic",
    "radiation_damage": "radiation",
    "viral_damage": "viral",
    "void_damage": "void",
    "tau_damage": "tau",
}

# Mapping for faction damage (faction)
FACTION_MAPPING = {
    "damage_vs_grineer": "grineer",
    "damage_vs_corpus": "corpus",
    "damage_vs_infested": "infested",
    "damage_vs_corrupted": "corrupted",
}


class ModParser:
    """Parses mod names and in-game stats to StaticBuff and InGameBuff instances."""

    def __init__(self, mod_data_path: str = "src/data/mod_data.txt"):
        """
        Initialize the parser with mod data.

        Args:
            mod_data_path: Path to the JSON file containing mod data
        """
        self.mod_data_path = Path(mod_data_path)
        self.mod_data = self._load_mod_data()

    def _load_mod_data(self) -> dict:
        """Load mod data from JSON file."""
        with open(self.mod_data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def parse_mods_and_stats(
        self, mod_names: list[str], in_game_stats: dict = None, rivens: dict = None
    ) -> tuple[InGameBuff, list[str], list[str]]:
        """
        Parse a list of mod names, rivens, and in-game stats into InGameBuff and element orders.

        Args:
            mod_names: List of mod names to include (can include riven IDs like "riven_1")
            in_game_stats: Dictionary of in-game stats (optional)
                - galvanized_shot: int (number of stacks)
                - galvanized_aptitude: int (number of stacks)
                - num_debuffs: int (number of debuffs on enemy)
                - final_additive_cd: float (additional critical damage)
                - attack_speed: float (attack speed bonus)
                - final_multiplier: float (final damage multiplier)
                - elements: dict (additional elemental damage)
                - element_order: list (order of elements for in-game buffs)
            rivens: Dictionary of riven data (optional)
                - Keys are riven IDs (e.g., "riven_1")
                - Values are dicts with stat key-value pairs (same format as in-game buffs)
                  Example: {"damage": 2.15, "element_heat": 1.20}

        Returns:
            Tuple of (InGameBuff, element_order_from_mods, element_order_from_igb)
        """
        in_game_buff = InGameBuff()

        # Initialize with default values
        in_game_buff.damage = 0
        in_game_buff.attack_speed = 0
        in_game_buff.multishot = 0
        in_game_buff.critical_chance = 0
        in_game_buff.critical_damage = 0
        in_game_buff.status_chance = 0
        in_game_buff.status_duration = 0
        in_game_buff.elements = Elements()
        in_game_buff.faction = {}

        # Track element order from mods
        element_order_from_mods = []

        # Ensure rivens is not None
        if rivens is None:
            rivens = {}

        # Process each mod (including rivens)
        for mod_name in mod_names:
            # Check if this is a riven
            if mod_name.startswith("riven_"):
                if mod_name in rivens:
                    riven_data = rivens[mod_name]
                    # Riven data is already in the same format as in-game buffs
                    riven_element_order = self._apply_stats_to_buff(riven_data, in_game_buff)
                    element_order_from_mods.extend(riven_element_order)
                else:
                    print(f"Warning: Riven '{mod_name}' not found in rivens data")
                continue

            # Regular mod processing
            if mod_name not in self.mod_data:
                print(f"Warning: Mod '{mod_name}' not found in database")
                continue

            mod = self.mod_data[mod_name]
            mod_element_order = self._apply_stats_to_buff(mod, in_game_buff, mod_name)
            element_order_from_mods.extend(mod_element_order)

        # Process in-game stats
        element_order_from_igb = []
        if in_game_stats:
            element_order_from_igb = self._apply_stats_to_buff(
                in_game_stats, in_game_buff
            )

        return in_game_buff, element_order_from_mods, element_order_from_igb

    def _add_value_to_field(
        self, in_game_buff: InGameBuff, field_name: str, value: float
    ) -> None:
        """
        Add a value to a field in InGameBuff.

        Args:
            in_game_buff: InGameBuff to modify
            field_name: Name of the field to modify
            value: Value to add
        """
        if hasattr(in_game_buff, field_name):
            current_value = getattr(in_game_buff, field_name)
            if isinstance(current_value, (int, float)):
                setattr(in_game_buff, field_name, current_value + value)

    def _add_element_to_buff(
        self, in_game_buff: InGameBuff, element_name: str, value: float
    ) -> bool:
        """
        Add an element value to InGameBuff.elements.

        Args:
            in_game_buff: InGameBuff to modify
            element_name: Name of the element
            value: Value to add

        Returns:
            True if element was added with value > 0 (for tracking element order)
        """
        if hasattr(in_game_buff.elements, element_name):
            current_value = getattr(in_game_buff.elements, element_name)
            setattr(in_game_buff.elements, element_name, current_value + value)
            return value > 0
        return False

    def _add_faction_to_buff(
        self, in_game_buff: InGameBuff, faction_name: str, value: float
    ) -> None:
        """
        Add a faction damage bonus to InGameBuff.faction.

        Args:
            in_game_buff: InGameBuff to modify
            faction_name: Name of the faction
            value: Value to add
        """
        if faction_name in in_game_buff.faction:
            in_game_buff.faction[faction_name] += value
        else:
            in_game_buff.faction[faction_name] = value

    def _apply_stats_to_buff(
        self, stats: dict, in_game_buff: InGameBuff, mod_name: str = None
    ) -> list[str]:
        """
        Apply stats (from mods or in-game sources) to InGameBuff.

        This unified method handles both:
        - Mod stats with mapped keys (e.g., "damage_vs_grineer" -> "grineer")
        - In-game stats with direct keys and nested dicts (e.g., "elements": {...})

        Args:
            stats: Dictionary of stats to apply (mod data or in-game stats)
            in_game_buff: InGameBuff to modify
            mod_name: Optional mod name for callback registration

        Returns:
            List of element names added (for element order tracking)
        """
        # TODO: clean this a bit

        element_order = []

        for stat_key, value in stats.items():
            # Skip non-stat fields (mod-specific)
            if stat_key in [
                "max_level",
                "special_notes",
                "on_headshot",
                "on_kill",
                "on_critical_hit",
            ]:
                continue

            # Skip special cases that shouldn't be in InGameBuff (mod-specific)
            if "per_status" in stat_key or "per_combo" in stat_key:
                continue

            # Try mod stat mappings first
            if stat_key in STAT_MAPPING:
                field_name = STAT_MAPPING[stat_key]
                self._add_value_to_field(in_game_buff, field_name, value)

            # Try element mappings
            elif stat_key in ELEMENT_MAPPING:
                element_name = ELEMENT_MAPPING[stat_key]
                if self._add_element_to_buff(in_game_buff, element_name, value):
                    element_order.append(element_name)

            # Try faction mappings
            elif stat_key in FACTION_MAPPING:
                faction_name = FACTION_MAPPING[stat_key]
                self._add_faction_to_buff(in_game_buff, faction_name, value)

            # Handle nested elements dictionary (in-game stats)
            elif stat_key == "elements" and isinstance(value, dict):
                for elem_key, elem_value in value.items():
                    if self._add_element_to_buff(in_game_buff, elem_key, elem_value):
                        element_order.append(elem_key)

            # Handle nested faction dictionary (in-game stats)
            elif stat_key == "faction" and isinstance(value, dict):
                for faction_key, faction_value in value.items():
                    self._add_faction_to_buff(in_game_buff, faction_key, faction_value)

            # Try direct field mapping (in-game stats or unmapped mod stats)
            else:
                if hasattr(in_game_buff, stat_key):
                    self._add_value_to_field(in_game_buff, stat_key, value)
                elif mod_name is None:
                    # Only warn for in-game stats, not for unmapped mod keys
                    print(f"Warning: Stat '{stat_key}' not found in InGameBuff")

        # Add callbacks (mod-specific)
        if mod_name and mod_name in CALLBACK_MAPPING:
            in_game_buff.callbacks.append(CALLBACK_MAPPING[mod_name])

        # Reverse element order for riven buffs (list.reverse() returns None, so reverse in-place then return)
        element_order.reverse()
        return element_order

    def get_available_mods(self) -> list[str]:
        """Get list of all available mod names."""
        return list(self.mod_data.keys())

    def get_mod_info(self, mod_name: str) -> dict:
        """
        Get information about a specific mod.

        Args:
            mod_name: Name of the mod

        Returns:
            Dictionary with mod information
        """
        return self.mod_data.get(mod_name, {})


if __name__ == "__main__":
    """Test the parser with the Dual Toxocyst example from wf_dmg_calc.py"""

    parser = ModParser()

    # Define mods for the build (matching the example in wf_dmg_calc.py)
    mods = [
        "hornet_strike",  # 2.2 damage
        "primed_target_cracker",  # 1.1 crit damage
        "barrel_diffusion",  # 1.2 multishot
        "lethal_torrent",  # 0.6 fire rate + 0.6 multishot
        "primed_pistol_gambit",  # 1.87 crit chance
        # Additional mods would go here...
    ]

    # In-game stats
    in_game_stats = {
        "galvanized_shot": 0,
        "galvanized_aptitude": 0,
        "final_additive_cd": 1.2,  # Pet crit multiplier bonus
        "attack_speed": 0.6,  # Pet attack speed bonus
        "num_debuffs": 0,
    }

    in_game_buff = parser.parse_mods_and_stats(mods, in_game_stats)

    print("InGameBuff:")
    print(f"  damage: {in_game_buff.damage}")
    print(f"  attack_speed: {in_game_buff.attack_speed}")
    print(f"  multishot: {in_game_buff.multishot}")
    print(f"  critical_chance: {in_game_buff.critical_chance}")
    print(f"  critical_damage: {in_game_buff.critical_damage}")
    print(f"  status_chance: {in_game_buff.status_chance}")
    print(f"  elements: {in_game_buff.elements.to_dict()}")
    print(f"  faction: {in_game_buff.faction}")
    print(f"  galvanized_shot: {in_game_buff.galvanized_shot}")
    print(f"  galvanized_aptitude: {in_game_buff.galvanized_aptitude}")
    print(f"  final_additive_cd: {in_game_buff.final_additive_cd}")
    print(f"  attack_speed: {in_game_buff.attack_speed}")
    print(f"  num_debuffs: {in_game_buff.num_debuffs}")
    print(f"  final_multiplier: {in_game_buff.final_multiplier}")

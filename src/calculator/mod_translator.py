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

# Mapping for faction damage (prejudice)
FACTION_MAPPING = {
    "damage_vs_grineer": "grineer",
    "damage_vs_corpus": "corpus",
    "damage_vs_infested": "infested",
    "damage_vs_corrupted": "corrupted",
}


class ModTranslator:
    """Translates mod names and in-game stats to StaticBuff and InGameBuff instances."""

    def __init__(self, mod_data_path: str = "src/data/mod_data.txt"):
        """
        Initialize the translator with mod data.

        Args:
            mod_data_path: Path to the JSON file containing mod data
        """
        self.mod_data_path = Path(mod_data_path)
        self.mod_data = self._load_mod_data()

    def _load_mod_data(self) -> dict:
        """Load mod data from JSON file."""
        with open(self.mod_data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def translate_mods_and_stats(
        self, mod_names: list[str], in_game_stats: dict = None
    ) -> tuple[InGameBuff, list[str], list[str]]:
        """
        Translate a list of mod names and in-game stats into InGameBuff and element orders.

        Args:
            mod_names: List of mod names to include
            in_game_stats: Dictionary of in-game stats (optional)
                - galvanized_shot: int (number of stacks)
                - galvanized_aptitude: int (number of stacks)
                - num_debuffs: int (number of debuffs on enemy)
                - final_additive_cd: float (additional critical damage)
                - attack_speed: float (attack speed bonus)
                - final_multiplier: float (final damage multiplier)
                - elements: dict (additional elemental damage)
                - element_order: list (order of elements for in-game buffs)

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
        in_game_buff.prejudice = {}

        # Track element order from mods
        element_order_from_mods = []

        # Process each mod
        for mod_name in mod_names:
            if mod_name not in self.mod_data:
                print(f"Warning: Mod '{mod_name}' not found in database")
                continue

            mod = self.mod_data[mod_name]
            mod_element_order = self._apply_mod_to_buff(mod_name, mod, in_game_buff)
            element_order_from_mods.extend(mod_element_order)

        # Process in-game stats
        element_order_from_igb = []
        if in_game_stats:
            element_order_from_igb = self._apply_in_game_stats(in_game_stats, in_game_buff)

        return in_game_buff, element_order_from_mods, element_order_from_igb

    def _apply_mod_to_buff(self, mod_name: str, mod: dict, in_game_buff: InGameBuff) -> list[str]:
        """
        Apply a single mod's effects to the InGameBuff.

        Args:
            mod_name: Name of the mod
            mod: Mod data dictionary
            in_game_buff: InGameBuff to modify

        Returns:
            List of element names added by this mod (for element order tracking)
        """
        mod_element_order = []

        for stat_key, value in mod.items():
            # Skip non-stat fields
            if stat_key in ["max_level", "special_notes", "on_headshot", "on_kill", "on_critical_hit"]:
                continue

            # Handle special cases that shouldn't be in StaticBuff
            if "per_status" in stat_key or "per_combo" in stat_key:
                continue

            # Map to general stat
            if stat_key in STAT_MAPPING:
                field_name = STAT_MAPPING[stat_key]
                current_value = getattr(in_game_buff, field_name)
                setattr(in_game_buff, field_name, current_value + value)

            # Map to element
            elif stat_key in ELEMENT_MAPPING:
                element_name = ELEMENT_MAPPING[stat_key]
                current_value = getattr(in_game_buff.elements, element_name)
                setattr(in_game_buff.elements, element_name, current_value + value)

                # Track all elements for combination order (skip if value is 0)
                if value > 0:
                    mod_element_order.append(element_name)

            # Map to faction (prejudice)
            elif stat_key in FACTION_MAPPING:
                faction_name = FACTION_MAPPING[stat_key]
                if faction_name in in_game_buff.prejudice:
                    in_game_buff.prejudice[faction_name] += value
                else:
                    in_game_buff.prejudice[faction_name] = value

            # Check if it's an attribute in StaticBuff that we haven't explicitly mapped
            else:
                if hasattr(in_game_buff, stat_key):
                    current_value = getattr(in_game_buff, stat_key)
                    if isinstance(current_value, (int, float)):
                        setattr(in_game_buff, stat_key, current_value + value)

        # callbacks
        if mod_name in CALLBACK_MAPPING:
            in_game_buff.callbacks.append(CALLBACK_MAPPING[mod_name])

        return mod_element_order

    def _apply_in_game_stats(self, in_game_stats: dict, in_game_buff: InGameBuff) -> list[str]:
        """
        Apply in-game stats to InGameBuff.

        Args:
            in_game_stats: Dictionary of in-game stats
            in_game_buff: InGameBuff to modify

        Returns:
            List of element names from in-game buffs (for element order tracking)
        """
        igb_element_order = []

        # Direct mappings for InGameBuff fields
        for key, value in in_game_stats.items():
            if key == "elements":
                # Handle element dictionary
                for elem_key, elem_value in value.items():
                    if hasattr(in_game_buff.elements, elem_key):
                        setattr(in_game_buff.elements, elem_key, elem_value)
                        # Track all elements for combination order (skip if value is 0)
                        if elem_value > 0:
                            igb_element_order.append(elem_key)
            elif hasattr(in_game_buff, key):
                setattr(in_game_buff, key, value)
            else:
                print(f"Warning: In-game stat '{key}' not found in InGameBuff")

        return igb_element_order

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
    """Test the translator with the Dual Toxocyst example from wf_dmg_calc.py"""

    translator = ModTranslator()

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

    in_game_buff = translator.translate_mods_and_stats(mods, in_game_stats)

    print("InGameBuff:")
    print(f"  damage: {in_game_buff.damage}")
    print(f"  attack_speed: {in_game_buff.attack_speed}")
    print(f"  multishot: {in_game_buff.multishot}")
    print(f"  critical_chance: {in_game_buff.critical_chance}")
    print(f"  critical_damage: {in_game_buff.critical_damage}")
    print(f"  status_chance: {in_game_buff.status_chance}")
    print(f"  elements: {in_game_buff.elements.to_dict()}")
    print(f"  prejudice: {in_game_buff.prejudice}")
    print(f"  galvanized_shot: {in_game_buff.galvanized_shot}")
    print(f"  galvanized_aptitude: {in_game_buff.galvanized_aptitude}")
    print(f"  final_additive_cd: {in_game_buff.final_additive_cd}")
    print(f"  attack_speed: {in_game_buff.attack_speed}")
    print(f"  num_debuffs: {in_game_buff.num_debuffs}")
    print(f"  final_multiplier: {in_game_buff.final_multiplier}")

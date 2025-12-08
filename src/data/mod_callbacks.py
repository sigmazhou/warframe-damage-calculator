from collections.abc import Callable
from enum import StrEnum, auto
from typing import Any


class CallbackType(StrEnum):
    IN_GAME_BUFF = auto()


class CallBack:
    func: Callable[[Any], None]
    type: CallbackType
    priority_group: int  # Lower values execute first

    def __init__(self, func: Callable[[Any], None], type: CallbackType, priority_group: int = 0):
        self.func = func
        self.type = type
        self.priority_group = priority_group

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


# Galvanized Shot (Pistol): +80% status chance base. On kill: +40% damage per status type for 14s, stacks up to 3x
# Always assumes headshot/active. Uses galvanized_shot stacks from InGameBuff.
galvanized_shot = CallBack(
    lambda igb: setattr(igb, "damage", igb.damage + igb.galvanized_shot * igb.num_debuffs * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Secondary Enervate (Arcane): Average crit chance boost
# Priority group 1: executes after all other callbacks (priority 0)
secondary_enervate = CallBack(
    lambda igb: setattr(igb, "critical_chance", (3.05 + igb.critical_chance) / 2),
    CallbackType.IN_GAME_BUFF,
    priority_group=1,
)


# Secondary Outburst (Arcane): +20% of crit chance buff & crit dmg buff per combo multiplier
# Max 240% (at 12x combo). Uses combo_multiplier directly (no -1).
# Priority group 1: executes after all other callbacks (priority 0)
def _secondary_outburst(igb):
    bonus = igb.combo_multiplier * 0.2
    igb.critical_chance += igb.critical_chance * bonus
    igb.critical_damage += igb.critical_damage * bonus


secondary_outburst = CallBack(
    _secondary_outburst,
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Scope (Rifle): +120% crit chance base (in mod_data). +40% crit chance per stack.
# Always assumes headshot. Uses galvanized_scope stacks from InGameBuff.
galvanized_scope = CallBack(
    lambda igb: setattr(igb, "critical_chance", igb.critical_chance + igb.galvanized_scope * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Crosshairs (Pistol): +120% crit chance base (in mod_data). +40% crit chance per stack.
# Always assumes headshot. Uses galvanized_crosshairs stacks from InGameBuff.
galvanized_crosshairs = CallBack(
    lambda igb: setattr(igb, "critical_chance", igb.critical_chance + igb.galvanized_crosshairs * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Aptitude (Rifle): +80% status chance base (in mod_data). +40% damage per status type per stack.
# Always assumes active. Uses galvanized_aptitude stacks and num_debuffs from InGameBuff.
galvanized_aptitude = CallBack(
    lambda igb: setattr(igb, "damage", igb.damage + igb.galvanized_aptitude * igb.num_debuffs * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Savvy (Shotgun): +80% status chance base (in mod_data). +40% damage per status type per stack.
# Always assumes active. Uses galvanized_savvy stacks and num_debuffs from InGameBuff.
galvanized_savvy = CallBack(
    lambda igb: setattr(igb, "damage", igb.damage + igb.galvanized_savvy * igb.num_debuffs * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Chamber (Rifle): +80% multishot base (in mod_data). +30% multishot per stack.
# Uses galvanized_chamber stacks from InGameBuff.
galvanized_chamber = CallBack(
    lambda igb: setattr(igb, "multishot", igb.multishot + igb.galvanized_chamber * 0.3),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Diffusion (Pistol): +110% multishot base (in mod_data). +30% multishot per stack.
# Uses galvanized_diffusion stacks from InGameBuff.
galvanized_diffusion = CallBack(
    lambda igb: setattr(igb, "multishot", igb.multishot + igb.galvanized_diffusion * 0.3),
    CallbackType.IN_GAME_BUFF,
)

# Galvanized Hell (Shotgun): +110% multishot base (in mod_data). +30% multishot per stack.
# Uses galvanized_hell stacks from InGameBuff.
galvanized_hell = CallBack(
    lambda igb: setattr(igb, "multishot", igb.multishot + igb.galvanized_hell * 0.3),
    CallbackType.IN_GAME_BUFF,
)

# Condition Overload (Melee): +80% damage per status type on target
# Uses num_debuffs from InGameBuff. The 0.8 multiplier is defined in mod_data as damage_per_status.
condition_overload = CallBack(
    lambda igb: setattr(igb, "damage", igb.damage + igb.num_debuffs * 0.8),
    CallbackType.IN_GAME_BUFF,
)

# Blood Rush (Melee): +40% crit chance per combo multiplier level
# Uses combo_multiplier from InGameBuff (1-12, where 1 = 1x combo, 12 = 12x combo)
# Subtracts 1 since combo level 1 gives no bonus.
blood_rush = CallBack(
    lambda igb: setattr(igb, "critical_chance", igb.critical_chance + (igb.combo_multiplier - 1) * 0.4),
    CallbackType.IN_GAME_BUFF,
)

# Weeping Wounds (Melee): +40% status chance per combo multiplier level
# Uses combo_multiplier from InGameBuff (1-12, where 1 = 1x combo, 12 = 12x combo)
# Subtracts 1 since combo level 1 gives no bonus.
weeping_wounds = CallBack(
    lambda igb: setattr(igb, "status_chance", igb.status_chance + (igb.combo_multiplier - 1) * 0.4),
    CallbackType.IN_GAME_BUFF,
)


CALLBACK_MAPPING = {
    # Pistol
    "galvanized_shot": galvanized_shot,  # +40% damage per status type per stack
    "galvanized_diffusion": galvanized_diffusion,  # +30% multishot per stack
    "galvanized_crosshairs": galvanized_crosshairs,  # +40% crit chance per stack
    # Arcanes
    "secondary_enervate": secondary_enervate,  # Average crit chance with 3.05
    "secondary_outburst": secondary_outburst,  # +20% crit chance/dmg buff per combo (max 240%)
    # Rifle
    "galvanized_scope": galvanized_scope,  # +40% crit chance per stack
    "galvanized_aptitude": galvanized_aptitude,  # +40% damage per status type per stack
    "galvanized_chamber": galvanized_chamber,  # +30% multishot per stack
    # Shotgun
    "galvanized_savvy": galvanized_savvy,  # +40% damage per status type per stack
    "galvanized_hell": galvanized_hell,  # +30% multishot per stack
    # Melee
    "condition_overload": condition_overload,  # +80% damage per status type on target
    "blood_rush": blood_rush,  # +60% crit chance per combo multiplier
    "weeping_wounds": weeping_wounds,  # +40% status chance per combo multiplier
}

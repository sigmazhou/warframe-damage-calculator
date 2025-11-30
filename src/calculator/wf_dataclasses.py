import copy
import math
import pdb

from watchpoints import watch
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from enum import StrEnum, auto
from typing import Any, TypeVar, Optional

from src.calculator.dot_dataclasses import DotState, DotType

Self = TypeVar("Self", bound="_SupportsMath")

ELEMENT_COMBINATION_MAP = {
    "cold": {"electricity": "magnetic", "heat": "blast", "toxin": "viral"},
    "electricity": {"cold": "magnetic", "heat": "radiation", "toxin": "corrosive"},
    "heat": {"cold": "blast", "electricity": "radiation", "toxin": "gas"},
    "toxin": {"cold": "viral", "electricity": "corrosive", "heat": "gas"},
}


@dataclass
class _SupportsMath:
    """Base class for dataclasses that support math operators."""

    def __add__(self: Self, other: Self) -> Self:
        """
        Add two dataclass instances together, combining all field values.

        For each field in self, attempts to add values from others.
        Fields missing in other are copied from self using copy.copy().
        Subclasses can customize behavior through _combine_field.

        Args:
            other: Another instance compatible for addition

        Returns:
            New instance of the same type as self with combined values
        """
        if not isinstance(other, _SupportsMath):
            return NotImplemented

        combined_values = self._add_fields(other, inplace=False)
        return type(self)(**combined_values)

    def __iadd__(self: Self, other: Self) -> Self:
        """
        In-place addition of another dataclass instance.

        Modifies self by adding values from other for each field.
        Subclasses can customize behavior through _combine_field.

        Args:
            other: Another instance compatible for addition

        Returns:
            Self with updated values
        """
        if not isinstance(other, _SupportsMath):
            return NotImplemented

        self._add_fields(other, inplace=True)
        return self

    def __mul__(self: Self, other: int | float) -> Self:
        """
        Multiply a dataclass instance by a scalar, multiplying all field values.

        Args:
            other: Scalar multiplier

        Returns:
            New instance of the same type as self with multiplied values
        """
        if not isinstance(other, (int, float)):
            return NotImplemented

        new_values = {f.name: getattr(self, f.name) * other for f in fields(self)}
        return type(self)(**new_values)

    def __imul__(self: Self, other: int | float) -> Self:
        """
        Multiply a dataclass instance by a scalar, multiplying all field values.

        Args:
            other: Scalar multiplier

        Returns:
            New instance of the same type as self with multiplied values
        """
        if not isinstance(other, (int, float)):
            return NotImplemented

        for f in fields(self):
            setattr(self, f.name, getattr(self, f.name) * other)
        return self

    def _add_fields(self, other, inplace: bool = False):
        """
        Helper to combine fields from self and other.

        Args:
            other: Another _SupportsMath instance
            inplace: If True, modify self in-place; if False, return dict of combined values

        Returns:
            Dict of combined values if inplace=False, None if inplace=True
        """
        combined_values = {} if not inplace else None

        for f in fields(self):
            self_value = getattr(self, f.name)

            if hasattr(other, f.name):
                other_value = getattr(other, f.name)
                new_value = self._add_field(f.name, self_value, other_value, inplace)

                if inplace:
                    setattr(self, f.name, new_value)
                else:
                    combined_values[f.name] = new_value
            else:
                # Field doesn't exist in other
                if not inplace:
                    combined_values[f.name] = copy.copy(self_value)
                # For inplace, keep self's value unchanged (no action needed)

        return combined_values

    def _add_field(self, name: str, self_value, other_value, inplace: bool = False):
        """
        Combine a field value from self and other.

        Override this method to customize how specific fields are combined.

        Args:
            name: Field name
            self_value: Value from self
            other_value: Value from other
            inplace: If True, modify mutable objects in-place when possible

        Returns:
            Combined value
        """
        # Handle dict specially (dict + dict doesn't work in Python)
        # For dicts, sum values for common keys, add unique keys
        if isinstance(self_value, dict) and isinstance(other_value, dict):
            if inplace:
                # Modify dict in-place
                for key, value in other_value.items():
                    if key in self_value:
                        self_value[key] = self_value[key] + value  # Sum values
                    else:
                        self_value[key] = value  # Add new key
                return self_value
            else:
                # Create new dict
                combined_dict = self_value.copy()
                for key, value in other_value.items():
                    if key in combined_dict:
                        combined_dict[key] = combined_dict[key] + value  # Sum values
                    else:
                        combined_dict[key] = value  # Add new key
                return combined_dict

        # Try direct addition (works for numbers, strings, lists, _SupportsMath objects, etc.)
        try:
            if inplace and hasattr(self_value, "__iadd__"):
                # Use in-place addition if available
                self_value += other_value
                return self_value
            else:
                # Use regular addition
                return self_value + other_value
        except (TypeError, AttributeError):
            # Addition not supported, use self's value
            return copy.copy(self_value)


# TODO: kill all hard coded strings
class Element(StrEnum):
    IMPACT = auto()
    PUNCTURE = auto()
    SLASH = auto()
    COLD = auto()
    ELECTRICITY = auto()
    HEAT = auto()
    TOXIN = auto()
    CORROSIVE = auto()
    RADIATION = auto()
    VIRAL = auto()
    GAS = auto()
    MAGNETIC = auto()
    BLAST = auto()
    VOID = auto()
    TAU = auto()
    TRUE_DMG = auto()


@dataclass
class Elements(_SupportsMath):
    """Represents elemental and physical damage values for weapons."""

    # Physical damage types
    impact: float = 0.0
    puncture: float = 0.0
    slash: float = 0.0

    # Basic elemental damage types
    cold: float = 0.0
    electricity: float = 0.0
    heat: float = 0.0
    toxin: float = 0.0

    cold_standalone: float = 0.0
    electricity_standalone: float = 0.0
    heat_standalone: float = 0.0
    toxin_standalone: float = 0.0

    # Combined elemental damage types
    blast: float = 0.0
    corrosive: float = 0.0
    gas: float = 0.0
    magnetic: float = 0.0
    radiation: float = 0.0
    viral: float = 0.0

    # Special damage types
    void: float = 0.0
    tau: float = 0.0
    true_dmg: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary format, excluding zero values."""
        return {k: v for k, v in self.__dict__.items() if v != 0.0}

    def total(self) -> float:
        """Calculate total damage across all elements."""
        return sum(self.__dict__.values())

    def total_with_vulnerability(self, vulnerability: "Elements") -> float:
        """Calculate total damage across all elements with vulnerability."""
        total = 0.0
        for f in fields(self):
            total += getattr(self, f.name) * getattr(vulnerability, f.name)
        return total

    def set_all(self, value: float) -> None:
        """Set all element values to the same value."""
        for f in fields(self):
            setattr(self, f.name, value)

    def set_all_zeroes_to_value(self, value: float) -> None:
        for f in fields(self):
            if getattr(self, f.name) == 0.0:
                setattr(self, f.name, value)

    def get_element(self, element: str) -> float:
        """Get the value of an element, including standalone elements if they exist."""
        if element in ELEMENT_COMBINATION_MAP:
            return getattr(self, element) + getattr(self, element + "_standalone")
        return getattr(self, element)

    def combine_elements(
            self, element_order: list[str], combine_standalone: bool = True
    ) -> None:
        visited = set()
        element_order_clean = []
        for e in element_order:
            if e in ELEMENT_COMBINATION_MAP and e not in visited:
                visited.add(e)
                element_order_clean.append(e)
        while len(element_order_clean) > 1:
            e1 = element_order_clean.pop(0)
            e2 = element_order_clean.pop(0)
            e_combined = ELEMENT_COMBINATION_MAP[e1][e2]
            setattr(
                self,
                e_combined,
                getattr(self, e1) + getattr(self, e2) + getattr(self, e_combined),
            )
            setattr(self, e1, 0)
            setattr(self, e2, 0)
        if combine_standalone:
            self._combine_standalone_elements()

    def _combine_standalone_elements(self) -> None:
        for e in fields(self):
            if e.name.endswith("_standalone"):
                e_combined = e.name.replace("_standalone", "")
                setattr(
                    self, e_combined, getattr(self, e.name) + getattr(self, e_combined)
                )
                setattr(self, e.name, 0)


@dataclass
class _GeneralStat(_SupportsMath):
    damage: float = 0
    attack_speed: float = 0
    multishot: float = 0
    critical_chance: float = 0
    critical_damage: float = 0
    status_chance: float = 0
    status_duration: float = 0
    elements: Elements = field(default_factory=Elements)
    faction: dict[str, float] = field(default_factory=dict)


@dataclass
class WeaponStat(_GeneralStat):
    damage: float = 1
    attack_speed: float = 1
    multishot: float = 1
    critical_damage: float = 1
    status_duration: float = 1

    def __post_init__(self):
        # Set default elements to puncture=1 if not provided
        self._normalize_elements()

    def _normalize_elements(self) -> None:
        """Normalize elements to have total 1."""
        total = self.elements.total()
        if total == 0:
            self.elements = Elements(impact=1)
        elif total != 1:
            self.elements *= 1 / total


@dataclass
class StaticBuff(_GeneralStat):
    """Buffs from mods."""

    pass


class EnemyFaction(StrEnum):
    NONE = auto()
    GRINEER = auto()
    CORPUS = auto()
    INFESTED = auto()
    OROKIN = auto()
    MURMUR = auto()
    SENTIENT = auto()


class EnemyType(StrEnum):
    NONE = auto()
    TRIDOLON = auto()


@dataclass
class InGameBuff(_GeneralStat):
    """In-game buffs and combat state modifiers."""

    galvanized_shot: int = 0
    galvanized_diffusion: int = 0
    galvanized_aptitude: int = 0
    final_additive_cd: float = 0  # Includes pet crit multiplier bonus
    attack_speed: float = 0.0  # Includes pet attack speed bonus
    num_debuffs: int = 0  # Number of debuffs on enemy
    elements: Elements = field(default_factory=Elements)
    final_multiplier: float = 1.0
    # special mod effects such as galvanized and blood rush
    callbacks: list[Callable[[Any], None]] = field(default_factory=list)


@dataclass
class EnemyStat:
    faction: EnemyFaction = field(default=EnemyFaction.NONE)
    type: EnemyType = field(default=EnemyType.NONE)
    elements_vulnerability: Elements | None = None
    base_armor: float = 0.0
    current_armor: float = 0.0

    active_debuffs: list['Debuff'] = field(default_factory=list)
    dot_state: DotState = field(default_factory=DotState)

    def __post_init__(self) -> None:
        if self.elements_vulnerability is None:
            self.elements_vulnerability = Elements()
            self.elements_vulnerability.set_all(1.0)

        # Armor capped at 2700 with 90% reduction
        self.base_armor = min(self.base_armor, 2700)
        self.current_armor = self.base_armor

    def apply_armor_strip(self, amount: float):
        """
        Strip armor from the enemy.

        Args:
            amount: Amount of armor to remove
        """
        self.current_armor = max(0.0, self.current_armor - amount)

    def get_armor_damage_reduction(self) -> float:
        """
        Calculate damage reduction from armor.

        Returns:
            Damage multiplier (0 = no reduction, 0.5 = 50% reduction)
        """
        if self.current_armor <= 0:
            return 0.0

        # ref: https://wiki.warframe.com/w/Armor
        return 0.9 * math.sqrt(self.current_armor / 2700.0)

    def add_debuff(self, debuff: 'Debuff', current_time: float) -> None:
        """Add a debuff to the enemy"""
        # Check if debuff of same type already exists
        existing = self.get_debuff_by_type(debuff.debuff_type)
        if existing:
            # TODO: Implement stack
            if debuff.debuff_refresh_type == DebuffRefreshType.REFRESH:
                existing.refresh(current_time)
        else:
            self.active_debuffs.append(debuff)

    def remove_debuff(self, debuff: 'Debuff'):
        """Remove a debuff from the enemy"""
        if debuff in self.active_debuffs:
            self.active_debuffs.remove(debuff)

    def get_debuff_by_type(self, debuff_type: str) -> Optional['Debuff']:
        """Get first debuff of specified type"""
        for debuff in self.active_debuffs:
            if debuff.debuff_type == debuff_type:
                return debuff
        return None

class DebuffType(StrEnum):
    """Types of debuffs that can be applied to enemies"""
    HEAT_ARMOR_STRIP = auto()


class DebuffRefreshType(StrEnum):
    REFRESH = auto()
    STACK = auto()


@dataclass
class Debuff:
    """
    Base class for debuffs.
    Each debuff tracks its own state and timing.
    """
    debuff_type: DebuffType
    debuff_refresh_type: DebuffRefreshType
    tick_interval: float  # How often the debuff ticks
    last_tick_time: float = 0.0
    expiration_time: float = 0.0
    duration: float = 6.0  # TODO: implement status duration

    def should_expire(self, enemy_stat: 'EnemyStat', current_time: float) -> bool:
        return current_time >= self.expiration_time

    def tick(self, enemy_stat: 'EnemyStat', current_time: float):
        """
        Apply the debuff's effect.
        Override this in subclasses.
        """
        pass

    def refresh(self, current_time: float):
        self.expiration_time = current_time + self.duration


@dataclass
class HeatArmorStripDebuff(Debuff):
    """
    Heat debuff that strips armor while heat DOTs are active.
    Automatically tied to active_dots["heat"] - strips while DOTs exist, recovers when gone.

    Armor Strip: 15%, 30%, 40%, 50% every 0.5s (4 stages total)
    Armor Recovery: 50%, 40%, 30%, 15%, 0% every 1.5s (5 stages total)
    """
    strip_stage = 0
    last_recovery_tick: float = -1.0

    # Constants
    STRIP_PERCENTAGES: tuple = field(default=(0.00, 0.15, 0.30, 0.40, 0.50), init=False)
    STRIP_INTERVAL: float = field(default=0.5, init=False)
    RECOVERY_INTERVAL: float = field(default=1.5, init=False)

    def __init__(self):
        super().__init__(
            debuff_type=DebuffType.HEAT_ARMOR_STRIP,
            debuff_refresh_type=DebuffRefreshType.REFRESH,
            tick_interval=0.5,
        )

    def should_expire(self, enemy_stat: 'EnemyStat', current_time: float) -> bool:
        """Expire only after full recovery and no heat DOTs"""
        return enemy_stat.dot_state.active_dots.get(DotType.HEAT, 0) == 0 and self.strip_stage == 0

    def tick(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor strip or recovery based on heat DOT state"""
        if len(enemy_stat.dot_state.active_dots.get(DotType.HEAT, [])) > 0:
            # Heat DOTs active - apply armor strip
            self._apply_strip(enemy_stat, current_time)
        else:
            # No heat DOTs - apply recovery
            self._apply_recovery(enemy_stat, current_time)

    def _apply_strip(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor strip effect"""

        if self.strip_stage >= len(self.STRIP_PERCENTAGES) - 1:
            return

        time_since_last_tick = current_time - self.last_tick_time
        if time_since_last_tick < self.STRIP_INTERVAL:
            return

        self.strip_stage += 1
        strip_percentage = self.STRIP_PERCENTAGES[self.strip_stage]
        enemy_stat.current_armor = enemy_stat.base_armor * (1.0 - strip_percentage)
        print(f"Applying heat strip, time = {current_time}, last tick = {self.last_tick_time}, strip stage = {self.strip_stage}")
        print(f"Current armor = {enemy_stat.current_armor}")
        self.last_tick_time = current_time

    def _apply_recovery(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor recovery effect"""
        if self.strip_stage == 0:
            return

        if self.last_recovery_tick < 0:
            self.last_recovery_tick = current_time
            return

        time_since_last_recovery = current_time - self.last_tick_time
        if time_since_last_recovery < self.RECOVERY_INTERVAL:
            return

        self.strip_stage -= 1
        strip_percentage = self.STRIP_PERCENTAGES[self.strip_stage]
        enemy_stat.current_armor = enemy_stat.base_armor * (1.0 - strip_percentage)
        print(f"Applying armor recovery, time = {current_time}, last tick = {self.last_tick_time}, strip stage = {self.strip_stage}")

        self.last_tick_time = current_time
        print(f"Current armor = {enemy_stat.current_armor}")

class DebuffManager:
    """Manages all debuffs on enemies"""

    @staticmethod
    def update_debuffs(enemy_stat: 'EnemyStat', current_time: float):
        """
        Update all debuffs on an enemy.
        Apply ticks and handle expirations.
        """
        debuffs_to_remove = []

        for debuff in enemy_stat.active_debuffs:
            # Check expiration first
            if debuff.should_expire(enemy_stat, current_time):
                debuffs_to_remove.append(debuff)
                continue

            # Apply tick effects
            debuff.tick(enemy_stat, current_time)

        # Remove expired debuffs
        for debuff in debuffs_to_remove:
            enemy_stat.remove_debuff(debuff)


def create_heat_armor_strip_debuff() -> HeatArmorStripDebuff:
    """
    Create heat armor strip debuff.
    This is automatically managed based on active_dots["heat"].
    """
    return HeatArmorStripDebuff()

from collections.abc import Callable
from dataclasses import dataclass, field, fields
from enum import StrEnum, auto
from typing import TypeVar, Generic
import copy

Self = TypeVar('Self', bound='_SupportsAdd')


@dataclass
class _SupportsAdd:
    """Base class for dataclasses that support addition operator."""

    def _combine_fields(self, other, inplace: bool = False):
        """
        Helper to combine fields from self and other.

        Args:
            other: Another _SupportsAdd instance
            inplace: If True, modify self in-place; if False, return dict of combined values

        Returns:
            Dict of combined values if inplace=False, None if inplace=True
        """
        combined_values = {} if not inplace else None

        for f in fields(self):
            self_value = getattr(self, f.name)

            if hasattr(other, f.name):
                other_value = getattr(other, f.name)
                new_value = self._combine_field(f.name, self_value, other_value, inplace)

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

    def __add__(self: Self, other: Self) -> Self:
        """
        Add two dataclass instances together, combining all field values.

        For each field in self, attempts to add values from other.
        Fields missing in other are copied from self using copy.copy().
        Subclasses can customize behavior through _combine_field.

        Args:
            other: Another instance compatible for addition

        Returns:
            New instance of the same type as self with combined values
        """
        if not isinstance(other, _SupportsAdd):
            return NotImplemented

        combined_values = self._combine_fields(other, inplace=False)
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
        if not isinstance(other, _SupportsAdd):
            return NotImplemented

        self._combine_fields(other, inplace=True)
        return self

    def _combine_field(self, name: str, self_value, other_value, inplace: bool = False):
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

        # Try direct addition (works for numbers, strings, lists, _SupportsAdd objects, etc.)
        try:
            if inplace and hasattr(self_value, '__iadd__'):
                # Use in-place addition if available
                self_value += other_value
                return self_value
            else:
                # Use regular addition
                return self_value + other_value
        except (TypeError, AttributeError):
            # Addition not supported, use self's value
            return copy.copy(self_value)


@dataclass
class Elements(_SupportsAdd):
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


@dataclass
class _GeneralStat(_SupportsAdd):
    damage: float = 0
    attack_speed: float = 0
    multishot: float = 0
    critical_chance: float = 0
    critical_damage: float = 0
    status_chance: float = 0
    status_duration: float = 0
    elements: Elements = field(default_factory=Elements)
    prejudice: dict[str, float] = field(default_factory=dict)


@dataclass
class WeaponStat(_GeneralStat):
    damage: float = 1
    attack_speed: float = 1
    multishot: float = 1
    critical_damage: float = 1
    status_duration: float = 1

    def __post_init__(self):
        # Set default elements to puncture=1 if not provided
        if self.elements.total() == 0:
            self.elements = Elements(puncture=1)


@dataclass
class StaticBuff(_GeneralStat):
    """Buffs from mods."""
    pass


class EnemyFaction(StrEnum):
    NONE = auto()
    GRINEER = auto()
    CORPUS = auto()


class EnemyType(StrEnum):
    NONE = auto()
    TRIDOLON = auto()


@dataclass
class EnemyStat:
    faction: EnemyFaction = field(default=EnemyFaction.NONE)
    type: EnemyType = field(default=EnemyType.NONE)
    elements_vulnerability: Elements | None = None

    def __post_init__(self) -> None:
        if self.elements_vulnerability is None:
            self.elements_vulnerability = Elements()
            self.elements_vulnerability.set_all(1.0)


@dataclass
class InGameBuff(_GeneralStat):
    """In-game buffs and combat state modifiers."""

    galvanized_shot: int = 0
    galvanized_aptitude: int = 0
    final_additive_cd: float = 0  # Includes pet crit multiplier bonus
    attack_speed: float = 0.0  # Includes pet attack speed bonus
    num_debuffs: int = 0  # Number of debuffs on enemy
    elements: Elements = field(default_factory=Elements)
    final_multiplier: float = 1.0
    # special mod effects such as galvanized and blood rush
    callbacks: list[Callable[["InGameBuff"], None]] = field(default_factory=list)

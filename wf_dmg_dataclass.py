from dataclasses import dataclass, field, fields
from enum import StrEnum, auto


@dataclass
class Elements:
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

    def __add__(self, other: "Elements") -> "Elements":
        """
        Add two Elements objects together, combining all element values.

        Args:
            other: Another Elements object to add

        Returns:
            New Elements object with combined values
        """
        if not isinstance(other, Elements):
            return NotImplemented

        # Create dict with combined values for all fields
        combined_values = {}
        for f in fields(self):
            combined_values[f.name] = getattr(self, f.name) + getattr(other, f.name)

        return Elements(**combined_values)

    def __iadd__(self, other: "Elements") -> "Elements":
        """
        In-place addition of another Elements object.

        Args:
            other: Another Elements object to add

        Returns:
            Self with updated values
        """
        if not isinstance(other, Elements):
            return NotImplemented

        # Add values from other to self for all fields
        for f in fields(self):
            current_value = getattr(self, f.name)
            other_value = getattr(other, f.name)
            setattr(self, f.name, current_value + other_value)

        return self


class _GeneralStat:
    damage: float
    attack_speed: float
    multishot: float
    critical_chance: float
    critical_damage: float
    status_chance: float
    status_duration: float
    elements: Elements
    prejudice: dict[str, float]


class WeaponStat(_GeneralStat):
    def __init__(self) -> None:
        super().__init__()
        self.damage = 1
        self.attack_speed = 1
        self.multishot = 1
        self.critical_chance = 0
        self.critical_damage = 1
        self.status_chance = 0
        self.status_duration = 1
        self.elements = Elements(puncture=1)
        self.prejudice = {}


class StaticBuff(_GeneralStat):
    # buff from mods
    def __init__(self) -> None:
        super().__init__()


class EnemyType(StrEnum):
    NONE = auto()
    GRINEER = auto()
    CORPUS = auto()
    TRIDOLON = auto()


class EnemyStat:
    faction: EnemyType = EnemyType.GRINEER


@dataclass
class InGameBuff(_GeneralStat):
    """In-game buffs and combat state modifiers."""

    galvanized_shot: int = 0
    galvanized_aptitude: int = 0
    final_additive_cd: float = 0  # Includes pet crit multiplier bonus
    attack_speed: float = 0.0  # Includes pet attack speed bonus
    num_debuffs: int = 0  # Number of debuffs on enemy
    elements: Elements = field(default_factory=Elements)

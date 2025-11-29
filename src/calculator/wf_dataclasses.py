import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field, fields
from enum import StrEnum, auto, Enum
from typing import Any, TypeVar, Generic
import copy

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

class DotType(Enum):
    """Types of DOT effects in Warframe."""
    HEAT = "heat"
    TOXIN = "toxin"
    SLASH = "slash"
    ELECTRICITY = "electricity"
    GAS = "gas"
    BLEED = "bleed"


class DotBehavior(Enum):
    """DOT stacking and refresh behaviors."""
    REFRESH_ALL = "refresh_all"  # Heat: refreshes all existing stacks
    INDEPENDENT = "independent"  # Toxin: independent timers per stack

@dataclass
class DotInstance:
    """Represents a single DOT stack instance."""
    dot_type: DotType
    damage_per_tick: float
    remaining_duration: float
    tick_rate: float = 1.0  # Ticks per second
    total_duration: float = 6.0  # Default 6 seconds

    def tick(self, delta_time: float) -> float:
        """
        Process one tick of DOT damage.

        Args:
            delta_time: Time elapsed since last tick

        Returns:
            Damage dealt this tick
        """
        if self.remaining_duration <= 0:
            return 0.0

        self.remaining_duration -= delta_time

        return self.damage_per_tick * delta_time * self.tick_rate

    def is_active(self) -> bool:
        """Check if this DOT instance is still active."""
        return self.remaining_duration > 0


@dataclass
class DotState:
    """Manages all active DOT effects on a target."""
    active_dots: dict[DotType, list[DotInstance]] = field(default_factory=dict)

    def add_dot(self, dot_instance: DotInstance, behavior: DotBehavior):
        """
        Add a new DOT instance with specific behavior.

        Args:
            dot_instance: The DOT to add
            behavior: How this DOT should stack/refresh
        """
        dot_type = dot_instance.dot_type

        if dot_type not in self.active_dots:
            self.active_dots[dot_type] = []

        if behavior == DotBehavior.REFRESH_ALL:
            # Heat behavior: refresh all existing stacks
            for existing_dot in self.active_dots[dot_type]:
                existing_dot.remaining_duration = dot_instance.total_duration
            self.active_dots[dot_type].append(dot_instance)

        elif behavior == DotBehavior.INDEPENDENT:
            # Toxin behavior: independent timers
            self.active_dots[dot_type].append(dot_instance)

    def tick_all(self, delta_time: float) -> dict[DotType, float]:
        """
        Process all active DOTs for one tick.

        Args:
            delta_time: Time elapsed since last tick

        Returns:
            Dictionary of damage dealt by each DOT type
        """
        damage_dealt = {}

        for dot_type, instances in list(self.active_dots.items()):
            total_damage = 0.0

            # Tick all instances and remove expired ones
            active_instances = []
            for instance in instances:
                damage = instance.tick(delta_time)
                total_damage += damage

                if instance.is_active():
                    active_instances.append(instance)

            # Update or remove the dot type
            if active_instances:
                self.active_dots[dot_type] = active_instances
                damage_dealt[dot_type] = total_damage
            else:
                del self.active_dots[dot_type]

        return damage_dealt

    def get_active_stacks(self, dot_type: DotType) -> int:
        """Get number of active stacks for a DOT type."""
        return len(self.active_dots.get(dot_type, []))

    def clear_all(self):
        """Remove all active DOTs."""
        self.active_dots.clear()


@dataclass
class DotCallback:
    """
    Callback for DOT-specific behavior modifications.
    Similar to mod callbacks but for DOT mechanics.
    """
    func: Callable[[DotInstance, Any], DotInstance]
    dot_type: DotType
    description: str = ""

    def __call__(self, dot_instance: DotInstance, *args: Any, **kwargs: Any) -> DotInstance:
        """Execute the callback."""
        return self.func(dot_instance, *args, **kwargs)


@dataclass
class DotConfig:
    """Configuration for a specific DOT type."""
    dot_type: DotType
    behavior: DotBehavior
    base_duration: float = 6.0
    tick_rate: float = 1.0
    damage_multiplier: float = 1.0
    callbacks: list[DotCallback] = field(default_factory=list)

    def create_instance(self, base_damage: float, crit_chance: float = 0.0, crit_damage: float = 1.0) -> DotInstance:
        """
        Create a DOT instance from this configuration.

        Args:
            base_damage: Base damage for this DOT
            crit_chance: Critical chance for this DOT
            crit_damage: Critical damage for this DOT

        Returns:
            Configured DOT instance
        """
        damage_per_tick = base_damage * self.damage_multiplier

        if random.random() < crit_chance:
            # Critical hit!
            damage_per_tick *= crit_damage

        instance = DotInstance(
            dot_type=self.dot_type,
            damage_per_tick=damage_per_tick,
            remaining_duration=self.base_duration,
            tick_rate=self.tick_rate,
            total_duration=self.base_duration,
        )

        # Apply callbacks to modify the instance
        for callback in self.callbacks:
            instance = callback(instance)

        return instance

@dataclass
class EnemyStat:
    faction: EnemyFaction = field(default=EnemyFaction.NONE)
    type: EnemyType = field(default=EnemyType.NONE)
    elements_vulnerability: Elements | None = None
    base_armor: float = 0.0
    current_armor: float = 0.0

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
            Damage multiplier (1.0 = no reduction, 0.5 = 50% reduction)
        """
        if self.current_armor <= 0:
            return 1.0

        # ref: https://wiki.warframe.com/w/Armor
        return 0.9 * math.sqrt(self.current_armor / 2700.0)
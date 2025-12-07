import random
from dataclasses import dataclass, field
from enum import Enum


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
class DotConfig:
    """Configuration for a specific DOT type."""
    dot_type: DotType
    behavior: DotBehavior
    base_duration: float = 6.0
    tick_rate: float = 1.0
    damage_multiplier: float = 1.0

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

        return instance

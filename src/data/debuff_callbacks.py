from enum import StrEnum, auto
from typing import Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from src.calculator.wf_dataclasses import EnemyStat


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
    duration: float = 6.0 # TODO: implement status duration
    stage: int = 0

    def should_tick(self, current_time: float) -> bool:
        """Check if enough time has passed for the next tick"""
        time_since_last_tick = current_time - self.last_tick_time
        return time_since_last_tick >= self.tick_interval

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
    recovery_stage: int = 0
    last_recovery_time: float = 0.0

    # Constants
    STRIP_PERCENTAGES: tuple = field(default=(0.15, 0.30, 0.40, 0.50), init=False)
    RECOVERY_PERCENTAGES: tuple = field(default=(0.50, 0.40, 0.30, 0.15, 0.00), init=False)
    STRIP_INTERVAL: float = field(default=0.5, init=False)
    RECOVERY_INTERVAL: float = field(default=1.5, init=False)

    def __init__(self):
        super().__init__(
            debuff_type=DebuffType.HEAT_ARMOR_STRIP,
            debuff_refresh_type=DebuffRefreshType.REFRESH,
            tick_interval=0.5,
        )

    def _has_heat_dots(self, enemy_stat: 'EnemyStat') -> bool:
        """Check if enemy has any active heat DOTs"""
        return len(enemy_stat.active_debuffs.get("heat", [])) > 0

    def should_expire(self, enemy_stat: 'EnemyStat', current_time: float) -> bool:
        """Expire only after full recovery and no heat DOTs"""
        return (not self._has_heat_dots(enemy_stat) and
                self.recovery_stage >= len(self.RECOVERY_PERCENTAGES))

    def tick(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor strip or recovery based on heat DOT state"""
        if self._has_heat_dots(enemy_stat):
            # Heat DOTs active - apply armor strip
            self._apply_strip(enemy_stat, current_time)
            print(f"Applying armor strip")
        else:
            # No heat DOTs - apply recovery
            self._apply_recovery(enemy_stat, current_time)
            print(f"Applying armor recover")

    def _apply_strip(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor strip effect"""
        if self.stage >= len(self.STRIP_PERCENTAGES):
            return

        time_since_last_tick = current_time - self.last_tick_time
        if time_since_last_tick < self.STRIP_INTERVAL:
            return

        strip_percentage = self.STRIP_PERCENTAGES[self.stage]
        enemy_stat.current_armor *= (1.0 - strip_percentage)
        self.stage += 1
        self.last_tick_time = current_time

        # Reset recovery when stripping
        self.recovery_stage = 0
        self.last_recovery_time = current_time

    def _apply_recovery(self, enemy_stat: 'EnemyStat', current_time: float):
        """Apply armor recovery effect"""
        if self.recovery_stage >= len(self.RECOVERY_PERCENTAGES):
            return

        if self.stage == 0:  # Nothing to recover
            return

        time_since_last_recovery = current_time - self.last_recovery_time
        if time_since_last_recovery < self.RECOVERY_INTERVAL:
            return

        recovery_percentage = self.RECOVERY_PERCENTAGES[self.recovery_stage]
        if recovery_percentage > 0:
            max_recovery = enemy_stat.base_armor - enemy_stat.current_armor
            enemy_stat.current_armor += max_recovery * recovery_percentage

        self.recovery_stage += 1
        self.last_recovery_time = current_time

        # Clamp to base armor
        if enemy_stat.current_armor >= enemy_stat.base_armor:
            enemy_stat.current_armor = enemy_stat.base_armor
            self.stage = 0  # Reset strip stage after full recovery


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
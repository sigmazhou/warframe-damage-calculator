from dataclasses import fields
from functools import reduce
from src.calculator.wf_dataclasses import (
    WeaponStat,
    StaticBuff,
    InGameBuff,
    EnemyStat,
    EnemyFaction,
    EnemyType,
    Elements,
)
from src.data.mod_callbacks import CallbackType


class DamageCalculator:
    """
    Represents the damage calculation of one weapon in a given circumstance.

    This class encapsulates all damage calculations including base damage,
    critical hits, status effects, and various buffs.
    """

    def __init__(
        self,
        weapon_stat: WeaponStat,
        static_buff: StaticBuff,
        in_game_buff: InGameBuff,
        enemy_stat: EnemyStat,
        element_order: list[str] = None,
    ):
        """
        Initialize the damage calculator with weapon stats and modifiers.

        Args:
            weapon_stat: Base weapon statistics
            static_buff: Buffs from mods
            in_game_buff: In-game buffs like galvanized stacks, pet bonuses, debuff count, final multiplier
            enemy_stat: Enemy faction and characteristics
            element_order: List of base elements in order for combination (e.g., ["heat", "toxin"])
        """
        self.weapon_stat = weapon_stat
        self.static_buff = static_buff
        self.in_game_buff = in_game_buff
        self.enemy_stat = enemy_stat
        self.element_order = element_order or []
        self.final_buff = in_game_buff + static_buff

        # apply IGB callbacks
        for callback in self.final_buff.callbacks:
            if callback.type == CallbackType.IN_GAME_BUFF:
                callback(self.final_buff)

        if self.element_order:
            # Apply element combination directly to final_buff.elements
            self.final_buff.elements.combine_elements(self.element_order)

    def calc_elem(self) -> float:
        """
        Calculate total elemental damage multiplier.

        Applies faction bonuses for Tridolon (radiation and cold get 1.5x).

        Returns:
            Total elemental damage multiplier
        """
        # Combine all element sources using the Elements addition operator
        combined = self.weapon_stat.elements + self.final_buff.elements

        if self.enemy_stat.type == EnemyType.TRIDOLON:
            # Apply Tridolon type bonuses (radiation and cold get 1.5x)
            total = 0.0
            for f in fields(combined):
                value = getattr(combined, f.name)
                if f.name in ("radiation", "cold"):
                    total += value * 1.5
                else:
                    total += value
            return total
        else:
            # No special type bonuses
            return combined.total()

    def calc_single_hit(self) -> float:
        """
        Calculate damage per single hit/shot.

        Returns:
            Damage value for a single hit
        """
        per_shot = (
            self.weapon_stat.damage
            * self.calc_elem()
            * self._get_base()
            * self._get_crit()
            * self._get_prejudice()
            * self._get_ms()
            * self.in_game_buff.final_multiplier
        )
        return per_shot

    def calc_direct(self) -> float:
        """
        Calculate direct damage per second.

        Returns:
            DPS from direct hits
        """
        muls = []

        per_shot = self.calc_single_hit()
        shot_per_sec = self._get_as()
        muls += [per_shot, shot_per_sec]

        if self.enemy_stat.type == EnemyType.TRIDOLON:
            muls.append(self._get_eidolon_non_crit_penalty())

        return reduce(lambda x, y: x * y, muls, 1)

    def calc_dots(self) -> dict[str, float]:
        """
        Calculate damage over time (DOT) for all status effects.

        Returns:
            Dictionary of status effect names and their DPS
        """
        dots = {
            "heat": self.calc_dot("heat"),
            "toxin": self.calc_dot("toxin"),
            "slash": self.calc_dot("slash"),
            "electricity": self.calc_dot("electricity"),
        }
        return {k: v for k, v in dots.items() if v > 0}

    def calc_dot(self, element: str) -> float:
        """
        Calculate fire damage over time (heat proc stacking).

        Returns:
            DPS from fire status effect
        """
        #TODO: consider % of element in all elements
        muls = [self.weapon_stat.damage]

        # First layer - base fire damage
        base_elem_buff = getattr(self.final_buff.elements, element)
        muls += [base_elem_buff * self._get_prejudice()]

        # Following layers
        per_layer = (
            0.5
            * self._get_base()
            * self._get_crit()
            * self._get_prejudice()
            * self.in_game_buff.final_multiplier
        )
        layers_per_sec = self._get_sc() * self._get_as() * self._get_ms()
        muls += [per_layer, layers_per_sec]

        return reduce(lambda x, y: x * y, muls, 1)

    def _get_eidolon_non_crit_penalty(self) -> float:
        """
        Calculate the penalty for non-critical hits against Eidolons.

        Eidolons take 50% damage from non-crits, so we adjust the average damage.

        Returns:
            Damage multiplier accounting for eidolon non-crit penalty
        """
        cc = self.weapon_stat.critical_chance * (1 + self.final_buff.critical_chance)
        return 1 - (1 - cc) * 0.5 if cc < 1 else 1

    def _get_base(self) -> float:
        """
        Calculate total base damage multiplier.

        Includes base damage buff from mods and galvanized shot stacks.

        Returns:
            Base damage multiplier
        """
        return 1 + self.final_buff.damage

    def _get_crit(self) -> float:
        """
        Calculate critical hit damage multiplier.

        Accounts for critical chance, critical damage, and in-game buffs (including pet bonuses).

        Returns:
            Average damage multiplier from critical hits
        """
        cc = self.weapon_stat.critical_chance * (1 + self.final_buff.critical_chance)
        cd = (
            self.weapon_stat.critical_damage * (1 + self.final_buff.critical_damage)
            + self.in_game_buff.final_additive_cd
        )

        return cc * (cd - 1) + 1

    def _get_prejudice(self) -> float:
        """
        Calculate faction damage multiplier from prejudice mods.

        Returns:
            Prejudice damage multiplier
        """
        total_prejudice = self.final_buff.prejudice.get(self.enemy_stat.faction.value, 0)
        return 1 + total_prejudice

    def _get_ms(self) -> float:
        """
        Calculate total multishot value.

        Includes base multishot, mods, and galvanized aptitude stacks.

        Returns:
            Total multishot multiplier
        """
        return self.weapon_stat.multishot * (
            1 + self.final_buff.multishot
        )

    def _get_as(self) -> float:
        """
        Calculate total attack speed (fire rate).

        Includes base attack speed, mods, and in-game buffs (including pet bonuses).

        Returns:
            Total attack speed multiplier
        """
        return self.weapon_stat.attack_speed * (1 + self.final_buff.attack_speed)

    def _get_sc(self) -> float:
        """
        Calculate total status chance.

        Returns:
            Total status chance (can exceed 1.0 for multiple procs)
        """
        return self.weapon_stat.status_chance * (1 + self.final_buff.status_chance)


if __name__ == "__main__":
    """
    Test cases for weapon builds

    furis
    base_crit_chance=0.26
    base_crit_damage=3.4
    base_status_chance=0.52

    dual tox
    base_crit_chance=0.31
    base_crit_damage=4.2
    base_status_chance=0.43
    """

    # Example 1: Dual Toxocyst build against Eidolon
    weapon = WeaponStat()
    weapon.damage = 1
    weapon.attack_speed = 1
    weapon.multishot = 1
    weapon.critical_chance = 0.31
    weapon.critical_damage = 4.2
    weapon.status_chance = 0.43
    weapon.elements = Elements(impact=1)  # Base physical damage

    # pet bonus
    # add_60_atk_speed = 1
    # add_120_crit_multiplier = 1

    # mods
    mods = StaticBuff()
    mods.damage = 2.2 + 3.6
    mods.attack_speed = 0 + 0.6 + 1.5
    mods.multishot = 0.6 + 1 + 2.1
    mods.critical_chance = 1.87 + 2.4
    mods.critical_damage = 1.1 + 2.4
    mods.status_chance = 0.8
    mods.elements = Elements(corrosive=0, radiation=3.3, toxin=1)
    mods.prejudice = {}

    # final_multiplier = 1  # +0.9

    # stats
    # num_debuffs = 0
    # galv_base_layers = 0
    # galv_ms_layers = 0

    buffs = InGameBuff()
    buffs.galvanized_shot = 0
    buffs.galvanized_diffusion = 0
    buffs.final_additive_cd = 1.2  # Pet crit multiplier bonus
    buffs.attack_speed = 0.6  # Pet attack speed bonus
    buffs.num_debuffs = 0

    enemy = EnemyStat()
    enemy.type = EnemyType.TRIDOLON

    calculator = DamageCalculator(
        weapon_stat=weapon,
        static_buff=mods,
        in_game_buff=buffs,
        enemy_stat=enemy,
    )

    print(f"Dual Toxocyst Direct DPS: {calculator.calc_direct()}")

    """
    furis fire build

    # mods
    mods.elements = Elements(heat=1.65+0.6)
    mods.damage = 2.2  # -0.15 or +4.8
    mods.status_chance = 0.6+0.8
    mods.critical_chance = 2.68+2.4
    mods.critical_damage = 1.468+2.4
    mods.attack_speed = 0+0.6
    mods.multishot = 1.1+0.6
    mods.prejudice = {"faction": 0.55}

    # in-game buffs
    buffs.num_debuffs = 5
    buffs.galvanized_shot = 3
    buffs.galvanized_diffusion = 4

    # final multiplier
    final_multiplier = 1  # +0.9
    """

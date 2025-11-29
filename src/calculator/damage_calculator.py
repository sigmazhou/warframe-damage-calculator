from collections import defaultdict
import random
from dataclasses import fields
from functools import reduce

from src.calculator.dot_config import DOT_CONFIG_MAP
from src.calculator.wf_dataclasses import (
    WeaponStat,
    StaticBuff,
    InGameBuff,
    EnemyStat,
    EnemyFaction,
    EnemyType,
    Elements,
    DotState,
    DotConfig,
    DotType,
    DotBehavior,
)
from src.data.mod_callbacks import CallbackType

SIM_V2 = True


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
        self.enemy_stat: EnemyStat = enemy_stat
        self.element_order = element_order or []
        self.final_buff: InGameBuff = in_game_buff + static_buff

        # apply IGB callbacks
        for callback in self.final_buff.callbacks:
            if callback.type == CallbackType.IN_GAME_BUFF:
                callback(self.final_buff)

        self.combined_elements: Elements = (
            self.final_buff.elements + weapon_stat.elements
        )

        if self.element_order:
            # Apply element combination directly to final_buff.elements
            self.combined_elements.combine_elements(self.element_order)

    def calc_elem(self) -> float:
        """
        Calculate total elemental damage multiplier.

        Applies faction bonuses for Tridolon (radiation and cold get 1.5x).

        Returns:
            Total elemental damage multiplier
        """
        # Use combined_elements which includes weapon elements after combination
        return self.combined_elements.total_with_vulnerability(
            self.enemy_stat.elements_vulnerability
        )

    def calc_single_hit_without_elements(self) -> float:
        """
        Calculate damage per single hit.

        Returns:
            Damage value for a single hit
        """
        per_hit = (
            self.weapon_stat.damage
            * self._get_base()
            * self._get_crit()
            * self._get_faction()
            * self.in_game_buff.final_multiplier
        )
        return per_hit

    def calc_single_hit(self) -> float:
        return self.calc_single_hit_without_elements() * self.calc_elem()

    def calc_direct_dps(self) -> float:
        """
        Calculate direct damage per second.

        Returns:
            DPS from direct hits
        """
        muls = []

        per_hit = self.calc_single_hit()
        hit_per_sec = self._get_as() * self._get_ms()
        muls += [per_hit, hit_per_sec]

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
        muls = [0.5, self.calc_single_hit_without_elements()]

        # Uncombined element for (1+mod+buff)
        elem_mod_and_buff = self.final_buff.elements.get_element(element) + 1
        muls += [elem_mod_and_buff, self._get_faction()]

        layers_per_sec = self._get_sc(element) * self._get_as() * self._get_ms()
        muls += [layers_per_sec]

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

    def _get_cc(self) -> float:
        return self.weapon_stat.critical_chance * (1 + self.final_buff.critical_chance)

    def _get_cd(self) -> float:
        return (
            self.weapon_stat.critical_damage * (1 + self.final_buff.critical_damage)
            + self.in_game_buff.final_additive_cd
        )

    def _get_crit(self) -> float:
        """
        Calculate critical hit damage multiplier.

        Accounts for critical chance, critical damage, and in-game buffs (including pet bonuses).

        Returns:
            Average damage multiplier from critical hits
        """
        cc = self._get_cc()
        cd = self._get_cd()

        return cc * (cd - 1) + 1

    def _get_faction(self) -> float:
        """
        Calculate faction damage multiplier from faction mods.

        Returns:
            faction damage multiplier
        """
        total_faction = self.final_buff.faction.get(self.enemy_stat.faction.value, 0)
        return 1 + total_faction

    def _get_ms(self) -> float:
        """
        Calculate total multishot value.

        Includes base multishot, mods, and galvanized aptitude stacks.

        Returns:
            Total multishot multiplier
        """
        return self.weapon_stat.multishot * (1 + self.final_buff.multishot)

    def _get_as(self) -> float:
        """
        Calculate total attack speed (fire rate).

        Includes base attack speed, mods, and in-game buffs (including pet bonuses).

        Returns:
            Total attack speed multiplier
        """
        return self.weapon_stat.attack_speed * (1 + self.final_buff.attack_speed)

    def _get_sc(self, element: str | None = None) -> float:
        """
        Calculate total status chance.

        Returns:
            Total status chance (can exceed 1.0 for multiple procs)
        """
        sc = self.weapon_stat.status_chance * (1 + self.final_buff.status_chance)
        if not element:
            return sc
        return (
            sc
            * self.combined_elements.get_element(element)
            / self.combined_elements.total()
        )

    def _simulate_crit(
        self, random_seed: int | None = None, return_crit_level: bool = False
    ) -> float:
        """
        Simulate a critical hit, returns critical damage multiplier.
        """
        if random_seed is not None:
            random.seed(random_seed)
        crit_level = int(self._get_cc()) + (
            1 if random.random() < (self._get_cc() % 1) else 0
        )
        if return_crit_level:
            return crit_level * (self._get_cd() - 1) + 1, crit_level
        return crit_level * (self._get_cd() - 1) + 1

    def _simulate_ms(self, random_seed: int | None = None) -> int:
        """
        Simulate a multishot, returns number of pellets.
        """
        if random_seed is not None:
            random.seed(random_seed)
        ms = int(self._get_ms()) + (1 if random.random() < (self._get_ms() % 1) else 0)
        return ms

    def _simulate_single_hit(self, random_seed: int | None = None) -> float:
        """
        Simulate a single hit. Applies debuffs and returns total direct damage.
        """
        if random_seed is not None:
            random.seed(random_seed)

        proc_counts = defaultdict(int)
        fixed_base_damage = (
            self.weapon_stat.damage
            * self._get_base()
            * self._get_faction()
            * self.in_game_buff.final_multiplier
        )
        total_base_damage = 0.0
        # don't consider elements here
        num_pellets = self._simulate_ms()
        for _ in range(num_pellets):
            base_damage = fixed_base_damage * self._simulate_crit()
            procs = self._roll_status_procs()
            for proc in procs:
                proc_counts[proc] += 1
                self.apply_status_proc(proc, base_damage)
            total_base_damage += base_damage

        # apply elements to total base damage
        total_base_damage *= self.combined_elements.total_with_vulnerability(
            self.enemy_stat.elements_vulnerability
        )
        return total_base_damage, proc_counts

    def apply_status_proc(self, element: str, base_damage: float | None = None):
        """
        Apply a status proc and create DOT instance.
        Currently only supports dots, will support other status effects in the future.

        Args:
            element: Element type that procced
        """
        if element not in DOT_CONFIG_MAP:
            return

        config = DOT_CONFIG_MAP[element]

        # Calculate base damage for this DOT
        if base_damage is None:
            # keep for V1 compatibility, remove when fully tested
            base_damage = (
                self.weapon_stat.damage
                * self._get_base()
                * self._get_faction()
                * self.in_game_buff.final_multiplier
            )
        element_multiplier = self.final_buff.elements.get_element(element) + 1
        proc_damage = base_damage * element_multiplier * self._get_faction()

        # Create DOT instance
        if SIM_V2:
            dot_instance = config.create_instance(proc_damage)
        else:
            dot_instance = config.create_instance(
                base_damage, self._get_cc(), self._get_cd()
            )
        self.enemy_stat.dot_state.add_dot(dot_instance, config.behavior)

    def _roll_status_procs(self, status_chance: float | None = None) -> list[str]:
        """
        Roll for status procs based on status chance and element weights.

        Args:
            status_chance: Total status chance (can be > 1.0)

        Returns:
            List of elements that procced
        """
        if not status_chance:
            status_chance = self._get_sc()
        procs = []

        # Calculate number of procs
        num_procs = int(status_chance)
        if random.random() < (status_chance - num_procs):
            num_procs += 1

        if num_procs == 0:
            return procs

        # Get element weights
        weights = self.combined_elements.to_dict()
        if not weights:
            return procs

        # Use element damages as weights
        total_damage = sum(weights.values())

        # Roll for each proc
        for _ in range(num_procs):
            rand = random.random() * total_damage
            cumulative = 0.0

            for element, damage in weights.items():
                cumulative += damage
                if rand <= cumulative:
                    procs.append(element)
                    break

        return procs

    def _reset_simulation(self):
        """
        Reset the simulation state.
        """
        self.enemy_stat.dot_state = DotState()

    def simulate_combat(
        self, duration: float, time_step: float = 1, verbose: bool = False
    ) -> dict:
        """
        Simulate combat over a period of time with actual DOT tracking.

        Args:
            duration: Total simulation time in seconds
            time_step: Time between simulation steps
            verbose: Print detailed simulation logs

        Returns:
            Dictionary with comprehensive damage breakdown
        """

        # Reset DOT state
        self._reset_simulation()

        total_direct_damage = 0.0
        total_dot_damage = {dot_type: 0.0 for dot_type in DotType}
        proc_counts = defaultdict(int)

        time_elapsed = 0.0
        shot_timer = 0.0
        attack_speed = self._get_as()
        time_between_shots = 1.0 / attack_speed if attack_speed > 0 else float("inf")

        status_chance = self._get_sc()
        multishot = self._get_ms()

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"COMBAT SIMULATION")
            print(f"{'=' * 60}")
            print(f"Attack Speed: {attack_speed:.2f} shots/sec")
            print(f"Status Chance: {status_chance:.2f}")
            print(f"Multishot: {multishot:.2f}")
            print(f"Duration: {duration}s")
            print(f"{'=' * 60}\n")

        shots_fired = 0
        while time_elapsed < duration:
            # Fire weapon
            while shot_timer <= 0 and time_elapsed < duration:
                shots_fired += 1
                shot_timer += time_between_shots

                if SIM_V2:
                    direct_damage, proc_counts = self._simulate_single_hit()
                    total_direct_damage += direct_damage
                    for proc, count in proc_counts.items():
                        proc_counts[proc] += count
                    continue

                direct_damage = self.calc_single_hit()
                total_direct_damage += direct_damage

                # Determine number of pellets
                num_pellets = int(multishot)
                if random.random() < (multishot - num_pellets):
                    num_pellets += 1

                # Roll procs for each pellet
                for pellet in range(num_pellets):
                    procs = self._roll_status_procs(status_chance)

                    for element in procs:
                        proc_counts[element] = proc_counts.get(element, 0) + 1
                        if element in DOT_CONFIG_MAP:
                            self.apply_status_proc(element)

            # Tick DOTs
            dot_damages = self.enemy_stat.dot_state.tick_all(time_step)
            for dot_type, damage in dot_damages.items():
                total_dot_damage[dot_type] += damage

            # Advance time
            time_elapsed += time_step
            shot_timer -= time_step

        # Filter out zero DOT damage
        filtered_dot_damage = {k: v for k, v in total_dot_damage.items() if v > 0}

        total_dot = sum(filtered_dot_damage.values())
        total_damage = total_direct_damage + total_dot

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"SIMULATION COMPLETE")
            print(f"{'=' * 60}")
            print(f"Shots fired: {shots_fired}")
            print(f"\nProc counts:")
            for element, count in sorted(proc_counts.items()):
                print(f"  {element}: {count}")
            print(f"\nDamage breakdown:")
            print(f"  Direct damage: {total_direct_damage:.2f}")
            print(f"  DOT damage: {total_dot:.2f}")
            for dot_type, damage in filtered_dot_damage.items():
                print(f"    {dot_type.value}: {damage:.2f}")
            print(f"  Total: {total_damage:.2f}")
            print(f"\nDPS:")
            print(f"  Direct DPS: {total_direct_damage / duration:.2f}")
            print(f"  DOT DPS: {total_dot / duration:.2f}")
            print(f"  Total DPS: {total_damage / duration:.2f}")
            print(f"{'=' * 60}\n")

        return {
            "single_hit": self.calc_single_hit(),
            "direct_dps": total_direct_damage / duration,
            "theoretical_dot_dps": self.calc_dots(),
            "simulated_dot_dps": total_dot / duration,
            "total_dps": total_damage / duration,
            "total_direct_damage": total_direct_damage,
            "total_dot_damage": filtered_dot_damage,
            "active_dot_stacks": {
                dot_type.value: self.enemy_stat.dot_state.get_active_stacks(dot_type)
                for dot_type in DotType
                if self.enemy_stat.dot_state.get_active_stacks(dot_type) > 0
            },
            "proc_counts": proc_counts,
            "shots_fired": shots_fired,
            "duration": duration,
        }

    def simulate_combat_multiple(
        self,
        duration: float,
        num_simulations: int = 10,
        time_step: float = 1.0,
        verbose: bool = False,
    ) -> dict:
        """
        Run multiple combat simulations and return statistics (min, max, avg).

        Args:
            duration: Total simulation time in seconds
            num_simulations: Number of simulations to run
            time_step: Time between simulation steps
            verbose: Print detailed simulation logs

        Returns:
            Dictionary with min, max, and average statistics
        """
        direct_dps_results = []
        dot_dps_results = []
        total_dps_results = []

        for i in range(num_simulations):
            result = self.simulate_combat(
                duration=duration, time_step=time_step, verbose=True
            )

            direct_dps_results.append(result["direct_dps"])
            dot_dps_results.append(result["simulated_dot_dps"])
            total_dps_results.append(result["total_dps"])

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"MULTIPLE SIMULATIONS COMPLETE ({num_simulations} runs)")
            print(f"{'=' * 60}")
            print(
                f"Direct DPS - Min: {min(direct_dps_results):.2f}, Max: {max(direct_dps_results):.2f}, Avg: {sum(direct_dps_results) / len(direct_dps_results):.2f}"
            )
            print(
                f"DOT DPS - Min: {min(dot_dps_results):.2f}, Max: {max(dot_dps_results):.2f}, Avg: {sum(dot_dps_results) / len(dot_dps_results):.2f}"
            )
            print(
                f"Total DPS - Min: {min(total_dps_results):.2f}, Max: {max(total_dps_results):.2f}, Avg: {sum(total_dps_results) / len(total_dps_results):.2f}"
            )
            print(f"{'=' * 60}\n")

        return {
            "simulated_stats": {
                "direct_dps": {
                    "min": min(direct_dps_results),
                    "max": max(direct_dps_results),
                    "avg": sum(direct_dps_results) / len(direct_dps_results),
                },
                "dot_dps": {
                    "min": min(dot_dps_results),
                    "max": max(dot_dps_results),
                    "avg": sum(dot_dps_results) / len(dot_dps_results),
                },
                "total_dps": {
                    "min": min(total_dps_results),
                    "max": max(total_dps_results),
                    "avg": sum(total_dps_results) / len(total_dps_results),
                },
            },
            "num_simulations": num_simulations,
            "duration": duration,
        }


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
    mods.faction = {}

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

    print(f"Dual Toxocyst Direct DPS: {calculator.calc_direct_dps()}")

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
    mods.faction = {"faction": 0.55}

    # in-game buffs
    buffs.num_debuffs = 5
    buffs.galvanized_shot = 3
    buffs.galvanized_diffusion = 4

    # final multiplier
    final_multiplier = 1  # +0.9
    """

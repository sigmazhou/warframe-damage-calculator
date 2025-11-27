# weapon basis
from csv import get_dialect
from functools import reduce

"""
furis
base_crit_chance=0.26
base_crit_damage=3.4
base_status_chance=0.52

dual tox
base_crit_chance=0.31
base_crit_damage=4.2
base_status_chance=0.43
"""

base_dmg = 1
base_atk_spd = 1
base_crit_chance = 0.31
base_crit_damage = 4.2
base_status_chance = 0.43
base_multi_shot = 1

target_is_eidolon = 1

# pet bonus
add_60_atk_speed = 1
add_120_crit_multiplier = 1

# mods
elem_buff = {"physical": 1, "corrosive": 0, "radiation": 3.3, "toxin": 1}
base_dmg_buff = 2.2 + 3.6
sc_buff = 0.8
cc_buff = 1.87 +2.4
cd_buff = 1.1 + 2.4
as_buff = 0 + 0.6 + 1.5
ms_buff = 0.6 + 1 + 2.1
prejudice = 0

final_multiplier = 1  # +0.9

# stats
num_debuffs = 0
galv_base_layers = 0
galv_ms_layers = 0

"""
furis fire

# mods
elem_buff = {"fire":1.65+0.6}
base_dmg_buff = 2.2#-0.15#+4.8
sc_buff = 0.6+0.8
cc_buff = 2.68+2.4
cd_buff = 1.468+2.4
as_buff = 0+0.6
ms_buff = 1.1+0.6
prejudice = 0.55

final_multiplier = 1#+0.9

# stats
num_debuffs = 5
galv_base_layers = 3
galv_ms_layers = 4

"""


def calc_elem():
    total = 0
    if target_is_eidolon:
        for elem, value in elem_buff.items():
            if elem in ("radiation", "cold"):
                total += value * 1.5
            else:
                total += value
    else:
        for _, value in elem_buff.items():
            total += value
    return total


def calc_single_hit():
    elem_total = calc_elem()
    per_shot = (
        elem_total
        * _get_base()
        * _get_crit()
        * _get_prejudice()
        * _get_ms()
        * final_multiplier
    )

    return per_shot


def calc_direct():
    muls = []

    per_shot = calc_single_hit()
    shot_per_sec = _get_as()
    muls += [per_shot, shot_per_sec]
    if target_is_eidolon:
        muls.append(_get_eidolon_non_crit_penalty())

    return reduce(lambda x, y: x * y, muls, 1)


def calc_fire_dot():
    muls = []

    # first layer
    base_fire_buff = elem_buff.get("fire", 0) + 1
    muls += [base_fire_buff * _get_prejudice()]

    # following layers
    per_layer = (
        0.5
        * _get_base()
        * _get_crit()
        * _get_prejudice()
        * _get_ms()
        * final_multiplier
    )
    layers_per_sec = _get_sc() * 1 * _get_as()
    muls += [per_layer, layers_per_sec]

    return reduce(lambda x, y: x * y, muls, 1)


def _get_eidolon_non_crit_penalty():
    cc = base_crit_chance * (1 + cc_buff)
    return 1 - (1 - cc) * 0.5 if cc < 1 else 1


def _get_base():
    return 1 + base_dmg_buff + galv_base_layers * num_debuffs * 0.4


def _get_crit():
    cc = base_crit_chance * (1 + cc_buff)
    cd = base_crit_damage * (1 + cd_buff) + add_120_crit_multiplier * 1.2

    return cc * (cd - 1) + 1


def _get_prejudice():
    return 1 + prejudice


def _get_ms():
    return base_multi_shot * (1 + ms_buff + galv_ms_layers * 0.3)


def _get_as():
    return base_atk_spd * (1 + as_buff + add_60_atk_speed * 0.6)


def _get_sc():
    return base_status_chance * (1 + sc_buff)


def _get_debuff():
    return 1 + 3.25


if __name__ == "__main__":
    print(calc_direct())

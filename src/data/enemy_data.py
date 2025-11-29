import copy
from src.calculator.wf_dataclasses import Elements, EnemyFaction, EnemyStat, EnemyType
import logging

logger = logging.getLogger(__name__)

faction_element_vulnerability = {
    EnemyFaction.GRINEER: Elements(impact=1.5, corrosive=1.5),
    EnemyFaction.CORPUS: Elements(puncture=1.5, magnetic=1.5),
    EnemyFaction.INFESTED: Elements(slash=1.5, heat=1.5),
    EnemyFaction.OROKIN: Elements(puncture=1.5, viral=1.5, radiation=0.5),
    EnemyFaction.MURMUR: Elements(electricity=1.5, radiation=1.5, viral=0.5),
    EnemyFaction.SENTIENT: Elements(cold=1.5, radiation=1.5, corrosive=0.5),
}


def get_enemy_stat(
    faction: EnemyFaction | str, type: EnemyType | str = EnemyType.NONE
) -> EnemyStat:
    # Parse faction
    if isinstance(faction, str):
        try:
            faction = EnemyFaction(faction.lower())
        except ValueError:
            logger.warning(f"Invalid faction: {faction}")
            faction = EnemyFaction.NONE

    # Parse type
    if isinstance(type, str):
        try:
            type = EnemyType(type.lower())
        except ValueError:
            logger.warning(f"Invalid type: {type}")
            type = EnemyType.NONE

    elements_vulnerability = copy.copy(
        faction_element_vulnerability.get(faction, Elements())
    )
    elements_vulnerability.set_all_zeroes_to_value(1.0)
    enemy_stat = EnemyStat(
        faction=faction, type=type, elements_vulnerability=elements_vulnerability
    )
    return enemy_stat

from enum import StrEnum, auto

class _GeneralStat:
    damage: float
    attack_speed: float
    multishot: float
    critical_chance: float
    critical_damage: float
    status_chance: float
    status_duration: float
    elements: dict[str, float]
    prejudice: dict[str, float]


class WeaponStat(_GeneralStat):
    def __init__(self) -> None:
        super().__init__()
        self.damage = 1
        self.attack_speed = 1
        self.multishot = 1
        self.critical_chance = 0
        self.critical_chance = 1
        self.status_chance = 0
        self.status_duration = 1
        self.elements = {"punctuate": 1}
        self.prejudice = {}

class StaticBuff(_GeneralStat):
    # buff from mods
    def __init__(self) -> None:
        super().__init__()


class EnemyFaction(StrEnum):
    NONE = auto()
    GRINEER = auto()
    CORPUS = auto()
    TRIDOLON = auto()

class EnemyStat:
    faction: EnemyFaction = EnemyFaction.GRINEER

class InGameBuff(_GeneralStat):
    galvanized_shot: int = 0
    galvanized_aptitude: int = 0
    final_additive_cd: float = 0
    elements: dict[str, float] = {}
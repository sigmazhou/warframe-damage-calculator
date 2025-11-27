from collections.abc import Callable
from enum import StrEnum, auto
from typing import Any


class CallbackType(StrEnum):
    IN_GAME_BUFF = auto()


class CallBack:
    func: Callable[[Any], None]
    type: CallbackType

    def __init__(self, func: Callable[[Any], None], type: CallbackType):
        self.func = func
        self.type = type

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.func(*args, **kwargs)


galvanized_shot = CallBack(
    lambda igb: setattr(igb, "damage", igb.damage + igb.galvanized_shot * igb.num_debuffs * 0.4),
    CallbackType.IN_GAME_BUFF,
)
galvanized_diffusion = CallBack(
    lambda igb: setattr(igb, "multishot", igb.multishot + igb.galvanized_diffusion * 0.3),
    CallbackType.IN_GAME_BUFF,
)
secondary_enervate = CallBack(
    lambda igb: setattr(igb, "critical_chance", (3.05 + igb.critical_chance) / 2),
    CallbackType.IN_GAME_BUFF,
)

CALLBACK_MAPPING = {
    "galvanized_shot": galvanized_shot,
    "galvanized_diffusion": galvanized_diffusion,
    "secondary_enervate": secondary_enervate,
}

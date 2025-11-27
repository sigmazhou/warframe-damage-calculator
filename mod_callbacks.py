from wf_dmg_dataclass import InGameBuff


def galvanized_shot(igb: InGameBuff) -> None:
    igb.damage += igb.galvanized_shot * igb.num_debuffs * 0.4

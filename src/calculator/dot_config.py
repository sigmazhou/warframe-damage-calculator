from src.calculator.wf_dataclasses import DotConfig, DotType, DotBehavior


def initialize_dot_configs() -> dict[str, DotConfig]:
    """Initialize DOT configurations based on combined elements."""
    configs = {}

    # Only create configs for elements that deal damage and have DOT effects
    dot_elements = {
        'heat': (DotType.HEAT, DotBehavior.REFRESH_ALL, 0.5),
        'toxin': (DotType.TOXIN, DotBehavior.INDEPENDENT, 0.5),
        'slash': (DotType.SLASH, DotBehavior.INDEPENDENT, 0.35),
        'electricity': (DotType.ELECTRICITY, DotBehavior.INDEPENDENT, 0.5),
        'gas': (DotType.GAS, DotBehavior.INDEPENDENT, 0.5),
    }

    for element_name, (dot_type, behavior, multiplier) in dot_elements.items():
        configs[element_name] = DotConfig(
            dot_type=dot_type,
            behavior=behavior,
            base_duration=6.0,
            tick_rate=1.0,
            damage_multiplier=multiplier
        )

    return configs


DOT_CONFIG_MAP = initialize_dot_configs()

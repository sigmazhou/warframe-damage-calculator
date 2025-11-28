from src.calculator.dot_dataclasses import DotCallback, DotType, DotInstance


# Heat DOT callbacks
def heat_armor_strip(dot_instance: DotInstance, armor_strip_amount: float = 0.5) -> DotInstance:
    """Heat procs strip armor (not directly modifying damage, but useful for tracking)."""
    # This would interact with enemy armor calculations
    return dot_instance


heat_enhanced = DotCallback(
    func=lambda instance, **kwargs: DotInstance(
        dot_type=instance.dot_type,
        damage_per_tick=instance.damage_per_tick * 1.5,  # Example: 50% more damage
        remaining_duration=instance.remaining_duration,
        tick_rate=instance.tick_rate,
        total_duration=instance.total_duration
    ),
    dot_type=DotType.HEAT,
    description="Increases heat DOT damage by 50%"
)


# Toxin DOT callbacks
toxin_extended = DotCallback(
    func=lambda instance, **kwargs: DotInstance(
        dot_type=instance.dot_type,
        damage_per_tick=instance.damage_per_tick,
        remaining_duration=instance.remaining_duration * 1.5,  # 50% longer duration
        tick_rate=instance.tick_rate,
        total_duration=instance.total_duration * 1.5
    ),
    dot_type=DotType.TOXIN,
    description="Extends toxin DOT duration by 50%"
)


# Slash DOT callbacks
slash_hunter_munitions = DotCallback(
    func=lambda instance, **kwargs: DotInstance(
        dot_type=instance.dot_type,
        damage_per_tick=instance.damage_per_tick * 1.3,  # Hunter Munitions bonus
        remaining_duration=instance.remaining_duration,
        tick_rate=instance.tick_rate,
        total_duration=instance.total_duration
    ),
    dot_type=DotType.SLASH,
    description="Hunter Munitions slash proc bonus"
)


# Electricity DOT callbacks
electricity_chaining = DotCallback(
    func=lambda instance, chain_multiplier: DotInstance(
        dot_type=instance.dot_type,
        damage_per_tick=instance.damage_per_tick * chain_multiplier,
        remaining_duration=instance.remaining_duration,
        tick_rate=instance.tick_rate * 2,  # Ticks faster
        total_duration=instance.total_duration * 0.5  # But shorter duration
    ),
    dot_type=DotType.ELECTRICITY,
    description="Electricity chains to nearby enemies"
)


# Combined element callbacks
gas_cloud_damage = DotCallback(
    func=lambda instance, **kwargs: DotInstance(
        dot_type=DotType.GAS,
        damage_per_tick=instance.damage_per_tick * 0.5,  # Gas deals less per tick
        remaining_duration=8.0,  # But lasts longer
        tick_rate=instance.tick_rate,
        total_duration=8.0
    ),
    dot_type=DotType.GAS,
    description="Gas cloud DOT with extended duration"
)
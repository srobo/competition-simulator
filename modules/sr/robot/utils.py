def map_to_range(
    old_min: float,
    old_max: float,
    new_min: float,
    new_max: float,
    value: float,
) -> float:
    """Maps a value from within one range of inputs to within a range of outputs."""
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

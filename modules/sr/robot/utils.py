def map_to_range(old_min, old_max, new_min, new_max, value):
    """Maps a value from within one range of inputs to within a range of outputs."""
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

def map_to_range(old_min, old_max, new_min, new_max, value):
    return ((value - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

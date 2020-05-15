import random

DEFAULT_RANDOM_RANGE_PERCENT = 5 # The maximum randomness which can be added in either direction

def add_jitter(actual_value, min, max, random_range_percent = DEFAULT_RANDOM_RANGE_PERCENT):
    full_range = float(max) - float(min)

    random_range = full_range * (random_range_percent / float(100))
    
    random.seed(random.randint(min, max))

    actual_value = actual_value + random.uniform(-random_range, random_range)

    if actual_value > max:
        actual_value = max
    elif actual_value < min:
        actual_value = min

    return actual_value
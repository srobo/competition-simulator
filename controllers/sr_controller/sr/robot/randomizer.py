import random

DEFAULT_RANDOM_RANGE_PERCENT = 10 # The maximum randomness which can be added in either direction

def add_jitter(actual_value, min_possible, max_possible, random_range_percent = DEFAULT_RANDOM_RANGE_PERCENT):
    random_range = actual_value * (random_range_percent / float(100))

    new_value = actual_value + random_in_range(-random_range, random_range)

    if new_value > max_possible:
        new_value = max_possible
    elif new_value < min_possible:
        new_value = min_possible

    return new_value

def random_in_range(min_possible, max_possible):
    return random.SystemRandom().uniform(min_possible,max_possible)


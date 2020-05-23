import random

DEFAULT_RANDOM_RANGE_PERCENT = 10 # The maximum randomness which can be added in either direction

def add_jitter(actual_value, min_possible, max_possible, random_range_percent = DEFAULT_RANDOM_RANGE_PERCENT):
    random_range = actual_value * (random_range_percent / float(100))
    new_value = actual_value + random.randint(-random_range, random_range)
    return max(min_possible, min(actual_value, max_possible))

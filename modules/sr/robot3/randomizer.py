"""
To better reflect reality, we add a little randomness to robot inputs and outputs.
This prevents the simulation from providing unrealistic perfection.
"""

import random
from typing import TypeVar

T = TypeVar('T', float, int)

# The maximum randomness which can be added in either direction
DEFAULT_RANDOM_RANGE_PERCENT = 2.5

# The maximum randomness which can be added in either direction, compared to full scale value
DEFAULT_RANDOM_INDEPENDENT_RANGE_PERCENT = 0.25


def add_jitter(
    actual_value: T,
    min_possible: T,
    max_possible: T,
    random_range_percent: float = DEFAULT_RANDOM_RANGE_PERCENT,
) -> float:
    random_range = actual_value * (random_range_percent / float(100))
    new_value = actual_value + random.uniform(-random_range, random_range)
    return float(max(min_possible, min(new_value, max_possible)))


def add_independent_jitter(
    actual_value: T,
    min_possible: T,
    max_possible: T,
    std_dev_percent: float = DEFAULT_RANDOM_INDEPENDENT_RANGE_PERCENT,  # % of full scale value
    can_wrap: bool = False,
) -> float:
    value_range = max_possible - min_possible
    std_dev = value_range * (std_dev_percent / float(100))
    new_value = random.gauss(actual_value, std_dev)
    if can_wrap:
        new_value_normalised = new_value - min_possible
        return float((new_value_normalised % value_range) + min_possible)
    else:
        return float(max(min_possible, min(new_value, max_possible)))

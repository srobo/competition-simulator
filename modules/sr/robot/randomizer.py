"""
To better reflect reality, we add a little randomness to robot inputs and outputs.
This prevents the simulation from providing unrealistic perfection.
"""

import random
from typing import TypeVar

T = TypeVar('T', float, int)

# The maximum randomness which can be added in either direction
DEFAULT_RANDOM_RANGE_PERCENT = 2.5


def add_jitter(
    actual_value: T,
    min_possible: T,
    max_possible: T,
    random_range_percent: float = DEFAULT_RANDOM_RANGE_PERCENT,
) -> T:
    random_range = actual_value * (random_range_percent / float(100))
    new_value = actual_value + random.uniform(-random_range, random_range)
    return type(actual_value)(max(min_possible, min(new_value, max_possible)))

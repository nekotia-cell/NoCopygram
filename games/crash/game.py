# из папки games/crash

import random
import math
from typing import Optional


def get_random_multiplier_with_probabilities(user_multiplier: float) -> Optional[float]:
    if not (1 <= user_multiplier <= 14):
        return None

    if 1 <= user_multiplier <= 3:
        probabilities = {
            (1, 1.01): 0.25,
            (1.02, 2): 0.35,
            (2.01, 3): 0.3,
            (3.01, 5): 0.3,
            (5.01, 10): 0.15,
            (10.01, 14): 0.05
        }
    elif 3 < user_multiplier <= 8:
        probabilities = {
            (1, 3): 0.15,
            (3.01, 5): 0.25,
            (5.01, 8): 0.25,
            (8.01, 12): 0.3,
            (12.01, 14): 0.15
        }
    else:
        probabilities = {
            (1, 5): 0.05,
            (5.01, 8): 0.15,
            (8.01, 12): 0.15,
            (12.01, 13): 0.15,
            (13.01, 14): 0.10,
            (14.01, 20): 0.20
        }

    rand = random.random()
    cumulative_probability = 0
    selected_range = None

    for range_tuple, probability in probabilities.items():
        cumulative_probability += probability
        if rand <= cumulative_probability:
            selected_range = range_tuple
            break

    if selected_range:
        return round(random.uniform(selected_range[0], selected_range[1]), 2)
    return None

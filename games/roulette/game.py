# из папки games/roulette

import random
from typing import Tuple, List, Dict


class RouletteGame:
    def __init__(self):
        self.bets: List[Dict] = []
        self.user_red_black: Dict[int, Dict[str, bool]] = {}

    def add_bet(self, user_id: int, stake: int, bet_value):
        self.bets.append({'user_id': user_id, 'stake': stake, 'bet': bet_value})

    def can_place_color_bet(self, user_id: int, color: str) -> bool:
        if user_id not in self.user_red_black:
            self.user_red_black[user_id] = {'red': False, 'black': False}
        return not self.user_red_black[user_id][color]

    def set_color_bet(self, user_id: int, color: str):
        if user_id not in self.user_red_black:
            self.user_red_black[user_id] = {'red': False, 'black': False}
        self.user_red_black[user_id][color] = True

    def clear_bets(self):
        self.bets = []
        self.user_red_black = {}

    def get_user_bets(self, user_id: int) -> List[Dict]:
        return [bet for bet in self.bets if bet['user_id'] == user_id]

    def remove_user_bets(self, user_id: int) -> int:
        user_bets = self.get_user_bets(user_id)
        total = sum(bet['stake'] for bet in user_bets)
        self.bets = [bet for bet in self.bets if bet['user_id'] != user_id]
        if user_id in self.user_red_black:
            del self.user_red_black[user_id]
        return total


def spin_roulette() -> Tuple[int, str]:
    number = random.randint(0, 36)
    if number == 0:
        color = "🟢"
    else:
        color = "🔴" if random.random() < 0.5 else "⚫️"
    return number, color


def parse_bet(bet_str: str, user_id: int, user_red_black_bets: dict):
    try:
        if bet_str.isdigit():
            number = int(bet_str)
            if 0 <= number <= 36:
                return number
        elif '-' in bet_str:
            parts = bet_str.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start = int(parts[0])
                end = int(parts[1])
                if 0 <= start <= 36 and 0 <= end <= 36 and start <= end:
                    return (start, end)
        elif bet_str.lower() == 'к':
            if user_id in user_red_black_bets and user_red_black_bets[user_id].get('red'):
                return None
            return 'red'
        elif bet_str.lower() == 'ч':
            if user_id in user_red_black_bets and user_red_black_bets[user_id].get('black'):
                return None
            return 'black'
        return None
    except ValueError:
        return None

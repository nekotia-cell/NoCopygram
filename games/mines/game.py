# Game logic for the mines game.

import random
import math
import time
from typing import Set
from config import GAME_TIMEOUT

MULTIPLIERS = [0, 1.28, 1.65, 2.1, 2.5, 2.9, 3.5, 4.1, 4.6, 5.1, 5.6, 6.2, 6.9, 7.4, 7.5, 7.6, 7.7, 7.9]


class MinesGame:
    def __init__(self, user_id: int, stake: int, chat_id: int = None):
        self.user_id = user_id
        self.stake = stake
        self.chat_id = chat_id
        self.mine_positions = random.sample(range(25), 6)
        self.revealed: Set[int] = set()
        self.multiplier_index = 0
        self.last_action_time = time.time()
        self.message_id = None
    
    def to_dict(self) -> dict:
        return {
            'stake': self.stake,
            'chat_id': self.chat_id,
            'mine_positions': self.mine_positions,
            'revealed': list(self.revealed),
            'multiplier_index': self.multiplier_index,
            'last_action_time': self.last_action_time,
            'message_id': self.message_id
        }
    
    @classmethod
    def from_dict(cls, user_id: int, data: dict) -> 'MinesGame':
        game = cls.__new__(cls)
        game.user_id = user_id
        game.stake = data['stake']
        game.chat_id = data.get('chat_id')
        game.mine_positions = data['mine_positions']
        game.revealed = set(data['revealed'])
        game.multiplier_index = data['multiplier_index']
        game.last_action_time = data['last_action_time']
        game.message_id = data.get('message_id')
        return game
    
    def reveal(self, position: int) -> bool:
        """Returns True if safe, False if mine"""
        if not 0 <= position < 25:
            raise ValueError("position must be between 0 and 24")
        self.revealed.add(position)
        self.last_action_time = time.time()
        return position not in self.mine_positions
    
    def get_current_multiplier(self) -> float:
        return MULTIPLIERS[self.multiplier_index]
    
    def next_multiplier(self):
        if self.multiplier_index < len(MULTIPLIERS) - 1:
            self.multiplier_index += 1
    
    def calculate_winnings(self) -> int:
        return math.floor(self.stake * self.get_current_multiplier())
    
    def is_max_multiplier(self) -> bool:
        return self.multiplier_index >= len(MULTIPLIERS) - 1
    
    def is_timeout(self) -> bool:
        return time.time() - self.last_action_time > GAME_TIMEOUT
    
    def refund(self):
        from database.models import UserDB
        UserDB.update_balance(self.user_id, self.stake)

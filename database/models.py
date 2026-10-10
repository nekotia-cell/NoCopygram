import json
import time
from typing import Optional, List, Dict, Any
from database.db import get_db, init_db

# User operations
class UserDB:
    @staticmethod
    def get(user_id: int) -> Optional[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                return data
            return None
    
    @staticmethod
    def create(user_id: int, first_name: str, last_name: Optional[str] = None, 
               registration_date: Optional[str] = None):
        with get_db() as cursor:
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, first_name, last_name, registration_date)
                VALUES (?, ?, ?, ?)
            ''', (user_id, first_name, last_name, registration_date))
    
    @staticmethod
    def update_balance(user_id: int, amount: int):
        with get_db() as cursor:
            cursor.execute('''
                UPDATE users SET balance = balance + ? WHERE user_id = ?
            ''', (amount, user_id))

    @staticmethod
    def transfer(sender_id: int, recipient_id: int, amount: int) -> bool:
        """Atomically move a positive amount between two users."""
        if amount <= 0 or sender_id == recipient_id:
            return False
        with get_db() as cursor:
            cursor.execute('SELECT 1 FROM users WHERE user_id = ?', (recipient_id,))
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                'UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?',
                (amount, sender_id, amount),
            )
            if cursor.rowcount != 1:
                return False
            cursor.execute(
                'UPDATE users SET balance = balance + ? WHERE user_id = ?',
                (amount, recipient_id),
            )
            return cursor.rowcount == 1

    @staticmethod
    def debit(user_id: int, amount: int) -> bool:
        if amount <= 0:
            return False
        with get_db() as cursor:
            cursor.execute(
                'UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?',
                (amount, user_id, amount),
            )
            return cursor.rowcount == 1

    @staticmethod
    def claim_bonus(user_id: int, amount: int, now: float, cooldown: float) -> bool:
        """Atomically claim a bonus only if the cooldown has elapsed."""
        if amount <= 0:
            return False
        with get_db() as cursor:
            cursor.execute(
                '''UPDATE users
                   SET balance = balance + ?, bonus_timer = ?
                   WHERE user_id = ? AND bonus_timer <= ?''',
                (amount, now, user_id, now - cooldown),
            )
            return cursor.rowcount == 1
    
    @staticmethod
    def set_balance(user_id: int, balance: int):
        with get_db() as cursor:
            cursor.execute('UPDATE users SET balance = ? WHERE user_id = ?', 
                         (balance, user_id))
    
    @staticmethod
    def get_balance(user_id: int) -> int:
        with get_db() as cursor:
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['balance'] if row else 0
    
    @staticmethod
    def set_vip(user_id: int, expires: float):
        with get_db() as cursor:
            cursor.execute('UPDATE users SET vip_expires = ? WHERE user_id = ?', 
                         (expires, user_id))
    
    @staticmethod
    def get_vip_expires(user_id: int) -> float:
        with get_db() as cursor:
            cursor.execute('SELECT vip_expires FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['vip_expires'] if row else 0
    
    @staticmethod
    def set_bonus_timer(user_id: int, timer: float):
        with get_db() as cursor:
            cursor.execute('UPDATE users SET bonus_timer = ? WHERE user_id = ?', 
                         (timer, user_id))
    
    @staticmethod
    def get_bonus_timer(user_id: int) -> float:
        with get_db() as cursor:
            cursor.execute('SELECT bonus_timer FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['bonus_timer'] if row else 0
    
    @staticmethod
    def set_blocked(user_id: int, blocked: bool):
        with get_db() as cursor:
            cursor.execute('UPDATE users SET is_blocked = ? WHERE user_id = ?', 
                         (1 if blocked else 0, user_id))
    
    @staticmethod
    def is_blocked(user_id: int) -> bool:
        with get_db() as cursor:
            cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return bool(row['is_blocked']) if row else False
    
    @staticmethod
    def set_clan(user_id: int, clan_name: Optional[str]):
        with get_db() as cursor:
            cursor.execute('UPDATE users SET clan_name = ? WHERE user_id = ?', 
                         (clan_name, user_id))
    
    @staticmethod
    def get_clan(user_id: int) -> Optional[str]:
        with get_db() as cursor:
            cursor.execute('SELECT clan_name FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            return row['clan_name'] if row else None
    
    @staticmethod
    def get_top(limit: int = 50, min_balance: int = 100000) -> List[Dict]:
        with get_db() as cursor:
            cursor.execute('''
                SELECT * FROM users 
                WHERE balance >= ? 
                ORDER BY balance DESC 
                LIMIT ?
            ''', (min_balance, limit))
            return [dict(row) for row in cursor.fetchall()]


# Clan operations
class ClanDB:
    @staticmethod
    def create(name: str, creator_id: int, creator_first_name: str):
        with get_db() as cursor:
            cursor.execute('''
                INSERT INTO clans (name, creator_id, creator_first_name)
                VALUES (?, ?, ?)
            ''', (name, creator_id, creator_first_name))
    
    @staticmethod
    def get(name: str) -> Optional[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM clans WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def delete(name: str):
        with get_db() as cursor:
            cursor.execute('DELETE FROM clans WHERE name = ?', (name,))
            cursor.execute('DELETE FROM clan_members WHERE clan_name = ?', (name,))
            cursor.execute('UPDATE users SET clan_name = NULL WHERE clan_name = ?', (name,))
    
    @staticmethod
    def update_treasury(name: str, amount: int):
        with get_db() as cursor:
            cursor.execute('UPDATE clans SET treasury = treasury + ? WHERE name = ?', 
                         (amount, name))
    
    @staticmethod
    def update_rating(name: str, rating: int):
        with get_db() as cursor:
            cursor.execute('UPDATE clans SET rating = ? WHERE name = ?', 
                         (rating, name))
    
    @staticmethod
    def get_top(limit: int = 10) -> List[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM clans ORDER BY rating DESC LIMIT ?', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def exists(name: str) -> bool:
        with get_db() as cursor:
            cursor.execute('SELECT 1 FROM clans WHERE name = ?', (name,))
            return cursor.fetchone() is not None


# Clan members operations
class ClanMemberDB:
    @staticmethod
    def add(user_id: int, clan_name: str, role: str = 'участник', increment_count: bool = True):
        with get_db() as cursor:
            cursor.execute('SELECT 1 FROM clan_members WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                return False
            cursor.execute('''
                INSERT INTO clan_members (user_id, clan_name, role)
                VALUES (?, ?, ?)
            ''', (user_id, clan_name, role))
            if increment_count:
                cursor.execute('''
                    UPDATE clans SET members_count = members_count + 1 WHERE name = ?
                ''', (clan_name,))
            return True
    
    @staticmethod
    def remove(user_id: int, clan_name: Optional[str] = None):
        with get_db() as cursor:
            query = 'SELECT clan_name FROM clan_members WHERE user_id = ?'
            params = [user_id]
            if clan_name is not None:
                query += ' AND clan_name = ?'
                params.append(clan_name)
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                clan_name = row['clan_name']
                cursor.execute('DELETE FROM clan_members WHERE user_id = ?', (user_id,))
                cursor.execute('''
                    UPDATE clans SET members_count = members_count - 1 WHERE name = ?
                ''', (clan_name,))
                return True
            return False
    
    @staticmethod
    def get_role(user_id: int, clan_name: Optional[str] = None) -> Optional[str]:
        with get_db() as cursor:
            if clan_name is None:
                cursor.execute('SELECT role FROM clan_members WHERE user_id = ?', (user_id,))
            else:
                cursor.execute(
                    'SELECT role FROM clan_members WHERE user_id = ? AND clan_name = ?',
                    (user_id, clan_name),
                )
            row = cursor.fetchone()
            return row['role'] if row else None
    
    @staticmethod
    def update_role(user_id: int, role: str, clan_name: Optional[str] = None):
        with get_db() as cursor:
            if clan_name is None:
                cursor.execute('UPDATE clan_members SET role = ? WHERE user_id = ?',
                               (role, user_id))
            else:
                cursor.execute(
                    'UPDATE clan_members SET role = ? WHERE user_id = ? AND clan_name = ?',
                    (role, user_id, clan_name),
                )
    
    @staticmethod
    def get_members(clan_name: str) -> List[Dict]:
        with get_db() as cursor:
            cursor.execute('''
                SELECT cm.*, u.first_name 
                FROM clan_members cm
                JOIN users u ON cm.user_id = u.user_id
                WHERE cm.clan_name = ?
            ''', (clan_name,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def count(clan_name: str) -> int:
        with get_db() as cursor:
            cursor.execute('SELECT COUNT(*) as count FROM clan_members WHERE clan_name = ?', 
                         (clan_name,))
            row = cursor.fetchone()
            return row['count'] if row else 0


# Promo code operations
class PromoDB:
    @staticmethod
    def create(code: str, koto_grams: int, activations: int):
        with get_db() as cursor:
            cursor.execute('''
                INSERT INTO promo_codes (code, koto_grams, activations, used_by)
                VALUES (?, ?, ?, '[]')
            ''', (code, koto_grams, activations))
    
    @staticmethod
    def get(code: str) -> Optional[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['used_by'] = json.loads(data['used_by'])
            return data
        return None
    
    @staticmethod
    def delete(code: str):
        with get_db() as cursor:
            cursor.execute('DELETE FROM promo_codes WHERE code = ?', (code,))
    
    @staticmethod
    def use(code: str, user_id: int) -> bool:
        with get_db() as cursor:
            cursor.execute('BEGIN IMMEDIATE')
            cursor.execute('SELECT * FROM promo_codes WHERE code = ?', (code,))
            row = cursor.fetchone()
            if not row:
                return False
            
            used_by = json.loads(row['used_by'])
            if user_id in used_by:
                return False
            
            if row['activations'] <= 0:
                return False
            
            used_by.append(user_id)
            cursor.execute('''
                UPDATE promo_codes 
                SET activations = activations - 1, used_by = ?
                WHERE code = ? AND activations > 0
            ''', (json.dumps(used_by), code))
            return cursor.rowcount == 1

    @staticmethod
    def get_by_code_case_insensitive(code: str) -> Optional[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM promo_codes WHERE LOWER(code) = LOWER(?)', (code,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['used_by'] = json.loads(data['used_by'])
                return data
            return None


# Roulette log operations
class RouletteLogDB:
    @staticmethod
    def add(result: str):
        with get_db() as cursor:
            cursor.execute('INSERT INTO roulette_log (result) VALUES (?)', (result,))
            # Keep only last 10
            cursor.execute('''
                DELETE FROM roulette_log 
                WHERE id NOT IN (SELECT id FROM roulette_log ORDER BY id DESC LIMIT 10)
            ''')
    
    @staticmethod
    def get_all() -> List[str]:
        with get_db() as cursor:
            cursor.execute('SELECT result FROM roulette_log ORDER BY id DESC')
            return [row['result'] for row in cursor.fetchall()]


# Active games operations (for mines)
class ActiveGameDB:
    @staticmethod
    def save(user_id: int, game_type: str, game_data: dict):
        with get_db() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO active_games (user_id, game_type, game_data, last_action_time)
                VALUES (?, ?, ?, ?)
            ''', (user_id, game_type, json.dumps(game_data), time.time()))
    
    @staticmethod
    def get(user_id: int) -> Optional[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM active_games WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['game_data'] = json.loads(data['game_data'])
                return data
            return None
    
    @staticmethod
    def delete(user_id: int):
        with get_db() as cursor:
            cursor.execute('DELETE FROM active_games WHERE user_id = ?', (user_id,))
    
    @staticmethod
    def get_all() -> List[Dict]:
        with get_db() as cursor:
            cursor.execute('SELECT * FROM active_games')
            games = []
            for row in cursor.fetchall():
                data = dict(row)
                data['game_data'] = json.loads(data['game_data'])
                games.append(data)
            return games
    
    @staticmethod
    def update_time(user_id: int):
        with get_db() as cursor:
            cursor.execute('''
                UPDATE active_games SET last_action_time = ? WHERE user_id = ?
            ''', (time.time(), user_id))

    @staticmethod
    def settle(user_id: int, amount: int) -> bool:
        """Delete an active game and pay exactly once in one transaction."""
        if amount < 0:
            return False
        with get_db() as cursor:
            cursor.execute('DELETE FROM active_games WHERE user_id = ?', (user_id,))
            if cursor.rowcount != 1:
                return False
            if amount:
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                               (amount, user_id))
                return cursor.rowcount == 1
            return True

    @staticmethod
    def expire_and_refund(user_id: int, stake: int) -> bool:
        """Remove an expired game and refund its stake exactly once."""
        if stake < 0:
            return False
        with get_db() as cursor:
            cursor.execute('DELETE FROM active_games WHERE user_id = ?', (user_id,))
            if cursor.rowcount != 1:
                return False
            cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?',
                           (stake, user_id))
            return cursor.rowcount == 1

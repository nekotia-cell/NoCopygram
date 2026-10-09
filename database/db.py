import sqlite3
import threading
from contextlib import contextmanager
from config import DB_PATH

# Thread-local storage for connections
local = threading.local()

def get_connection():
    """Get thread-local database connection"""
    if not hasattr(local, 'connection'):
        local.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        local.connection.row_factory = sqlite3.Row
    return local.connection

@contextmanager
def get_db():
    """Context manager for database operations"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def init_db():
    """Initialize database tables"""
    with get_db() as cursor:
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                balance INTEGER DEFAULT 0,
                vip_expires REAL DEFAULT 0,
                bonus_timer REAL DEFAULT 0,
                registration_date TEXT,
                clan_name TEXT DEFAULT NULL,
                is_blocked INTEGER DEFAULT 0
            )
        ''')
        
        # Clans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                name TEXT PRIMARY KEY,
                creator_id INTEGER,
                creator_first_name TEXT,
                rating INTEGER DEFAULT 0,
                treasury INTEGER DEFAULT 0,
                members_count INTEGER DEFAULT 1
            )
        ''')
        
        # Clan members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clan_members (
                user_id INTEGER PRIMARY KEY,
                clan_name TEXT,
                role TEXT DEFAULT 'участник',
                FOREIGN KEY (clan_name) REFERENCES clans(name)
            )
        ''')
        
        # Promo codes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                koto_grams INTEGER,
                activations INTEGER,
                used_by TEXT DEFAULT '[]',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        
        # Roulette log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roulette_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result TEXT,
                timestamp REAL DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # Active games table (for mines)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_games (
                user_id INTEGER PRIMARY KEY,
                game_type TEXT,
                game_data TEXT,
                last_action_time REAL
            )
        ''')

def close_db():
    """Close database connection for current thread"""
    if hasattr(local, 'connection'):
        local.connection.close()
        del local.connection
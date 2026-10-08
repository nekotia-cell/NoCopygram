from typing import List, Dict
from database.models import ClanDB


def get_top_clans(limit: int = 10) -> List[Dict]:
    return ClanDB.get_top(limit)

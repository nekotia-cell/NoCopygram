# из папки users/

from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    user_id: int
    first_name: str
    last_name: Optional[str]
    balance: int = 0
    vip_expires: Optional[float] = None
    registration_date: Optional[str] = None
    clan_name: Optional[str] = None

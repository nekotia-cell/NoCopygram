from typing import Optional
from config import CLAN_MAX_MEMBERS
from database.models import ClanDB, ClanMemberDB


class Clan:
    def __init__(self, name: str, creator_id: int, creator_first_name: str):
        self.name = name
        self.creator_id = creator_id
        self.creator_first_name = creator_first_name
        self._load_from_db()
    
    def _load_from_db(self):
        data = ClanDB.get(self.name)
        if data:
            self.rating = data['rating']
            self.treasury = data['treasury']
        else:
            self.rating = 0
            self.treasury = 0
    
    def deposit(self, amount: int):
        ClanDB.update_treasury(self.name, amount)
        self.treasury += amount
    
    def withdraw(self, amount: int) -> bool:
        if self.treasury >= amount:
            ClanDB.update_treasury(self.name, -amount)
            self.treasury -= amount
            return True
        return False
    
    def add_member(self, user_id: int) -> bool:
        if ClanMemberDB.count(self.name) < CLAN_MAX_MEMBERS:
            ClanMemberDB.add(user_id, self.name, "участник")
            from database.models import UserDB
            UserDB.set_clan(user_id, self.name)
            return True
        return False
    
    def remove_member(self, user_id: int):
        ClanMemberDB.remove(user_id)
        from database.models import UserDB
        UserDB.set_clan(user_id, None)
    
    def get_member_role(self, user_id: int) -> Optional[str]:
        return ClanMemberDB.get_role(user_id)
    
    def promote_member(self, user_id: int) -> bool:
        role = self.get_member_role(user_id)
        if role == "участник":
            ClanMemberDB.update_role(user_id, "модератор")
            return True
        elif role == "модератор":
            ClanMemberDB.update_role(user_id, "заместитель")
            return True
        return False
    
    def demote_member(self, user_id: int) -> bool:
        role = self.get_member_role(user_id)
        if role == "заместитель":
            ClanMemberDB.update_role(user_id, "модератор")
            return True
        elif role == "модератор":
            ClanMemberDB.update_role(user_id, "участник")
            return True
        return False
    
    @property
    def members(self):
        return {m['user_id']: m['role'] for m in ClanMemberDB.get_members(self.name)}

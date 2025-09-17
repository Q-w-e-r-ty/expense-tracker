"""
user.py


Defines User and UserManager. Uses salted SHA-256 for password storage.


users.csv columns: user_id,username,hashed_password


hashed_password format: salt$sha256hex
"""


import csv
import os
import hashlib
import binascii
from dataclasses import dataclass
from typing import Optional, List


USERS_CSV = 'users.csv'




@dataclass
class User:
    user_id: int
    username: str
    hashed_password: str # stored as salt$hexhash




class UserManager:
    def __init__(self, path: str = USERS_CSV):
        self.path = path
        self.users: List[User] = []
        self._ensure_file()
        self._load()


    def _ensure_file(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['user_id', 'username', 'hashed_password'])


    def _load(self):
        self.users = []
        try:
            with open(self.path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.users.append(User(int(r['user_id']), r['username'], r['hashed_password']))
        except FileNotFoundError:
            self._ensure_file()


    def _save(self):
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'username', 'hashed_password'])
            for u in self.users:
                writer.writerow([u.user_id, u.username, u.hashed_password])
                print('Users loaded:', len(um.users))

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        if salt is None:
            salt = os.urandom(16)
            pwd = password.encode('utf-8')
            dk = hashlib.pbkdf2_hmac('sha256', pwd, salt, 100_000)
        return binascii.hexlify(salt).decode() + '$' + binascii.hexlify(dk).decode()


    def _verify_password(self, stored: str, provided: str) -> bool:
        try:
            salt_hex, hash_hex = stored.split('$')
            salt = binascii.unhexlify(salt_hex)
            provided_hash = hashlib.pbkdf2_hmac('sha256', provided.encode('utf-8'), salt, 100_000)
            return binascii.hexlify(provided_hash).decode() == hash_hex
        except Exception:
            return False


    def find_by_username(self, username: str) -> Optional[User]:
        for u in self.users:
            if u.username == username:
                return u
        return None


    def create_user(self, username: str, password: str) -> User:
    # username uniqueness
        if self.find_by_username(username):
            raise ValueError('Username already exists')
        next_id = max([u.user_id for u in self.users], default=0) + 1
        hashed = self._hash_password(password)
        user = User(next_id, username, hashed)
        self.users.append(user)
        self._save()
        return user


    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.find_by_username(username)
        if not user:
            return None
        if self._verify_password(user.hashed_password, password):
            return user
        return None


    @staticmethod
    def validate_password_rules(password: str) -> bool:
    # at least 8 chars, one uppercase, one lowercase, one digit
        if len(password) < 8:
            return False
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_upper and has_lower and has_digit




if __name__ == '__main__':
    um = UserManager()
    print('Users loaded:', len(um.users))
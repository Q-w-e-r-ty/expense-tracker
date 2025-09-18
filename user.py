# -------------------- user.py --------------------
"""
user.py
Manages user creation and authentication. Uses salted SHA-256 for password storage.
users.csv fields: user_id,username,hashed_password
hashed_password format stored: salt$sha256_hex
"""

import csv
import os
import hashlib
import secrets
from typing import Optional

USERS_CSV = 'users.csv'

class User:
    def __init__(self, user_id: str, username: str, hashed_password: str):
        self.user_id = user_id
        self.username = username
        self.hashed_password = hashed_password


class UserManager:
    def __init__(self, path: str = USERS_CSV):
        self.path = path
        # Ensure file exists with header
        if not os.path.exists(self.path):
            with open(self.path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['user_id', 'username', 'hashed_password'])

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Return salted sha256 in the form salt$hash"""
        if salt is None:
            salt = secrets.token_hex(16)
        h = hashlib.sha256()
        h.update((salt + password).encode('utf-8'))
        return f"{salt}${h.hexdigest()}"

    def _verify_password(self, password: str, stored: str) -> bool:
        try:
            salt, h = stored.split('$')
        except ValueError:
            return False
        return self._hash_password(password, salt) == stored

    def _load_all_users(self) -> list:
        users = []
        with open(self.path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                users.append(User(r['user_id'], r['username'], r['hashed_password']))
        return users

    def get_user_by_username(self, username: str) -> Optional[User]:
        for u in self._load_all_users():
            if u.username == username:
                return u
        return None

    def create_user(self, username: str, password: str) -> User:
        # Basic username existence check
        if self.get_user_by_username(username) is not None:
            raise ValueError('Username already exists')

        # Generate a new user_id (sequential integer as string)
        users = self._load_all_users()
        if not users:
            next_id = 1
        else:
            ids = [int(u.user_id) for u in users]
            next_id = max(ids) + 1
        hashed = self._hash_password(password)
        user = User(str(next_id), username, hashed)

        # Append to CSV immediately
        with open(self.path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([user.user_id, user.username, user.hashed_password])

        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if user and self._verify_password(password, user.hashed_password):
            return user
        return None

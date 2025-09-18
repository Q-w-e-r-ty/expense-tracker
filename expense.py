# -------------------- expense.py --------------------
"""
expense.py
Manages expenses stored in expenses.csv with fields:
expense_id, user_id, amount, date, category, description

- expense_id is an integer starting at 1 per user
- composite key: user_id + expense_id
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

EXPENSES_CSV = 'expenses.csv'

CATEGORIES = ['Food', 'Transport', 'Rent', 'Utilities', 'Shopping', 'Other']

class Expense:
    def __init__(self, expense_id: str, user_id: str, amount: float, date: str, category: str, description: str):
        self.expense_id = expense_id
        self.user_id = user_id
        self.amount = float(amount)
        self.date = date  # YYYY-MM-DD
        self.category = category
        self.description = description

    def to_dict(self) -> Dict:
        return {
            'expense_id': str(self.expense_id),
            'user_id': str(self.user_id),
            'amount': f"{self.amount:.2f}",
            'date': self.date,
            'category': self.category,
            'description': self.description,
        }


class ExpenseManager:
    def __init__(self, path: str = EXPENSES_CSV):
        self.path = path
        if not os.path.exists(self.path):
            with open(self.path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])

    def _load_all(self) -> List[Expense]:
        expenses = []
        with open(self.path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    expenses.append(Expense(r['expense_id'], r['user_id'], float(r['amount']), r['date'], r['category'], r['description']))
                except Exception:
                    continue
        return expenses

    def _write_all(self, expenses: List[Expense]):
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['expense_id', 'user_id', 'amount', 'date', 'category', 'description']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in expenses:
                writer.writerow(e.to_dict())

    def list_for_user(self, user_id: str) -> List[Expense]:
        all_exp = self._load_all()
        user_exp = [e for e in all_exp if e.user_id == str(user_id)]
        # chronological order by date
        user_exp.sort(key=lambda x: datetime.strptime(x.date, '%Y-%m-%d'))
        return user_exp

    def _next_expense_id_for_user(self, user_id: str) -> int:
        user_exp = [int(e.expense_id) for e in self._load_all() if e.user_id == str(user_id)]
        return max(user_exp) + 1 if user_exp else 1

    def add_expense(self, user_id: str, amount: float, date: str, category: str, description: str) -> Expense:
        # Validate category
        if category not in CATEGORIES:
            raise ValueError('Invalid category')
        # Validate date format
        datetime.strptime(date, '%Y-%m-%d')
        if amount <= 0:
            raise ValueError('Amount must be positive')

        eid = self._next_expense_id_for_user(user_id)
        exp = Expense(str(eid), str(user_id), amount, date, category, description)
        all_exp = self._load_all()
        all_exp.append(exp)
        self._write_all(all_exp)
        return exp

    def find_expense(self, user_id: str, expense_id: str) -> Optional[Expense]:
        for e in self._load_all():
            if e.user_id == str(user_id) and e.expense_id == str(expense_id):
                return e
        return None

    def edit_expense(self, user_id: str, expense_id: str, **kwargs) -> Expense:
        all_exp = self._load_all()
        found = False
        for e in all_exp:
            if e.user_id == str(user_id) and e.expense_id == str(expense_id):
                found = True
                if 'amount' in kwargs:
                    if float(kwargs['amount']) <= 0:
                        raise ValueError('Amount must be positive')
                    e.amount = float(kwargs['amount'])
                if 'date' in kwargs:
                    datetime.strptime(kwargs['date'], '%Y-%m-%d')
                    e.date = kwargs['date']
                if 'category' in kwargs:
                    if kwargs['category'] not in CATEGORIES:
                        raise ValueError('Invalid category')
                    e.category = kwargs['category']
                if 'description' in kwargs:
                    e.description = kwargs['description']
                break
        if not found:
            raise KeyError('Expense not found')
        self._write_all(all_exp)
        return e

    def delete_expense(self, user_id: str, expense_id: str) -> bool:
        all_exp = self._load_all()
        new_list = [e for e in all_exp if not (e.user_id == str(user_id) and e.expense_id == str(expense_id))]
        if len(new_list) == len(all_exp):
            return False
        self._write_all(new_list)
        return True

    def export_user_expenses(self, user_id: str, out_path: str):
        user_exp = self.list_for_user(user_id)
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])
            writer.writeheader()
            for e in user_exp:
                writer.writerow(e.to_dict())

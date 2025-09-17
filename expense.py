
"""
expense.py

Defines Expense and ExpenseManager which reads/writes expenses.csv.

expenses.csv columns: expense_id,user_id,amount,date,category,description

expense_id is per-user sequential starting at 1.
"""

import csv
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

EXPENSES_CSV = 'expenses.csv'

VALID_CATEGORIES = ['Food', 'Transport', 'Rent', 'Utilities', 'Shopping', 'Other']


@dataclass
class Expense:
    expense_id: int  # sequential per user
    user_id: int
    amount: float
    date: str  # YYYY-MM-DD
    category: str
    description: str


class ExpenseManager:
    def __init__(self, path: str = EXPENSES_CSV):
        self.path = path
        self.expenses: List[Expense] = []
        self._ensure_file()
        self._load()

    def _ensure_file(self):
        if not os.path.exists(self.path):
            with open(self.path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])

    def _load(self):
        self.expenses = []
        try:
            with open(self.path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    self.expenses.append(Expense(int(r['expense_id']), int(r['user_id']), float(r['amount']), r['date'], r['category'], r['description']))
        except FileNotFoundError:
            self._ensure_file()

    def _save(self):
        with open(self.path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])
            for e in self.expenses:
                writer.writerow([e.expense_id, e.user_id, f'{e.amount:.2f}', e.date, e.category, e.description])

    def list_user_expenses(self, user_id: int) -> List[Expense]:
        # chronological order by date
        user_exp = [e for e in self.expenses if e.user_id == user_id]
        user_exp.sort(key=lambda x: x.date)
        return user_exp

    def next_expense_id_for_user(self, user_id: int) -> int:
        ids = [e.expense_id for e in self.expenses if e.user_id == user_id]
        return max(ids, default=0) + 1

    def add_expense(self, user_id: int, amount: float, date: str, category: str, description: str) -> Expense:
        if category not in VALID_CATEGORIES:
            raise ValueError('Invalid category')
        eid = self.next_expense_id_for_user(user_id)
        exp = Expense(eid, user_id, amount, date, category, description)
        self.expenses.append(exp)
        self._save()
        return exp

    def find_expense(self, user_id: int, expense_id: int) -> Optional[Expense]:
        for e in self.expenses:
            if e.user_id == user_id and e.expense_id == expense_id:
                return e
        return None

    def edit_expense(self, user_id: int, expense_id: int, **kwargs) -> Expense:
        exp = self.find_expense(user_id, expense_id)
        if not exp:
            raise ValueError('Expense not found')
        # editable fields: amount, date, category, description
        if 'amount' in kwargs:
            exp.amount = float(kwargs['amount'])
        if 'date' in kwargs:
            exp.date = kwargs['date']
        if 'category' in kwargs:
            if kwargs['category'] not in VALID_CATEGORIES:
                raise ValueError('Invalid category')
            exp.category = kwargs['category']
        if 'description' in kwargs:
            exp.description = kwargs['description']
        self._save()
        return exp

    def delete_expense(self, user_id: int, expense_id: int) -> bool:
        exp = self.find_expense(user_id, expense_id)
        if not exp:
            return False
        self.expenses.remove(exp)
        self._save()
        return True

    def export_user_expenses(self, user_id: int, filepath: str):
        user_expenses = self.list_user_expenses(user_id)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])
            for e in user_expenses:
                writer.writerow([e.expense_id, e.user_id, f'{e.amount:.2f}', e.date, e.category, e.description])


if __name__ == '__main__':
    em = ExpenseManager()
    print('Expenses loaded:', len(em.expenses))
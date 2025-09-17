"""
main.py

CLI entrypoint. Provides main menu and transaction submenu.

Dependencies: pandas, matplotlib
Install: pip install pandas matplotlib
"""

import sys
from user import UserManager
from expense import ExpenseManager, VALID_CATEGORIES
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt


def input_nonempty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print('Input cannot be empty.')


def validate_date(date_text: str) -> bool:
    try:
        datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_amount(amount_text: str):
    try:
        v = float(amount_text)
        if v <= 0:
            return None
        return v
    except Exception:
        return None


class CLIApp:
    def __init__(self):
        self.user_mgr = UserManager()
        self.exp_mgr = ExpenseManager()
        self.current_user = None

    def run(self):
        while True:
            print('\n--- Personal Expense Manager ---')
            print('1) Login')
            print('2) Create Account')
            print('3) Exit')
            choice = input('Choose an option: ').strip()
            if choice == '1':
                self.login()
            elif choice == '2':
                self.create_account()
            elif choice == '3':
                print('Goodbye!')
                sys.exit(0)
            else:
                print('Invalid option. Try again.')

    def login(self):
        username = input_nonempty('Username: ')
        password = input('Password: ')
        user = self.user_mgr.authenticate(username, password)
        if not user:
            print('Authentication failed. Check username/password.')
            return
        self.current_user = user
        print(f'Welcome {user.username}!')
        self.transaction_menu()

    def create_account(self):
        username = input_nonempty('Choose a username: ')
        if self.user_mgr.find_by_username(username):
            print('Username already exists.')
            return
        while True:
            password = input('Choose a password: ')
            if not self.user_mgr.validate_password_rules(password):
                print('Password must be at least 8 characters, contain upper, lower, and digit.')
            else:
                confirm = input('Confirm password: ')
                if password != confirm:
                    print('Passwords do not match.')
                else:
                    break
        try:
            user = self.user_mgr.create_user(username, password)
            print(f'Account created. Your user id: {user.user_id}')
        except Exception as e:
            print('Failed to create account:', e)

    def transaction_menu(self):
        while True:
            print('\n--- Transactions ---')
            print('LIST      - List expenses')
            print('ADD       - Add expense')
            print('EDIT      - Edit expense')
            print('DELETE    - Delete expense')
            print('REPORTS   - Show reports')
            print('VISUALIZE - Show charts')
            print('EXPORT    - Export expenses to CSV')
            print('LOGOUT    - Logout')
            cmd = input('Enter command: ').strip().upper()
            if cmd == 'LIST':
                self.cmd_list()
            elif cmd == 'ADD':
                self.cmd_add()
            elif cmd == 'EDIT':
                self.cmd_edit()
            elif cmd == 'DELETE':
                self.cmd_delete()
            elif cmd == 'REPORTS':
                self.cmd_reports()
            elif cmd == 'VISUALIZE':
                self.cmd_visualize()
            elif cmd == 'EXPORT':
                self.cmd_export()
            elif cmd == 'LOGOUT':
                print('Logging out...')
                self.current_user = None
                return
            else:
                print('Unknown command.')

    def cmd_list(self):
        exps = self.exp_mgr.list_user_expenses(self.current_user.user_id)
        if not exps:
            print('No expenses found.')
            return
        print('ID | Amount | Date | Category | Description')
        for e in exps:
            print(f'{e.expense_id} | {e.amount:.2f} | {e.date} | {e.category} | {e.description}')

    def cmd_add(self):
        amt = validate_amount(input_nonempty('Amount: '))
        if amt is None:
            print('Invalid amount.')
            return
        date = input_nonempty('Date (YYYY-MM-DD): ')
        if not validate_date(date):
            print('Invalid date.')
            return
        print('Categories:', ', '.join(VALID_CATEGORIES))
        category = input('Category: ').strip()
        if category not in VALID_CATEGORIES:
            print('Invalid category.')
            return
        desc = input('Description: ').strip()
        self.exp_mgr.add_expense(self.current_user.user_id, amt, date, category, desc)
        print('Expense added.')

    def cmd_edit(self):
        eid_text = input_nonempty('Expense ID to edit: ')
        if not eid_text.isdigit():
            print('Invalid ID')
            return
        eid = int(eid_text)
        exp = self.exp_mgr.find_expense(self.current_user.user_id, eid)
        if not exp:
            print('Expense not found')
            return
        amt_text = input(f'Amount [{exp.amount}]: ').strip()
        date_text = input(f'Date [{exp.date}]: ').strip()
        cat_text = input(f'Category [{exp.category}]: ').strip()
        desc_text = input(f'Description [{exp.description}]: ').strip()
        updates = {}
        if amt_text:
            amt = validate_amount(amt_text)
            if amt is None:
                print('Invalid amount.')
                return
            updates['amount'] = amt
        if date_text:
            if not validate_date(date_text):
                print('Invalid date.')
                return
            updates['date'] = date_text
        if cat_text:
            if cat_text not in VALID_CATEGORIES:
                print('Invalid category.')
                return
            updates['category'] = cat_text
        if desc_text:
            updates['description'] = desc_text
        self.exp_mgr.edit_expense(self.current_user.user_id, eid, **updates)
        print('Expense updated.')

    def cmd_delete(self):
        eid_text = input_nonempty('Expense ID to delete: ')
        if not eid_text.isdigit():
            print('Invalid ID')
            return
        eid = int(eid_text)
        confirm = input(f'Delete expense {eid}? (yes/no): ').strip().lower()
        if confirm in ('yes', 'y'):
            if self.exp_mgr.delete_expense(self.current_user.user_id, eid):
                print('Deleted.')
            else:
                print('Not found.')
        else:
            print('Aborted.')

    def _load_user_dataframe(self):
        exps = self.exp_mgr.list_user_expenses(self.current_user.user_id)
        if not exps:
            return pd.DataFrame()
        rows = [vars(e) for e in exps]
        df = pd.DataFrame(rows)
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = df['amount'].astype(float)
        return df

    def cmd_reports(self):
        df = self._load_user_dataframe()
        if df.empty:
            print('No expenses.')
            return
        df['month'] = df['date'].dt.to_period('M')
        print('\nTotal per month:')
        print(df.groupby('month')['amount'].sum())
        print('\nBy category:')
        print(df.groupby('category')['amount'].sum())

    def cmd_visualize(self):
        df = self._load_user_dataframe()
        if df.empty:
            print('No data to plot.')
            return
        df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
        monthly = df.groupby('month')['amount'].sum()
        cat = df.groupby('category')['amount'].sum()
        monthly.plot(kind='bar', title='Monthly Spending')
        plt.show()
        cat.plot(kind='pie', autopct='%1.1f%%', title='Category Distribution')
        plt.ylabel('')
        plt.show()

    def cmd_export(self):
        filename = f'export_{self.current_user.username}.csv'
        self.exp_mgr.export_user_expenses(self.current_user.user_id, filename)
        print(f'Exported to {filename}')


if __name__ == '__main__':
    CLIApp().run()

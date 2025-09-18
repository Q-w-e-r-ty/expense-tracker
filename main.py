# Expense Manager Application - Multiple files in one document
# Files included below: user.py, expense.py, main.py



# -------------------- main.py --------------------
"""
main.py
Command-line interface that uses UserManager and ExpenseManager.
"""

import sys
from getpass import getpass
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

from user import UserManager
from expense import ExpenseManager, CATEGORIES


PASSWORD_POLICY = {
    'min_len': 8,
    'uppercase': True,
    'lowercase': True,
    'digits': True,
}


def validate_password_strength(pw: str) -> bool:
    if len(pw) < PASSWORD_POLICY['min_len']:
        return False
    if PASSWORD_POLICY['uppercase'] and not any(c.isupper() for c in pw):
        return False
    if PASSWORD_POLICY['lowercase'] and not any(c.islower() for c in pw):
        return False
    if PASSWORD_POLICY['digits'] and not any(c.isdigit() for c in pw):
        return False
    return True


def main_menu():
    um = UserManager()
    em = ExpenseManager()

    while True:
        print('\n--- Personal Expense Manager ---')
        print('1. Login')
        print('2. Create Account')
        print('3. Exit')
        choice = input('Choose an option: ').strip()

        if choice == '1':
            username = input('Username: ').strip()
            password = getpass('Password: ')
            user = um.authenticate(username, password)
            if user:
                print(f'Login successful. Welcome, {user.username}!')
                transaction_menu(user, em)
            else:
                print('Invalid username or password.')

        elif choice == '2':
            username = input('Choose a username: ').strip()
            if um.get_user_by_username(username):
                print('Username already taken. Try another.')
                continue
            password = getpass('Choose a password: ')
            if not validate_password_strength(password):
                print('Password does not meet policy: min 8 chars, include uppercase, lowercase, and digit.')
                continue
            try:
                new_user = um.create_user(username, password)
                print(f'Account created. Your user id is {new_user.user_id}')
            except Exception as e:
                print('Failed to create account:', e)

        elif choice == '3':
            print('Goodbye!')
            sys.exit(0)
        else:
            print('Invalid choice.')


def transaction_menu(user, em: ExpenseManager):
    while True:
        print('\n--- Transactions ---')
        print('Commands: LIST, ADD, EDIT, DELETE, REPORTS, VISUALIZE, EXPORT, LOGOUT')
        cmd = input('Enter command: ').strip().upper()

        if cmd == 'LIST':
            exps = em.list_for_user(user.user_id)
            if not exps:
                print('No expenses found.')
            else:
                print(f"Expenses for {user.username} (user_id={user.user_id}):")
                print('{:>8} | {:>10} | {:>10} | {:>12} | {:<30}'.format('ID', 'Amount', 'Date', 'Category', 'Description'))
                print('-'*80)
                for e in exps:
                    print('{:>8} | {:>10} | {:>10} | {:>12} | {:<30}'.format(e.expense_id, f"{e.amount:.2f}", e.date, e.category, e.description[:30]))

        elif cmd == 'ADD':
            try:
                amount = float(input('Amount: ').strip())
                date = input('Date (YYYY-MM-DD): ').strip()
                # validate date
                datetime.strptime(date, '%Y-%m-%d')
                print('Choose category from:')
                for i, c in enumerate(CATEGORIES, 1):
                    print(f'{i}. {c}')
                cat_idx = int(input('Category number: ').strip())
                if not 1 <= cat_idx <= len(CATEGORIES):
                    print('Invalid category selection')
                    continue
                category = CATEGORIES[cat_idx-1]
                description = input('Description: ').strip()
                exp = em.add_expense(user.user_id, amount, date, category, description)
                print(f'Expense added with id {exp.expense_id}')
            except ValueError as ve:
                print('Invalid input:', ve)
            except Exception as e:
                print('Failed to add expense:', e)

        elif cmd == 'EDIT':
            exp_id = input('Enter expense_id to edit: ').strip()
            found = em.find_expense(user.user_id, exp_id)
            if not found:
                print('Expense not found')
                continue
            print('Leave a field empty to keep current value.')
            new_amount = input(f'Amount ({found.amount}): ').strip()
            new_date = input(f'Date ({found.date}): ').strip()
            print('Categories:')
            for i, c in enumerate(CATEGORIES, 1):
                print(f'{i}. {c}')
            new_cat = input(f'Category ({found.category}) number: ').strip()
            new_desc = input(f'Description ({found.description}): ').strip()
            kwargs = {}
            if new_amount:
                kwargs['amount'] = float(new_amount)
            if new_date:
                kwargs['date'] = new_date
            if new_cat:
                idx = int(new_cat)
                if not 1 <= idx <= len(CATEGORIES):
                    print('Invalid category index')
                    continue
                kwargs['category'] = CATEGORIES[idx-1]
            if new_desc:
                kwargs['description'] = new_desc
            try:
                em.edit_expense(user.user_id, exp_id, **kwargs)
                print('Expense updated.')
            except Exception as e:
                print('Failed to edit expense:', e)

        elif cmd == 'DELETE':
            exp_id = input('Enter expense_id to delete: ').strip()
            confirm = input(f'Are you sure you want to delete expense {exp_id}? (yes/no): ').strip().lower()
            if confirm != 'yes':
                print('Deletion cancelled')
                continue
            ok = em.delete_expense(user.user_id, exp_id)
            if ok:
                print('Deleted successfully')
            else:
                print('Expense not found')

        elif cmd == 'REPORTS':
            # Using pandas to create two reports
            exps = em.list_for_user(user.user_id)
            if not exps:
                print('No expenses to report.')
                continue
            df = pd.DataFrame([e.to_dict() for e in exps])
            df['amount'] = df['amount'].astype(float)
            df['date'] = pd.to_datetime(df['date'])
            # Total spending per month
            df['month'] = df['date'].dt.to_period('M')
            monthly = df.groupby('month')['amount'].sum().reset_index()
            monthly['month'] = monthly['month'].dt.strftime('%Y-%m')
            print('\nTotal spending per month:')
            print(monthly.to_string(index=False))
            # Category-wise distribution
            cat = df.groupby('category')['amount'].sum().reset_index()
            print('\nCategory-wise distribution:')
            print(cat.to_string(index=False))

        elif cmd == 'VISUALIZE':
            exps = em.list_for_user(user.user_id)
            if not exps:
                print('No expenses to visualize.')
                continue
            df = pd.DataFrame([e.to_dict() for e in exps])
            df['amount'] = df['amount'].astype(float)
            df['date'] = pd.to_datetime(df['date'])
            df['month'] = df['date'].dt.to_period('M')
            monthly = df.groupby('month')['amount'].sum().reset_index()
            monthly['month_str'] = monthly['month'].dt.strftime('%Y-%m')
            # Bar chart for monthly
            plt.figure()
            plt.bar(monthly['month_str'], monthly['amount'])
            plt.title('Monthly Spending')
            plt.xlabel('Month')
            plt.ylabel('Total Spending')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

            # Pie chart for categories
            cat = df.groupby('category')['amount'].sum()
            plt.figure()
            cat.plot.pie(autopct='%1.1f%%')
            plt.title('Category Distribution')
            plt.ylabel('')
            plt.tight_layout()
            plt.show()

        elif cmd == 'EXPORT':
            out = input('Output CSV filename (e.g., my_expenses.csv): ').strip()
            try:
                em.export_user_expenses(user.user_id, out)
                print(f'Exported to {out}')
            except Exception as e:
                print('Failed to export:', e)

        elif cmd == 'LOGOUT':
            print('Logged out')
            break

        else:
            print('Unknown command')


if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print('\nExiting...')
        sys.exit(0)

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
import os
import io
import csv

from user import UserManager
from expense import ExpenseManager, CATEGORIES
import pandas as pd
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret')

UM = UserManager()
EM = ExpenseManager()


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'warning')
            return redirect(url_for('login'))
        return fn(*args, **kwargs)

    return wrapper


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('expenses'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password required', 'danger')
            return redirect(url_for('register'))
        try:
            UM.create_user(username, password)
            flash('Account created, please login', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('register'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = UM.authenticate(username, password)
        if user:
            session['user_id'] = user.user_id
            session['username'] = user.username
            flash('Logged in', 'success')
            return redirect(url_for('expenses'))
        flash('Invalid credentials', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))


@app.route('/expenses')
@login_required
def expenses():
    user_id = session['user_id']
    exps = EM.list_for_user(user_id)
    return render_template('expenses.html', expenses=exps, categories=CATEGORIES)


@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        user_id = session['user_id']
        try:
            amount = float(request.form.get('amount', '0'))
            date = request.form.get('date', '')
            category = request.form.get('category', '')
            description = request.form.get('description', '')
            EM.add_expense(user_id, amount, date, category, description)
            flash('Expense added', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('add_expense'))
    return render_template('expense_form.html', categories=CATEGORIES, action='Add')


@app.route('/expenses/edit/<expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    user_id = session['user_id']
    found = EM.find_expense(user_id, expense_id)
    if not found:
        flash('Expense not found', 'warning')
        return redirect(url_for('expenses'))
    if request.method == 'POST':
        kwargs = {}
        amount = request.form.get('amount', '').strip()
        date = request.form.get('date', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        if amount:
            kwargs['amount'] = float(amount)
        if date:
            kwargs['date'] = date
        if category:
            kwargs['category'] = category
        if description:
            kwargs['description'] = description
        try:
            EM.edit_expense(user_id, expense_id, **kwargs)
            flash('Expense updated', 'success')
            return redirect(url_for('expenses'))
        except Exception as e:
            flash(str(e), 'danger')
            return redirect(url_for('edit_expense', expense_id=expense_id))
    return render_template('expense_form.html', expense=found, categories=CATEGORIES, action='Edit')


@app.route('/expenses/delete/<expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    user_id = session['user_id']
    ok = EM.delete_expense(user_id, expense_id)
    if ok:
        flash('Deleted', 'success')
    else:
        flash('Not found', 'warning')
    return redirect(url_for('expenses'))


@app.route('/expenses/export')
@login_required
def export_expenses():
    user_id = session['user_id']
    user_exp = EM.list_for_user(user_id)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['expense_id', 'user_id', 'amount', 'date', 'category', 'description'])
    writer.writeheader()
    for e in user_exp:
        writer.writerow(e.to_dict())
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     as_attachment=True,
                     download_name=f'expenses_user_{user_id}.csv',
                     mimetype='text/csv')


@app.route('/reports')
@login_required
def reports():
    user_id = session['user_id']
    exps = EM.list_for_user(user_id)
    if not exps:
        flash('No expenses to report', 'info')
        return redirect(url_for('expenses'))

    df = pd.DataFrame([e.to_dict() for e in exps])
    df['amount'] = df['amount'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly['month'] = monthly['month'].dt.strftime('%Y-%m')
    cat = df.groupby('category')['amount'].sum().reset_index()

    # convert dataframes to lists of dicts for rendering
    monthly_data = monthly.to_dict(orient='records')
    category_data = cat.to_dict(orient='records')

    return render_template('reports.html', monthly=monthly_data, categories=category_data)


def _plot_to_datauri(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    data = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/png;base64,{data}'


@app.route('/visualize')
@login_required
def visualize():
    user_id = session['user_id']
    exps = EM.list_for_user(user_id)
    if not exps:
        flash('No expenses to visualize', 'info')
        return redirect(url_for('expenses'))

    df = pd.DataFrame([e.to_dict() for e in exps])
    df['amount'] = df['amount'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    monthly = df.groupby('month')['amount'].sum().reset_index()
    monthly['month_str'] = monthly['month'].dt.strftime('%Y-%m')

    # monthly bar chart
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    ax1.bar(monthly['month_str'], monthly['amount'])
    ax1.set_title('Monthly Spending')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('Total Spending')
    plt.xticks(rotation=45)
    plt.tight_layout()
    monthly_uri = _plot_to_datauri(fig1)
    plt.close(fig1)

    # category pie chart
    cat = df.groupby('category')['amount'].sum()
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    cat.plot.pie(autopct='%1.1f%%', ax=ax2)
    ax2.set_title('Category Distribution')
    ax2.set_ylabel('')
    plt.tight_layout()
    category_uri = _plot_to_datauri(fig2)
    plt.close(fig2)

    return render_template('visualize.html', monthly_img=monthly_uri, category_img=category_uri)


if __name__ == '__main__':
    app.run(debug=True)

```markdown
# expense-tracker

This repository is a small personal expense tracker. I added a simple Flask web UI to the existing CLI code.

Run the application (recommended to use a virtualenv):

```powershell
pip install -r requirements.txt
$env:FLASK_APP = 'app.py'; $env:FLASK_ENV = 'development'
flask run
```

Open http://127.0.0.1:5000 in your browser.

Files added:
- `app.py` - Flask application and routes
- `templates/` - Jinja2 templates for the UI
- `requirements.txt` - Python dependencies

The app uses the existing `user.py` and `expense.py` for data management (CSV files created in the working dir).

Note: For production, set a secure `FLASK_SECRET_KEY` environment variable and disable debug mode.
```
# expense-tracker
# CCS Sit-in Monitoring System — Flask (Python)

## Setup & Run

```bash
# 1. Install dependencies
pip install flask

# 2. Run the app
python app.py

# 3. Open browser at:
http://127.0.0.1:5000
```

## Login Credentials

| Role    | ID       | Password |
|---------|----------|----------|
| Admin   | admin    | admin    |
| Student | 3677937  | pass123  |
| Student | 123456   | pass123  |

## Project Structure

```
ccs-flask/
├── app.py                  ← Main Flask application (all routes & logic)
├── requirements.txt
└── templates/
    ├── base.html           ← Shared layout (nav, alerts, styles)
    ├── login.html          ← Login page
    ├── register.html       ← Registration page
    ├── admin_nav.html      ← Admin navbar include
    ├── admin_dashboard.html← Admin home (stats chart + announcements)
    ├── student_list.html   ← Students table (add/edit/delete)
    ├── student_form.html   ← Add/Edit student form
    ├── sitin_form.html     ← Sit-in check-in form
    ├── sitin_records.html  ← Current sit-in records + checkout
    ├── search.html         ← Search students
    ├── reports.html        ← Sit-in reports
    ├── feedback.html       ← Feedback reports
    ├── reservation.html    ← Reservations
    └── student_dashboard.html ← Student portal
```

## To connect a real database (MySQL / SQLite)

Replace the in-memory lists in `app.py` with SQLAlchemy:

```bash
pip install flask-sqlalchemy
```

```python
from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@localhost/ccs_sitin'
db = SQLAlchemy(app)
```

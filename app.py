from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'ccs-sitin-secret-key-2026'

# ─── MySQL Configuration ───────────────────────────────────────────────────────
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sitin_db'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# ─── Helpers ───────────────────────────────────────────────────────────────────

def find_student(student_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
    student = cur.fetchone()
    cur.close()
    return student

def get_announcements():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM announcements ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    return rows

def next_sit_id():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM sitin_records")
    row = cur.fetchone()
    cur.close()
    return f"SIT-{(row['cnt'] + 1):04d}"

# ─── Admin decorator ───────────────────────────────────────────────────────────

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Student decorator ─────────────────────────────────────────────────────────

def student_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'student':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        sid = request.form.get('id_number', '').strip()
        pwd = request.form.get('password', '').strip()

        if sid == 'admin' and pwd == 'admin':
            session['user'] = 'admin'
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))

        student = find_student(sid)
        if student and student['password'] == pwd:
            session['user'] = sid
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))

        flash('Invalid ID number or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sid    = request.form.get('id_number', '').strip()
        last   = request.form.get('last_name', '').strip()
        first  = request.form.get('first_name', '').strip()
        middle = request.form.get('middle_name', '').strip()
        year   = int(request.form.get('year_level', 1))
        course = request.form.get('course', 'BSIT').strip()
        email  = request.form.get('email', '').strip()
        addr   = request.form.get('address', '').strip()
        pwd    = request.form.get('password', '').strip()
        pwd2   = request.form.get('repeat_password', '').strip()

        if find_student(sid):
            flash('ID Number already registered.', 'danger')
        elif pwd != pwd2:
            flash('Passwords do not match.', 'danger')
        elif not sid or not last or not first or not pwd:
            flash('Please fill all required fields.', 'danger')
        else:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO students (id, last, first, middle, year, course, email, address, session, password) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sid, last, first, middle, year, course, email, addr, 30, pwd))
            mysql.connection.commit()
            cur.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# ─── Admin routes ──────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.execute("SELECT * FROM sitin_records")
    sitin_records = cur.fetchall()
    cur.close()

    currently = [r for r in sitin_records if r['status'] == 'Active']
    stats = {}
    for r in sitin_records:
        stats[r['purpose']] = stats.get(r['purpose'], 0) + 1

    return render_template('admin_dashboard.html',
        students=students,
        sitin_records=sitin_records,
        announcements=get_announcements(),
        currently_sitin=len(currently),
        total_sitin=len(sitin_records),
        stats=json.dumps(stats)
    )

@app.route('/admin/announce', methods=['POST'])
@admin_required
def post_announcement():
    body = request.form.get('body', '').strip()
    if body:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO announcements (author, date, body) VALUES (%s,%s,%s)",
            ("CCS Admin", datetime.now().strftime("%Y-%b-%d"), body))
        mysql.connection.commit()
        cur.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/students')
@admin_required
def student_list():
    q = request.args.get('q', '').lower()
    cur = mysql.connection.cursor()
    if q:
        cur.execute("SELECT * FROM students WHERE LOWER(id) LIKE %s OR LOWER(CONCAT(first,' ',last)) LIKE %s",
            (f'%{q}%', f'%{q}%'))
    else:
        cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    return render_template('student_list.html', students=students, query=q, announcements=get_announcements())

@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    if request.method == 'POST':
        sid = request.form.get('id_number', '').strip()
        if find_student(sid):
            flash('ID already exists.', 'danger')
        else:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO students (id, last, first, middle, year, course, email, address, session, password) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (sid,
                 request.form.get('last_name','').strip(),
                 request.form.get('first_name','').strip(),
                 request.form.get('middle_name','').strip(),
                 int(request.form.get('year_level', 1)),
                 request.form.get('course','BSIT').strip(),
                 request.form.get('email','').strip(),
                 request.form.get('address','').strip(),
                 int(request.form.get('session', 30)),
                 request.form.get('password','pass123').strip()))
            mysql.connection.commit()
            cur.close()
            flash('Student added.', 'success')
            return redirect(url_for('student_list'))
    return render_template('student_form.html', student=None, announcements=get_announcements())

@app.route('/admin/students/edit/<sid>', methods=['GET', 'POST'])
@admin_required
def edit_student(sid):
    student = find_student(sid)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('student_list'))
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("UPDATE students SET last=%s, first=%s, middle=%s, year=%s, course=%s, email=%s, address=%s, session=%s WHERE id=%s",
            (request.form.get('last_name','').strip(),
             request.form.get('first_name','').strip(),
             request.form.get('middle_name','').strip(),
             int(request.form.get('year_level', 1)),
             request.form.get('course','BSIT').strip(),
             request.form.get('email','').strip(),
             request.form.get('address','').strip(),
             int(request.form.get('session', 30)),
             sid))
        mysql.connection.commit()
        cur.close()
        flash('Student updated.', 'success')
        return redirect(url_for('student_list'))
    return render_template('student_form.html', student=student, announcements=get_announcements())

@app.route('/admin/students/delete/<sid>', methods=['POST'])
@admin_required
def delete_student(sid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM students WHERE id = %s", (sid,))
    mysql.connection.commit()
    cur.close()
    flash('Student deleted.', 'success')
    return redirect(url_for('student_list'))

@app.route('/admin/students/reset-sessions', methods=['POST'])
@admin_required
def reset_sessions():
    cur = mysql.connection.cursor()
    cur.execute("UPDATE students SET session = 30")
    mysql.connection.commit()
    cur.close()
    flash('All sessions reset to 30.', 'success')
    return redirect(url_for('student_list'))

@app.route('/admin/sitin')
@admin_required
def current_sitin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sitin_records WHERE status = 'Active'")
    active = cur.fetchall()
    cur.close()
    return render_template('sitin_records.html', records=active, announcements=get_announcements())

@app.route('/admin/sitin/form', methods=['GET', 'POST'])
@admin_required
def sitin_form():
    sid = request.args.get('id', '')
    student = find_student(sid)
    if request.method == 'POST':
        sid2 = request.form.get('id_number', '').strip()
        student2 = find_student(sid2)
        if not student2:
            flash('Student not found.', 'danger')
            return redirect(url_for('sitin_form'))
        sit_id = next_sit_id()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sitin_records (sit_id, student_id, name, purpose, lab, session, status, date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (sit_id, sid2,
             f"{student2['first']} {student2['last']}",
             request.form.get('purpose','').strip(),
             request.form.get('lab','').strip(),
             student2['session'],
             'Active',
             datetime.now().strftime("%Y-%m-%d %H:%M")))
        cur.execute("UPDATE students SET session = GREATEST(0, session - 1) WHERE id = %s", (sid2,))
        mysql.connection.commit()
        cur.close()
        flash(f"{student2['first']} {student2['last']} checked in successfully!", 'success')
        return redirect(url_for('current_sitin'))
    return render_template('sitin_form.html', student=student, announcements=get_announcements())

@app.route('/admin/sitin/checkout/<sit_id>', methods=['POST'])
@admin_required
def checkout(sit_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE sitin_records SET status = 'Done' WHERE sit_id = %s", (sit_id,))
    mysql.connection.commit()
    cur.close()
    flash('Student checked out.', 'success')
    return redirect(url_for('current_sitin'))


@app.route('/admin/sitin/approve/<sit_id>', methods=['POST'])
@admin_required
def approve_sitin(sit_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE sitin_records SET status='Active' WHERE sit_id=%s", (sit_id,))
    mysql.connection.commit()
    cur.close()
    flash('Sit-in approved!', 'success')
    return redirect(url_for('lab_dashboard'))


@app.route('/admin/sitin/reject/<sit_id>', methods=['POST'])
@admin_required
def reject_sitin(sit_id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE sitin_records SET status='Rejected' WHERE sit_id=%s", (sit_id,))
    mysql.connection.commit()
    cur.close()
    flash('Sit-in rejected.', 'danger')
    return redirect(url_for('lab_dashboard'))

@app.route('/admin/search')
@admin_required
def search_student():
    q = request.args.get('q', '').lower()
    results = []
    if q:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM students WHERE LOWER(id) LIKE %s OR LOWER(CONCAT(first,' ',last)) LIKE %s",
            (f'%{q}%', f'%{q}%'))
        results = cur.fetchall()
        cur.close()
    return render_template('search.html', results=results, query=q, announcements=get_announcements())

@app.route('/admin/reports')
@admin_required
def sitin_reports():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM sitin_records")
    records = cur.fetchall()
    cur.close()
    return render_template('reports.html', records=records, announcements=get_announcements())

@app.route('/admin/lab')
@admin_required
def lab_dashboard():
    cur = mysql.connection.cursor()

    # Active PCs / sit-in
    cur.execute("SELECT * FROM sitin_records WHERE status='Active'")
    active = cur.fetchall()

    # Pending requests
    cur.execute("SELECT * FROM sitin_records WHERE status='Pending'")
    pending = cur.fetchall()

    # Logs
    cur.execute("SELECT * FROM sitin_records ORDER BY date DESC LIMIT 20")
    logs = cur.fetchall()

    cur.close()

    return render_template('lab_dashboard.html',
        active=active,
        pending=pending,
        logs=logs,
        announcements=get_announcements()
    )

@app.route('/admin/feedback')
@admin_required
def feedback_reports():
    return render_template('feedback.html', announcements=get_announcements())

@app.route('/admin/reservation')
@admin_required
def reservation():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM reservations ORDER BY id DESC")
    reservations = cur.fetchall()
    cur.close()
    return render_template('reservation.html', reservations=reservations, announcements=get_announcements())

@app.route('/admin/reservation/add', methods=['POST'])
@admin_required
def add_reservation():
    sid = request.form.get('student_id', '').strip()
    student = find_student(sid)
    name = f"{student['first']} {student['last']}" if student else "Unknown"
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO reservations (student_id, name, lab, purpose, date, time, status) VALUES (%s,%s,%s,%s,%s,%s,'Pending')",
        (sid, name, request.form.get('lab'), request.form.get('purpose'),
         request.form.get('date'), request.form.get('time')))
    mysql.connection.commit()
    cur.close()
    flash('Reservation added!', 'success')
    return redirect(url_for('reservation'))

@app.route('/admin/reservation/approve/<int:rid>', methods=['POST'])
@admin_required
def approve_reservation(rid):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE reservations SET status='Approved' WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    flash('Reservation approved!', 'success')
    return redirect(url_for('reservation'))

@app.route('/admin/reservation/reject/<int:rid>', methods=['POST'])
@admin_required
def reject_reservation(rid):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE reservations SET status='Rejected' WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    flash('Reservation rejected.', 'success')
    return redirect(url_for('reservation'))

@app.route('/admin/reservation/delete/<int:rid>', methods=['POST'])
@admin_required
def delete_reservation(rid):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM reservations WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    flash('Reservation deleted.', 'success')
    return redirect(url_for('reservation'))

# ─── Student routes ────────────────────────────────────────────────────────────

@app.route('/student')
@student_required
def student_dashboard():
    student = find_student(session['user'])
    cur = mysql.connection.cursor()

    # Sit-in records
    cur.execute("SELECT * FROM sitin_records WHERE student_id = %s", (session['user'],))
    my_records = cur.fetchall()

    # Reservations
    cur.execute("SELECT * FROM reservations WHERE student_id = %s ORDER BY id DESC", (session['user'],))
    my_reservations = cur.fetchall()
    cur.close()

    # Build notifications
    notifications = []
    for r in my_records:
        if r['status'] == 'Active':
            notifications.append({
                'type': 'approved',
                'title': 'Sit-in Approved',
                'message': f"Your sit-in at {r['lab']} has been approved.",
                'date': r['date'],
                'is_read': False
            })
        elif r['status'] == 'Done':
            notifications.append({
                'type': 'done',
                'title': 'Sit-in Completed',
                'message': f"Your sit-in session at {r['lab']} is done.",
                'date': r['date'],
                'is_read': True
            })
    for r in my_reservations:
        if r['status'] == 'Approved':
            notifications.append({
                'type': 'approved',
                'title': 'Reservation Approved',
                'message': f"Your reservation for {r['lab']} on {r['date']} at {r['time']} is approved!",
                'date': r['date'],
                'is_read': False
            })
        elif r['status'] == 'Rejected':
            notifications.append({
                'type': 'rejected',
                'title': 'Reservation Rejected',
                'message': f"Your reservation for {r['lab']} on {r['date']} was rejected.",
                'date': r['date'],
                'is_read': False
            })

    return render_template('student_dashboard.html',
        student=student,
        announcements=get_announcements(),
        records=my_records,
        my_reservations=my_reservations,
        notifications=notifications)

@app.route('/student/sitin', methods=['POST'])
@student_required
def student_sitin_request():
    student = find_student(session['user'])
    if student and student['session'] > 0:
        sit_id = next_sit_id()
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO sitin_records (sit_id, student_id, name, purpose, lab, session, status, date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (sit_id, student['id'],
             f"{student['first']} {student['last']}",
             request.form.get('purpose','').strip(),
             request.form.get('lab','').strip(),
             student['session'],
             'Pending',
             datetime.now().strftime("%Y-%m-%d %H:%M")))
        mysql.connection.commit()
        cur.close()
        flash('Sit-in request submitted! Waiting for admin approval.', 'success')
    else:
        flash('No remaining sessions.', 'danger')
    return redirect(url_for('student_dashboard'))

@app.route('/student/reservation/add', methods=['POST'])
@student_required
def student_add_reservation():
    student = find_student(session['user'])
    name = f"{student['first']} {student['last']}"
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO reservations (student_id, name, lab, purpose, date, time, status) VALUES (%s,%s,%s,%s,%s,%s,'Pending')",
        (student['id'], name,
         request.form.get('lab'),
         request.form.get('purpose'),
         request.form.get('date'),
         request.form.get('time')))
    mysql.connection.commit()
    cur.close()
    flash('Reservation submitted! Waiting for admin approval.', 'success')
    return redirect(url_for('student_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
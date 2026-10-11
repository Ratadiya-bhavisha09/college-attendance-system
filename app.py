from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            status TEXT,
            date TEXT
        )
    ''')
    
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('teacher1', '1234', 'teacher')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('student1', '1234', 'student')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('rahul', '1234', 'student')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('priya', '1234', 'student')")
        conn.commit()
    except sqlite3.IntegrityError:
        pass
        
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = ?", (username, password, role))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            if role == 'teacher':
                return redirect(url_for('teacher_dashboard', username=username))
            else:
                return redirect(url_for('student_dashboard', username=username)) # Yeh line update karni hai
            
    return render_template('login.html', error=error)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    username = request.args.get('username', 'Teacher')
    return render_template('teacher_dashboard.html', username=username)


@app.route('/student_dashboard')
def student_dashboard():
    username = request.args.get('username', 'Student')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    student = cursor.fetchone()
    
    attendance_records = []
    total_classes = 0
    present_count = 0
    percentage = 0
    
    if student:
        student_id = student[0]
        cursor.execute("SELECT date, status FROM attendance WHERE student_id = ? ORDER BY date DESC", (student_id,))
        attendance_records = cursor.fetchall()
        
        total_classes = len(attendance_records)
        if total_classes > 0:
            present_count = sum(1 for record in attendance_records if record[1] == 'Present')
            percentage = round((present_count / total_classes) * 100, 2)
        
    conn.close()
    
    return render_template('student_dashboard.html', 
                           username=username, 
                           records=attendance_records,
                           total_classes=total_classes,
                           present_count=present_count,
                           percentage=percentage)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'student'
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            conn.commit()
            msg = "Student added successfully!"
        except sqlite3.IntegrityError:
            msg = "Username already exists!"
        conn.close()
        
        return f"<h2 style='text-align:center; color:green; margin-top:50px;'>{msg} <br><br><a href='/teacher_dashboard'>Go to Dashboard</a></h2>"
        
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Add Student</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); height: 100vh; display: flex; align-items: center; justify-content: center;">
        <div class="card shadow p-4" style="width: 400px; border-radius: 12px;">
            <h3 class="text-center mb-4 text-primary">Add New Student</h3>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Student Username</label>
                    <input type="text" name="username" class="form-control" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <input type="password" name="password" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100">Add Student</button>
            </form>
            <div class="text-center mt-3">
                <a href="/teacher_dashboard" class="text-decoration-none">Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/take_attendance', methods=['GET', 'POST'])
def take_attendance():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        # Yahan par purani entry delete kar do taaki duplicate na bane
        cursor.execute("DELETE FROM attendance WHERE date = ?", (today_date,))
        
        cursor.execute("SELECT id FROM users WHERE role = 'student'")
        students = cursor.fetchall()
        
        for student in students:
            student_id = student[0]
            status = request.form.get(f'status_{student_id}')
            if status:
                cursor.execute("INSERT INTO attendance (student_id, status, date) VALUES (?, ?, ?)", 
                               (student_id, status, today_date))
        
        conn.commit()
        conn.close()
        return "<h2 style='text-align:center; color:green; margin-top:50px;'>Attendance Saved Successfully! <br><br><a href='/teacher_dashboard'>Go to Dashboard</a></h2>"    
    cursor.execute("SELECT * FROM users WHERE role = 'student'")
    students = cursor.fetchall()
    conn.close()
    
    return render_template('take_attendance.html', students=students)

@app.route('/view_reports')
def view_reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT attendance.date, users.username, attendance.status FROM attendance JOIN users ON attendance.student_id = users.id ORDER BY attendance.date DESC")
    reports = cursor.fetchall()
    conn.close()
    return render_template('view_reports.html', reports=reports)

if __name__ == '__main__':
    app.run(debug=True)
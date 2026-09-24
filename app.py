
from flask import Flask, render_template, request, redirect, Response, flash, session, url_for
from werkzeug.utils import secure_filename
import os
import sqlite3

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.secret_key = "student_management_secret"


# Create database and table
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            course TEXT NOT NULL
        )
    """)

    try:
        cursor.execute("ALTER TABLE students ADD COLUMN photo TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE students ADD COLUMN cgpa REAL")
    except:
      pass
    

    conn.commit()
    conn.close()
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":

            session['admin'] = True

            flash("Login Successful!", "success")

            return redirect('/')

        else:

            flash("Invalid Username or Password!", "danger")

    return render_template('login.html') 
@app.route('/logout')
def logout():

    session.pop('admin', None)

    flash("Logged out successfully!", "info")

    return redirect('/login')   

  

# Home Page
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'admin' not in session:
      return redirect('/login')
     

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    search_result = None

    if request.method == 'POST':

        if 'search' in request.form:

            search_text = request.form['search']

            cursor.execute(
                """
                SELECT * FROM students
                WHERE id=? OR name LIKE ?
                """,
                (search_text, f"%{search_text}%")
            )

            search_result = cursor.fetchall()

        else:

            student_id = request.form['id']
            name = request.form['name']
            course = request.form['course']
            cgpa = request.form['cgpa']

            photo = request.files['photo']

            filename = ""

            if photo and photo.filename != "":
                filename = secure_filename(photo.filename)

                photo.save(
                    os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        filename
                    )
                )

            try:


                cursor.execute(
    "INSERT INTO students (id, name, course, photo, cgpa) VALUES (?, ?, ?, ?, ?)",
    (student_id, name, course, filename, cgpa)
)

                conn.commit()
                flash("Student added successfully!", "success")

            except sqlite3.IntegrityError:
                flash("Student ID already exists!", "danger")

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT course) FROM students")
    total_courses = cursor.fetchone()[0]

    cursor.execute("""
        SELECT course, COUNT(*)
        FROM students
        GROUP BY course
    """)
    course_stats = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        students=students,
        search_result=search_result,
        total_students=total_students,
        total_courses=total_courses,
        course_stats=course_stats
    )
@app.route('/delete/<string:id>')
def delete_student(id):

    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    

    cursor.execute("DELETE FROM students WHERE id=?", (id,))

    conn.commit()
    conn.close()

    flash("Student deleted successfully!", "warning")
    return redirect('/')

@app.route('/export')
def export_csv():

    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()


    csv_data = "ID,Name,Course,CGPA\n"

    for student in students:
        csv_data += f"{student[0]},{student[1]},{student[2]},{student[4]}\n"
        

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )

@app.route('/update/<string:id>', methods=['GET', 'POST'])
def update_student(id):

    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    

    if request.method == 'POST':
        name = request.form['name']
        course = request.form['course']
        cgpa = request.form['cgpa']

        cursor.execute(
            "UPDATE students SET name=?, course=?, cgpa=? WHERE id=?",
            (name, course, cgpa, id)
        )

        conn.commit()
        conn.close()

        flash("Student updated successfully!", "info")
        return redirect('/')

    cursor.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cursor.fetchone()

    conn.close()

    return render_template("update.html", student=student)




# ADD THIS HERE
@app.route('/idcard/<string:id>')
def id_card(id):

    if 'admin' not in session:
        return redirect('/login')

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (id,))
    student = cursor.fetchone()

    conn.close()

    return render_template("idcard.html", student=student)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


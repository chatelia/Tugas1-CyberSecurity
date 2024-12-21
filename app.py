from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import bleach
import sqlite3
import bcrypt
import secrets
import re  # ------ NO 3 ------


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16) # ------ NO 1 ------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------ NO 1 ------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'

# ------ NO 1 ------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        # Check if user exists and password matches
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# ------ NO 1 ------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        # ------ NO 2 ------
        username = bleach.clean(request.form['username'])  
        password = request.form['password']
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt())

        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username,
                        password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# ------ NO 1 ------
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)  # Remove user from session
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# # ------ NO 3 ------
def validate_input(name, age, grade):
    if not name or not name.strip():
        return False, "Name cannot be empty or whitespace"

    if re.search(r"['\";=%]+", name):
        return False, "Name contains invalid characters"

    try:
        age = int(age) 
        if age < 1 or age > 120:
            return False, "Age must be a valid number between 1 and 120"
    except ValueError:
        return False, "Age must be a valid number"

    valid_grades = ['A', 'B', 'C', 'D', 'E', 'F']
    if grade not in valid_grades:
        return False, f"Grade must be one of {','.join(valid_grades)}"

    return True, None


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)


@app.route('/add', methods=['POST'])
def add_student():
    # name = request.form['name']
    # age = request.form['age']
    # grade = request.form['grade']

    # ------ NO 2 ------
    name = bleach.clean(request.form['name'])
    age = int(request.form['age'])
    grade = bleach.clean(request.form['grade'])

    # # ------ NO 3 ------
    is_valid, error_message = validate_input(name, age, grade)
    if not is_valid:
            return error_message, 400

    connection = sqlite3.connect('instance/students.db')
    cursor = connection.cursor()

    # RAW Query
    # db.session.execute(
    #     text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
    #     {'name': name, 'age': age, 'grade': grade}
    # )
    # db.session.commit()

    # query = f"INSERT INTO student (name, age, grade) VALUES ('{name}', {age}, '{grade}')"
    # cursor.execute(query)
    # connection.commit()
    # connection.close()
    # # ------ NO 3 ------
    new_student = Student(name=name, age=int(age), grade=grade)
    db.session.add(new_student)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<string:id>')
def delete_student(id):
    # # ------ NO 3 ------
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    # # RAW Query
    # db.session.execute(text(f"DELETE FROM student WHERE id={id}"))
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    # ------ NO 3 ------
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        # ------ NO 2 ------
        name = bleach.clean(request.form['name'])  
        age = request.form['age']
        grade = bleach.clean(request.form['grade']) 

        # name = request.form['name']
        # age = request.form['age']
        # grade = request.form['grade']


        # # ------ NO 3 ------
        is_valid, error_message = validate_input(name, age, grade)
        if not is_valid:
              return error_message, 400

        # # RAW Query
        # db.session.execute(text(
        #     f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        # # ------ NO 3 ------
        student.name = name
        student.age = int(age)
        student.grade = grade

        db.session.commit()
        return redirect(url_for('index'))
    # else:
    #     # # RAW Query
    #     # student = db.session.execute(
    #     #     text(f"SELECT * FROM student WHERE id={id}")).fetchone()
    return render_template('edit.html', student=student)


# if __name__ == '__main__':
#     with app.app_context():
#         db.create_all()
#     app.run(debug=True)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=False)

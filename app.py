#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'   # ⚠️ change in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db?check_same_thread=False'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------------
# Models
# ----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    todos = db.relationship('Todo', backref='owner', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('todo'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    if request.method == "POST":
        task = request.form['task']
        new_task = Todo(task=task, owner=current_user)
        db.session.add(new_task)
        db.session.commit()
    tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('todo.html', tasks=tasks)

@app.route('/complete/<int:task_id>')
@login_required
def complete(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.owner != current_user:
        flash("Not authorized to update this task")
        return redirect(url_for('todo'))
    task.completed = True
    db.session.commit()
    return redirect(url_for('todo'))

@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Todo.query.get_or_404(task_id)
    if task.owner != current_user:
        flash("Not authorized to delete this task")
        return redirect(url_for('todo'))
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('todo'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ----------------------
# Ensure database exists
# ----------------------
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'todo.db')

try:
    if not os.path.exists(db_path):
        with app.app_context():
            db.create_all()
        print(f"Database created at {db_path}")
except Exception as e:
    print(f"Error creating database: {e}")

# ----------------------
# Run locally
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)

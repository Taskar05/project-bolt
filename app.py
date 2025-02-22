from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os
from functools import wraps
import re
import random
import smtplib

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Admin credentials (in production, use environment variables and proper password hashing)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# USDT Rate
USDT_RATE = 92.30

# Database initialization
def init_db():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            verified INTEGER DEFAULT 0,
            verification_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            wallet_address TEXT NOT NULL,
            amount REAL NOT NULL,
            pkr_amount REAL NOT NULL,
            email TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper function to send verification email
def send_verification_email(email, code):
    sender_email = "your-email@gmail.com"
    sender_password = "your-email-password"
    subject = "Email Verification Code"
    body = f"Your verification code is: {code}"
    message = f"Subject: {subject}\n\n{body}"
    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message)

# Login required decorator for clients
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin login required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('dashboard.html', usdt_rate=USDT_RATE)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        verification_code = str(random.randint(100000, 999999))

        try:
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (name, email, password, phone, verification_code) VALUES (?, ?, ?, ?, ?)',
                     (name, email, password, phone, verification_code))
            conn.commit()
            conn.close()
            send_verification_email(email, verification_code)
            flash('Registration successful! Please check your email for the verification code.', 'success')
            return redirect(url_for('verify_email'))
        except sqlite3.IntegrityError:
            flash('Email or phone number already exists', 'error')
    return render_template('register.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')
        
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('SELECT verification_code FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        
        if user and user[0] == code:
            c.execute('UPDATE users SET verified = 1 WHERE email = ?', (email,))
            conn.commit()
            conn.close()
            flash('Email verified! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid verification code', 'error')
    return render_template('verify_email.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('SELECT id, name, email, verified FROM users WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            if user[3] == 0:
                flash('Please verify your email before logging in.', 'error')
                return redirect(url_for('verify_email'))
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_email'] = user[2]
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('orders.db')
    c = conn.cursor()
    c.execute('SELECT id, name, email, phone, verified FROM users ORDER BY created_at DESC')
    users = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)


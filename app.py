from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
from datetime import datetime
import os
from functools import wraps
import re

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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
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
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')

        # Basic validation
        if not all([email, password, phone]):
            flash('All fields are required', 'error')
            return render_template('register.html')

        # Validate phone number (simple validation)
        if not re.match(r'^\+?1?\d{9,15}$', phone):
            flash('Invalid phone number format', 'error')
            return render_template('register.html')

        try:
            conn = sqlite3.connect('orders.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (email, password, phone) VALUES (?, ?, ?)',
                     (email, password, phone))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email or phone number already exists', 'error')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('SELECT id, email FROM users WHERE email = ? AND password = ?',
                 (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_email'] = user[1]
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    return redirect(url_for('login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.json
        wallet_address = data.get('wallet_address')
        amount = float(data.get('amount'))
        email = session['user_email']
        user_id = session['user_id']

        if not all([wallet_address, amount]) or amount <= 0:
            return jsonify({'error': 'Invalid input data'}), 400

        pkr_amount = amount * USDT_RATE

        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO orders (user_id, wallet_address, amount, pkr_amount, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, wallet_address, amount, pkr_amount, email))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Order created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        
        if 'admin_logged_in' in session:
            c.execute('''
                SELECT o.*, u.phone 
                FROM orders o 
                JOIN users u ON o.user_id = u.id 
                ORDER BY o.created_at DESC
            ''')
        else:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401
            c.execute('''
                SELECT * FROM orders 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (user_id,))
        
        orders = c.fetchall()
        conn.close()

        orders_list = []
        for order in orders:
            order_dict = {
                'id': order[0],
                'user_id': order[1],
                'wallet_address': order[2],
                'amount': order[3],
                'pkr_amount': order[4],
                'email': order[5],
                'status': order[6],
                'created_at': order[7]
            }
            if 'admin_logged_in' in session:
                order_dict['phone'] = order[8]
            orders_list.append(order_dict)

        return jsonify(orders_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        if new_status not in ['pending', 'completed', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400

        conn = sqlite3.connect('orders.db')
        c = conn.cursor()
        c.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': 'Order status updated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
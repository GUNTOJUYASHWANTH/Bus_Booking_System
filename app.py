from flask import Flask, render_template, request, redirect, url_for, session, flash
from db_config import connect_db

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ---------- HOME ----------
@app.route('/')
def home():
    return render_template('index.html')

# ---------- USER REGISTRATION ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = connect_db()
        cursor = conn.cursor()
        username = request.form['username']
        password = request.form['password']
        phone = request.form['phone']
        cursor.execute("INSERT INTO users (username, password, phone) VALUES (%s, %s, %s)", (username, password, phone))
        conn.commit()
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------- USER LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            flash("Login successful!", "success")
            return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

# ---------- USER DASHBOARD ----------
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'])

# ---------- VIEW BUSES ----------
@app.route('/view_buses')
def view_buses():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM buses")
    buses = cursor.fetchall()
    return render_template('view_buses.html', buses=buses)

# ---------- BOOK TICKET ----------
@app.route('/book_ticket', methods=['GET', 'POST'])
def book_ticket_page():
    if request.method == 'POST':
        bus_id = request.form['bus_id']
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        user_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO passengers (user_id, name, age, gender, bus_id) VALUES (%s, %s, %s, %s, %s)", (user_id, name, age, gender, bus_id))
        conn.commit()
        passenger_id = cursor.lastrowid
        flash("Ticket booked successfully!", "success")
        return redirect(url_for('view_ticket', passenger_id=passenger_id))
    return render_template('book_ticket.html')

# ---------- VIEW TICKET ----------
@app.route('/ticket/<int:passenger_id>')
def view_ticket(passenger_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.bus_name, b.source, b.destination, b.price, u.username
        FROM passengers p
        JOIN buses b ON p.bus_id = b.bus_id
        JOIN users u ON p.user_id = u.user_id
        WHERE p.passenger_id = %s AND p.user_id = %s
    """, (passenger_id, session['user_id']))
    ticket = cursor.fetchone()
    if not ticket:
        flash("Ticket not found or access denied.", "danger")
        return redirect(url_for('user_dashboard'))
    return render_template('ticket.html', ticket=ticket)

# ---------- CANCEL TICKET ----------
@app.route('/cancel_ticket', methods=['GET', 'POST'])
def cancel_ticket_page():
    if request.method == 'POST':
        passenger_id = request.form['passenger_id']
        user_id = session['user_id']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passengers WHERE passenger_id = %s AND user_id = %s", (passenger_id, user_id))
        conn.commit()
        flash("Ticket canceled!" if cursor.rowcount > 0 else "Ticket not found or not yours!", "info")
        return redirect(url_for('user_dashboard'))
    return render_template('cancel_ticket.html')

# ---------- WALLET ----------
@app.route('/wallet', methods=['GET', 'POST'])
def wallet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        amount = float(request.form['amount'])
        cursor.execute("UPDATE users SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
        conn.commit()
        flash("Money added successfully!", "success")
        return redirect(url_for('wallet'))
    cursor.execute("SELECT balance FROM users WHERE user_id = %s", (user_id,))
    balance = cursor.fetchone()['balance']
    return render_template('wallet.html', balance=balance)

# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

# =================== ADMIN SECTION ===================

# ---------- ADMIN LOGIN ----------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['admin'] = True
            flash("Admin login successful!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid admin credentials", "danger")
    return render_template('admin_login.html')

# ---------- ADMIN DASHBOARD ----------
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

# ---------- ADD BUS ----------
@app.route('/admin/add_bus', methods=['GET', 'POST'])
def add_bus():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        bus_name = request.form['bus_name']
        source = request.form['source']
        destination = request.form['destination']
        price = request.form['price']
        seats_available = request.form['seats_available']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO buses (bus_name, source, destination, price, seats_available) VALUES (%s, %s, %s, %s, %s)",
                       (bus_name, source, destination, price, seats_available))
        conn.commit()
        flash("✅ Bus added successfully!", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('add_bus.html')

# ---------- VIEW USERS ----------
@app.route('/admin/view_users')
def view_users():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    return render_template('view_users.html', users=users)

# ---------- VIEW BOOKINGS ----------
@app.route('/admin/view_bookings')
def view_bookings():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.passenger_id, u.username, b.bus_name
        FROM passengers p
        JOIN users u ON p.user_id = u.user_id
        JOIN buses b ON p.bus_id = b.bus_id
    """)
    bookings = cursor.fetchall()
    return render_template('view_bookings.html', bookings=bookings)

# ---------- ADMIN LOGOUT ----------
@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("🔐 Admin logged out.", "info")
    return redirect(url_for('home'))

# ---------- MAIN ----------
if __name__ == '__main__':
    app.run(debug=True)

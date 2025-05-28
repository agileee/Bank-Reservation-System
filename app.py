from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'bankdb'

mysql = MySQL(app)

# -------------------- Home --------------------

@app.route('/')
def home():
    return render_template('index.html')

# -------------------- Login --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM clients WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and user['password'] == password:
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))

    return render_template("login.html")

# -------------------- Register --------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        pin = request.form['pin']
        account_number = str(random.randint(1000000000, 9999999999))

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM clients WHERE email = %s", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash('Email already registered. Please login.', 'warning')
            cur.close()
            return redirect(url_for('login'))

        cur.execute("""
            INSERT INTO clients (username, email, password, transaction_pin, account_number)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, email, password, pin, account_number))
        mysql.connection.commit()
        cur.close()

        session['email'] = email
        return redirect(url_for('dashboard'))

    return render_template('register.html')

# -------------------- Dashboard --------------------

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))

    return render_template('dashboard.html', email=session['email'])

# -------------------- Logout --------------------

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# -------------------- Loan Section --------------------

@app.route('/loan')
def loan_section():
    if 'email' not in session:
        flash('Please log in to access the loan section.', 'warning')
        return redirect(url_for('login'))

    return redirect(url_for('loan_form'))

@app.route('/loan/apply')
def loan_form():
    if 'email' not in session:
        flash('Please log in to apply for a loan.', 'warning')
        return redirect(url_for('login'))

    return render_template('loan.html')

@app.route('/loan/submit', methods=['POST'])
def apply_loan():
    if 'email' not in session:
        flash('Please log in to submit a loan.', 'warning')
        return redirect(url_for('login'))

    email = session['email']
    name = request.form['name']
    loan_type = request.form['loan_type']
    amount = request.form['amount']
    duration = request.form['duration']
    purpose = request.form['purpose']

    # Save to database
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO loans (email, name, loan_type, amount, duration, purpose)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (email, name, loan_type, amount, duration, purpose))
    mysql.connection.commit()
    cur.close()

    return f"""
    <h3>Thank you, {name}!</h3>
    <p>Your application for a <strong>{loan_type}</strong> loan of <strong>${amount}</strong> for <strong>{duration} months</strong> has been submitted.</p>
    <p><strong>Purpose:</strong> {purpose}</p>
    <a href="/dashboard">Back to Dashboard</a>
    """

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'email' not in session:
        flash('Please log in to make a deposit.', 'warning')
        return redirect(url_for('login'))

    email = session['email']

    if request.method == 'POST':
        amount = request.form['amount']
        method = request.form['method']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO deposits (email, amount, method) VALUES (%s, %s, %s)", 
                    (email, amount, method))
        mysql.connection.commit()
        cur.close()

        flash(f'Deposited ₹{amount} successfully!', 'success')
        return redirect(url_for('deposit'))  # Reload to show updated history

    # Fetch deposit history
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT amount, method, deposit_time FROM deposits WHERE email = %s ORDER BY deposit_time DESC", (email,))
    deposit_history = cur.fetchall()
    cur.close()

    return render_template('deposit.html', deposit_history=deposit_history)


@app.route('/transaction', methods=['GET', 'POST'])
def transaction():
    if 'email' not in session:
        flash('Please log in to make a transaction.', 'warning')
        return redirect(url_for('login'))

    email = session['email']

    if request.method == 'POST':
        receiver = request.form['receiver']
        amount = request.form['amount']
        pin = request.form['pin']

        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be greater than 0.", "danger")
                return redirect(url_for('transaction'))
        except ValueError:
            flash("Invalid amount entered.", "danger")
            return redirect(url_for('transaction'))

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # 1. Verify PIN
        cur.execute("SELECT transaction_pin FROM clients WHERE email = %s", (email,))
        result = cur.fetchone()
        if not result or result['transaction_pin'] != pin:
            flash('Invalid Transaction PIN!', 'danger')
            cur.close()
            return redirect(url_for('transaction'))

        # 2. Check if receiver exists
        cur.execute("SELECT * FROM clients WHERE email = %s", (receiver,))
        receiver_exists = cur.fetchone()
        if not receiver_exists:
            flash('Receiver email not found.', 'danger')
            cur.close()
            return redirect(url_for('transaction'))

        # 3. Calculate available balance
        cur.execute("SELECT SUM(amount) as total_deposits FROM deposits WHERE email = %s", (email,))
        deposits = cur.fetchone()['total_deposits'] or 0

        cur.execute("SELECT SUM(amount) as total_sent FROM transactions WHERE sender_email = %s", (email,))
        sent = cur.fetchone()['total_sent'] or 0

        balance = deposits - sent

        if amount > balance:
            flash(f"Insufficient balance. Your available balance is ₹{balance:.2f}", 'danger')
            cur.close()
            return redirect(url_for('transaction'))

        # 4. Process transaction
        cur.execute("""
            INSERT INTO transactions (sender_email, receiver_email, amount, transaction_pin)
            VALUES (%s, %s, %s, %s)
        """, (email, receiver, amount, pin))
        mysql.connection.commit()
        cur.close()

        flash(f'Transaction of ₹{amount:.2f} sent to {receiver}', 'success')
        return redirect(url_for('transaction'))

    # Show history
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("""
        SELECT * FROM transactions 
        WHERE sender_email = %s OR receiver_email = %s 
        ORDER BY transaction_time DESC
    """, (email, email))
    history = cur.fetchall()
    cur.close()

    return render_template('transaction.html', history=history)

@app.route('/balance')
def balance_view():
    if 'email' not in session:
        flash('Please log in to view your balance.', 'warning')
        return redirect(url_for('login'))

    email = session['email']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Total deposits
    cur.execute("SELECT SUM(amount) AS total_deposits FROM deposits WHERE email = %s", (email,))
    total_deposits = cur.fetchone()['total_deposits'] or 0

    # Total sent transactions
    cur.execute("SELECT SUM(amount) AS total_sent FROM transactions WHERE sender_email = %s", (email,))
    total_sent = cur.fetchone()['total_sent'] or 0

    # Balance
    balance = total_deposits - total_sent

    # Percent calculations
    total_activity = total_deposits + total_sent
    deposit_percent = (total_deposits / total_activity) * 100 if total_activity > 0 else 0
    sent_percent = (total_sent / total_activity) * 100 if total_activity > 0 else 0

    cur.close()

    return render_template("balance.html",
                           balance=balance,
                           total_deposits=total_deposits,
                           total_sent=total_sent,
                           deposit_percent=round(deposit_percent, 2),
                           sent_percent=round(sent_percent, 2))


@app.route('/profile')
def profile():
    if 'email' not in session:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))

    email = session['email']
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch user info
    cur.execute("SELECT username, email, account_number FROM clients WHERE email = %s", (email,))
    user = cur.fetchone()

    # Total deposits
    cur.execute("SELECT COALESCE(SUM(amount), 0) AS total_deposit FROM deposits WHERE email = %s", (email,))
    deposit_result = cur.fetchone()
    total_deposit = float(deposit_result['total_deposit'])

    # Total sent transactions
    cur.execute("SELECT COALESCE(SUM(amount), 0) AS total_sent FROM transactions WHERE sender_email = %s", (email,))
    sent_result = cur.fetchone()
    total_sent = float(sent_result['total_sent'])

    # Total received transactions
    cur.execute("SELECT COALESCE(SUM(amount), 0) AS total_received FROM transactions WHERE receiver_email = %s", (email,))
    received_result = cur.fetchone()
    total_received = float(received_result['total_received'])

    # Final balance = deposits + received - sent
    balance = total_deposit + total_received - total_sent

    cur.close()

    return render_template('profile.html', user=user, total_deposit=total_deposit,
                           total_sent=total_sent, total_received=total_received,
                           balance=balance)

# -------------------- Run App --------------------


if __name__ == '__main__':
    app.run(debug=True)
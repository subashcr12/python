from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
import time
from flask import Flask, request, redirect, url_for, render_template

# Twilio Credentials (replace with your credentials)
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
client = Client(account_sid, auth_token)

# Twilio numbers (replace with your numbers)
whatsapp_from = 'whatsapp:+14155238886'  # Your Twilio WhatsApp number
call_from = '+1234567890'  # Your Twilio phone number

# SQLite database to store users and reminders
def init_db():
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, phone TEXT UNIQUE, password TEXT)''')
    
    # Create reminders table
    c.execute('''CREATE TABLE IF NOT EXISTS reminders 
                 (id INTEGER PRIMARY KEY, user_id INTEGER, message TEXT, time TEXT, method TEXT,
                 FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Register a new user
def register_user(phone, password):
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (phone, password) VALUES (?, ?)", (phone, password))
    conn.commit()
    conn.close()

# Authenticate user login
def authenticate_user(phone, password):
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone = ? AND password = ?", (phone, password))
    user = c.fetchone()
    conn.close()
    return user

# Add a reminder for a user
def add_reminder(user_id, message, time, method):
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute("INSERT INTO reminders (user_id, message, time, method) VALUES (?, ?, ?, ?)", 
              (user_id, message, time, method))
    conn.commit()
    conn.close()

# Get reminders for a user
def get_reminders(user_id):
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reminders WHERE user_id = ?", (user_id,))
    reminders = c.fetchall()
    conn.close()
    return reminders

# Send WhatsApp message
def send_whatsapp_message(reminder):
    message = client.messages.create(
        body=reminder[2],  # Reminder message
        from_=whatsapp_from,
        to=reminder[1]  # User's WhatsApp number
    )
    print(f"WhatsApp Reminder Sent: {message.sid}")

# Make a phone call
def make_voice_call(reminder):
    call = client.calls.create(
        to=reminder[1],  # User's phone number
        from_=call_from,
        url=f'http://twimlets.com/message?Message%5B0%5D={reminder[2]}'  # Read out the reminder message
    )
    print(f"Call Reminder Initiated: {call.sid}")

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Function to schedule reminders
def schedule_reminders():
    conn = sqlite3.connect('reminders.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reminders")
    reminders = c.fetchall()
    
    for reminder in reminders:
        reminder_time = reminder[3]  # Reminder time
        if reminder[4] == 'whatsapp':
            scheduler.add_job(send_whatsapp_message, 'date', run_date=reminder_time, args=[reminder])
        elif reminder[4] == 'call':
            scheduler.add_job(make_voice_call, 'date', run_date=reminder_time, args=[reminder])

    conn.close()

# Start the scheduler
scheduler.start()

# Keep the script running to allow background tasks to execute
try:
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()

# Flask Web App
app = Flask(__name__)

# Home page - Login page
@app.route('/')
def index():
    return render_template('login.html')  # Create a login form in HTML

# Register user page
@app.route('/register', methods=['POST'])
def register():
    phone = request.form['phone']
    password = request.form['password']
    register_user(phone, password)
    return redirect(url_for('login'))

# Login user page
@app.route('/login', methods=['POST'])
def login():
    phone = request.form['phone']
    password = request.form['password']
    user = authenticate_user(phone, password)
    if user:
        return redirect(url_for('dashboard', user_id=user[0]))  # Redirect to dashboard with user ID
    else:
        return "Invalid credentials"

# User dashboard to manage reminders
@app.route('/dashboard/<int:user_id>', methods=['GET', 'POST'])
def dashboard(user_id):
    if request.method == 'POST':
        message = request.form['message']
        time = request.form['time']
        method = request.form['method']
        add_reminder(user_id, message, time, method)
        return redirect(url_for('dashboard', user_id=user_id))
    else:
        reminders = get_reminders(user_id)
        return render_template('dashboard.html', user_id=user_id, reminders=reminders)  # Show reminders

if __name__ == '__main__':
    app.run(debug=True)

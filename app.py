import base64
import datetime
import hashlib
import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)

def encrypt_data(text):
    encoded = base64.urlsafe_b64encode(hashlib.sha256(text.encode()).digest())
    return encoded.decode()
app = Flask(__name__)
app.secret_key = "super_secret_secret"
def load_key():
    return Fernet.generate_key()

def encrypt_data(text):
    key = load_key()
    f = Fernet(key)
    return f.encrypt(text.encode())

def decrypt_data(encrypted_text):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(encrypted_text).decode()
    return f.encrypt(text.encode())

# Route to add a log entry with encryption
@app.route('/add-log', methods=['POST'])
def add_log():
    # Example log message we want to secure
    message = "User login successful"
    
    # Encrypt the message before saving
    encrypted_message = encrypt_data(message)
    
    # Save the encrypted data into security.db
    conn = sqlite3.connect('security.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message BLOB
        )
    ''')
    cursor.execute("INSERT INTO logs (message) VALUES (?)", (encrypted_message,))
    conn.commit()
    conn.close()
    
    return "Log encrypted and saved to database successfully!"
def decrypt_data(encrypted_text):
    key = load_key()
    f = Fernet(key)
    return f.decrypt(encrypted_text).decode()
    return Fernet.generate_key()

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect('security.db')
    cursor = conn.cursor()
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT)''')
    # Audit logs table
    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT,
                        action TEXT,
                        timestamp TEXT)''')
    
    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Administrator')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('family', 'user123', 'Family Member')")
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        
        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            
            # Log audit trail
            cursor.execute("INSERT INTO audit_logs (username, action, timestamp) VALUES (?, ?, ?)",
                           (username, f"Logged in as {user[3]}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid Credentials. Access Denied."
        conn.close()
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('security.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, action, timestamp FROM audit_logs ORDER BY id DESC LIMIT 5")
    logs = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', username=session['username'], role=session['role'], logs=logs)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
import time
from flask import Response
import sqlite3
from flask import Response, session, redirect, url_for, render_template

# Helper function to log camera access into security.db
def log_audit_event(username, action):
    try:
        conn = sqlite3.connect('security.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO audit_logs (username, action, timestamp) VALUES (?, ?, datetime('now', 'localtime'))", 
                       (username, action))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Audit log error:", e)

@app.route('/video_feed/<cam_id>')
def video_feed(cam_id):
    # 1. Session Protection: Ensure user is logged in
    if 'user' not in session:
        return "Unauthorized Access - Please Log In", 403
    
    # 3. Database Audit Logging: Log which camera was accessed
    username = session.get('user', 'unknown')
    camera_name = "Hallway" if cam_id == "1" else "Perimeter"
    log_audit_event(username, f"Accessed Camera Feed: {camera_name}")

    # 2. Multi-Camera Feed Generator (Returns a smooth HTML stream container)
    def generate():
        while True:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            html_chunk = f"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="1">
                    <style>
                        body {{ background-color: #0d1117; color: #00ffcc; font-family: monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                        .feed-box {{ text-align: center; border: 1px dashed #00ffcc; padding: 15px; width: 90%; border-radius: 8px; }}
                    </style>
                </head>
                <body>
                    <div class="feed-box">
                        <h3>[LIVE SECURE STREAM - CAM {cam_id}: {camera_name.upper()}]</h3>
                        <p>Status: Encrypted & Active</p>
                        <p>Timestamp: {current_time}</p>
                    </div>
                </body>
            </html>
            """
            yield (b'--frame\r\n'
                   b'Content-Type: text/html\r\n\r\n' + html_chunk.encode('utf-8') + b'\r\n')
            time.sleep(1)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
if __name__ == '__main__':
    app.run(debug=True, port=5000)
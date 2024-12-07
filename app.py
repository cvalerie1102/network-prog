from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from argon2 import PasswordHasher
import sqlite3
import os
import uuid

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per second"]  # 10 requests per second
)

# Database setup
DATABASE = "totally_not_my_privateKeys.db"
NOT_MY_KEY = os.environ.get("NOT_MY_KEY", b"16BYTEKEY_123456")  # AES key (must be 16 bytes)
ph = PasswordHasher()

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE,
            date_registered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_ip TEXT NOT NULL,
            request_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)
        conn.commit()

init_db()

# AES Encryption functions
def encrypt(data):
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(NOT_MY_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    return iv + encrypted_data

def decrypt(encrypted_data):
    iv = encrypted_data[:16]
    encrypted_content = encrypted_data[16:]
    cipher = Cipher(algorithms.AES(NOT_MY_KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(encrypted_content) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

# Register endpoint
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = str(uuid.uuid4())  # Generate UUID password
    password_hash = ph.hash(password)

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)",
                           (username, password_hash, email))
            conn.commit()
            return jsonify({"password": password}), 201
        except sqlite3.IntegrityError:
            return jsonify({"error": "User already exists"}), 400

# Authentication logging
@app.route("/auth", methods=["POST"])
@limiter.limit("10 per second")  # Apply rate limiting here
def auth():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            user_id, password_hash = user
            try:
                if ph.verify(password_hash, password):
                    cursor.execute("INSERT INTO auth_logs (request_ip, user_id) VALUES (?, ?)",
                                   (request.remote_addr, user_id))
                    conn.commit()
                    return jsonify({"status": "authenticated"}), 200
            except Exception:
                pass
    return jsonify({"status": "unauthorized"}), 401

# Show all logs
@app.route("/logs", methods=["GET"])
def logs():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM auth_logs")
        logs = cursor.fetchall()
        return jsonify(logs)

if __name__ == "__main__":
    app.run(debug=True, port=8080)  # Updated port to 8080
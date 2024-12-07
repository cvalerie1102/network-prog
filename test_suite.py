import pytest
from app import app, db, NOT_MY_KEY
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Ensure the database is initialized
        yield client
        with app.app_context():
            db.drop_all()  # Clean up the database after tests


def test_user_registration(client):
    # Test registering a new user
    payload = {"username": "testuser", "email": "testuser@example.com"}
    response = client.post('/register', json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert "password" in data

    # Test registering with duplicate username
    response = client.post('/register', json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()

    # Test registering with duplicate email
    payload = {"username": "testuser2", "email": "testuser@example.com"}
    response = client.post('/register', json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_auth_logs(client):
    # Register a user
    payload = {"username": "authuser", "email": "authuser@example.com"}
    response = client.post('/register', json=payload)
    assert response.status_code == 201
    password = response.get_json()["password"]

    # Authenticate the user
    auth_payload = {"username": "authuser", "password": password}
    response = client.post('/auth', json=auth_payload)
    assert response.status_code == 200

    # Verify that the authentication log is created
    with app.app_context():
        conn = db.engine.connect()
        result = conn.execute("SELECT * FROM auth_logs WHERE user_id = (SELECT id FROM users WHERE username = 'authuser')")
        logs = list(result)
        assert len(logs) == 1
        assert logs[0]["request_ip"] is not None
        assert logs[0]["request_timestamp"] is not None


def test_aes_encryption(client):
    # Ensure the encryption key is set
    assert NOT_MY_KEY is not None

    # Add a private key to the database and verify it is encrypted
    private_key = "test_private_key"
    with app.app_context():
        conn = db.engine.connect()
        encrypted_key = encrypt_private_key(private_key)
        conn.execute(
            "INSERT INTO keys (key_id, private_key) VALUES (?, ?)",
            ("test_key_id", encrypted_key)
        )

        result = conn.execute("SELECT private_key FROM keys WHERE key_id = 'test_key_id'")
        stored_key = result.fetchone()["private_key"]
        assert stored_key != private_key  # Ensure it's encrypted

        # Decrypt the key and verify it matches the original
        decrypted_key = decrypt_private_key(stored_key)
        assert decrypted_key == private_key


# Utility functions for encryption/decryption
def encrypt_private_key(private_key):
    cipher = Cipher(algorithms.AES(NOT_MY_KEY), modes.ECB())
    encryptor = cipher.encryptor()
    padded_key = private_key.ljust(32).encode()  # Pad to 32 bytes
    encrypted_key = encryptor.update(padded_key) + encryptor.finalize()
    return encrypted_key


def decrypt_private_key(encrypted_key):
    cipher = Cipher(algorithms.AES(NOT_MY_KEY), modes.ECB())
    decryptor = cipher.decryptor()
    decrypted_key = decryptor.update(encrypted_key) + decryptor.finalize()
    return decrypted_key.decode().strip()


def test_show_all_cracked(client):
    # Example for showing all cracked passwords
    response = client.get('/show_all_cracked')
    assert response.status_code == 200
    data = response.get_json()
    assert "cracked_passwords" in data
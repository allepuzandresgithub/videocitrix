# db.py - Funciones de base de datos.
# Lee todas las credenciales desde variables de entorno (o desde .env si existe).
# No contiene valores por defecto inseguros.

import os
import sys
import mysql.connector
from mysql.connector import Error
import bcrypt
from datetime import datetime

# Intentar cargar .env si existe (útil en desarrollo)
try:
    from dotenv import load_dotenv
    load_dotenv()  # No sobreescribe variables del sistema ya definidas
except ImportError:
    # Si no está instalado, seguir sin él
    pass
except Exception:
    pass

def required_env(name):
    """Obtiene variable de entorno o termina el programa si no existe."""
    value = os.getenv(name)
    if value is None:
        sys.exit(f"❌ Error crítico: Variable de entorno {name} no definida. Revisa tu archivo .env o configura la variable en el sistema.")
    return value

# Configuración desde variables de entorno (obligatorias, sin fallbacks)
DB_CONFIG = {
    'host': required_env("DB_HOST"),
    'user': required_env("DB_APP_USER"),
    'password': required_env("DB_APP_PASSWORD"),
    'database': required_env("DB_NAME")
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Error conectando a MySQL: {e}")
        return None

# ------------------------------------------------------------
# Funciones de negocio (sin cambios, solo usan get_db_connection)
# ------------------------------------------------------------

def create_user(username, email, password):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {'id': user_id, 'username': username, 'email': email}
    except Error as e:
        print(f"Error creando usuario: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def authenticate_user(username_or_email, password):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE username = %s OR email = %s",
        (username_or_email, username_or_email)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", (datetime.now(), user['id']))
        conn.commit()
        cursor.close()
        conn.close()
        user.pop('password_hash')
        return user
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, email, created_at, last_login, role, avatar_url FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def get_all_users():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, email, role, created_at, last_login, avatar_url FROM users ORDER BY created_at DESC"
    )
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    for u in users:
        for key in ('created_at', 'last_login'):
            if u.get(key):
                u[key] = u[key].isoformat()
    return users

def delete_user(user_id):
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0

def update_user_role(user_id, role):
    if role not in ('user', 'admin'):
        return False
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = %s WHERE id = %s", (role, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def update_user_avatar(user_id, avatar_url):
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar_url = %s WHERE id = %s", (avatar_url, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def update_user_password(user_id, new_password):
    conn = get_db_connection()
    if not conn:
        return False
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (password_hash, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True

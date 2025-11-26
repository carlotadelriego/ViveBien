# database.py
import sqlite3
import hashlib
from datetime import datetime, timedelta
import os
import random
from data_simulation import simulate_biometrics

DB_PATH = "vivebien.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

# ----------------------------------------
#  Inicialización de la base de datos
# ----------------------------------------
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            target_steps INTEGER DEFAULT 8000,
            tts_enabled INTEGER DEFAULT 1
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS biometrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            steps INTEGER,
            sleep_hours REAL,
            heart_rate INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            text TEXT,
            sentiment TEXT,
            score REAL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

# ----------------------------------------
# Hash seguro
# ----------------------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------------------------
# Registro de usuario
# ----------------------------------------
def register_user(name: str, email: str, password: str, target_steps: int = 8000, tts_enabled: bool = True):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (name, email, password_hash, target_steps, tts_enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, hash_password(password), int(target_steps), int(bool(tts_enabled))))
        conn.commit()
        return True, "Usuario creado correctamente."
    except sqlite3.IntegrityError:
        return False, "Este email ya está registrado."
    finally:
        conn.close()

# ----------------------------------------
# Login de usuario
# ----------------------------------------
def login_user(email: str, password: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name, password_hash, target_steps, tts_enabled FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False, "El usuario no existe.", None
    user_id, name, stored_hash, target_steps, tts_enabled = row
    if hash_password(password) != stored_hash:
        return False, "Contraseña incorrecta.", None
    return True, "Login correcto.", {
        "user_id": user_id,
        "name": name,
        "email": email,
        "target_steps": target_steps,
        "tts_enabled": bool(tts_enabled)
    }

# ----------------------------------------
# Update user (persistir cambios)
# ----------------------------------------
def update_user(user_id: int, name: str = None, target_steps: int = None, tts_enabled: bool = None):
    conn = get_conn()
    c = conn.cursor()
    fields = []
    vals = []
    if name is not None:
        fields.append("name = ?")
        vals.append(name)
    if target_steps is not None:
        fields.append("target_steps = ?")
        vals.append(int(target_steps))
    if tts_enabled is not None:
        fields.append("tts_enabled = ?")
        vals.append(int(bool(tts_enabled)))
    if fields:
        sql = "UPDATE users SET " + ", ".join(fields) + " WHERE id = ?"
        vals.append(int(user_id))
        c.execute(sql, tuple(vals))
        conn.commit()
    conn.close()
    return True

# ----------------------------------------
# Guardar biometría de un usuario
# ----------------------------------------
def save_biometrics(user_id: int, data: dict, date_iso: str = None):
    if date_iso is None:
        date_iso = datetime.now().date().isoformat()
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO biometrics (user_id, date, steps, sleep_hours, heart_rate)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, date_iso, int(data.get("steps", 0)), float(data.get("sleep_hours", 0.0)), int(data.get("heart_rate", 0))))
    conn.commit()
    conn.close()

# ----------------------------------------
# Obtener biometría histórica
# ----------------------------------------
def load_biometrics(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT date, steps, sleep_hours, heart_rate
        FROM biometrics
        WHERE user_id = ?
        ORDER BY date ASC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ----------------------------------------
# Guardar registro emocional
# ----------------------------------------
def save_mood_log(user_id: int, text: str, sentiment: str, score: float):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO mood_logs (user_id, date, text, sentiment, score)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, datetime.now().isoformat(), text, sentiment, float(score)))
    conn.commit()
    conn.close()

# ----------------------------------------
# Comprobaciones y seed
# ----------------------------------------
def has_any_user():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    n = c.fetchone()[0]
    conn.close()
    return n > 0

def seed_db():
    """
    Crea 3 usuarios de ejemplo con 14 días de biometría cada uno.
    Sofía (equilibrada), Marcos (estresado), Lucía (activa)
    """
    if has_any_user():
        return False, "La BD ya tiene usuarios."
    users = [
        ("Sofía", "sofia@example.com", "password123", 10000, True),
        ("Marcos", "marcos@example.com", "password123", 7000, True),
        ("Lucía", "lucia@example.com", "password123", 14000, True),
    ]
    for name, email, pwd, target, tts in users:
        ok, msg = register_user(name, email, pwd, target, tts)
        if not ok:
            continue
    # ahora generar biometría con patrones distintos
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, name FROM users")
    rows = c.fetchall()
    conn.close()
    for user_id, name in rows:
        for d in range(14):
            # fecha de hace 14-días hasta hoy
            date_iso = (datetime.now().date() - timedelta(days=(13-d))).isoformat()
            if name.lower().startswith("sof"):
                # equilibrada
                steps = random.randint(8000, 11000)
                sleep = round(random.uniform(7.0, 8.0),1)
                hr = random.randint(60,75)
            elif name.lower().startswith("mar"):
                steps = random.randint(2000, 4500)
                sleep = round(random.uniform(4.0, 6.0),1)
                hr = random.randint(80,98)
            else:
                steps = random.randint(12000, 16000)
                sleep = round(random.uniform(7.0, 9.0),1)
                hr = random.randint(55,72)
            save_biometrics(user_id, {"steps": steps, "sleep_hours": sleep, "heart_rate": hr}, date_iso=date_iso)
        # generar algunos mood logs
        if name.lower().startswith("mar"):
            save_mood_log(user_id, "Me siento muy estresado por los exámenes", "Negativo", -0.4)
        elif name.lower().startswith("sof"):
            save_mood_log(user_id, "Hoy me siento bien, he dormido mejor", "Positivo", 0.3)
        else:
            save_mood_log(user_id, "Entrené bien hoy y me siento activa", "Positivo", 0.4)
    return True, "Seed completado: 3 usuarios creados con datos."

# fin database.py

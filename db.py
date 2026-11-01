import os
import json
import sqlite3
import shutil
from datetime import datetime
from flask import session
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException

class PaymentRequired(HTTPException):
    code = 402
    description = 'Looks like you got to another page, or no connection.'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/ecocoins.db'
    JSON_PATH = '/tmp/ecocoins_data.json'
    SEED_DB = os.path.join(BASE_DIR, 'database', 'ecocoins.db')
    SEED_JSON = os.path.join(BASE_DIR, 'data', 'ecocoins_data.json')
    if not os.path.exists(DB_PATH) and os.path.exists(SEED_DB):
        shutil.copy2(SEED_DB, DB_PATH)
    if not os.path.exists(JSON_PATH) and os.path.exists(SEED_JSON):
        shutil.copy2(SEED_JSON, JSON_PATH)
else:
    DB_PATH = os.path.join(BASE_DIR, 'database', 'ecocoins.db')
    JSON_PATH = os.path.join(BASE_DIR, 'data', 'ecocoins_data.json')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sync_to_json():
    conn = get_db()
    cur = conn.cursor()
    users = [dict(r) for r in cur.execute("SELECT * FROM users").fetchall()]
    materials = [dict(r) for r in cur.execute("SELECT * FROM materials").fetchall()]
    txs = [dict(r) for r in cur.execute("SELECT * FROM transactions").fetchall()]
    rewards = [dict(r) for r in cur.execute("SELECT * FROM rewards").fetchall()]
    redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions").fetchall()]
    conn.close()

    payload = {
        "users": users,
        "materials": materials,
        "transactions": txs,
        "rewards": rewards,
        "redemptions": redemptions
    }
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'resident',
        qr_code TEXT NOT NULL UNIQUE,
        points INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT
    )''')

    try:
        cur.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        conn.commit()
    except Exception:
        pass

    cur.execute('''CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        points_per_unit INTEGER NOT NULL,
        unit TEXT DEFAULT 'piece',
        status TEXT DEFAULT 'active'
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        material_id INTEGER,
        material_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        points_earned INTEGER NOT NULL,
        receipt_no TEXT NOT NULL,
        created_at TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        points_required INTEGER NOT NULL,
        stock INTEGER DEFAULT 50,
        partner_name TEXT DEFAULT '',
        status TEXT DEFAULT 'available'
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        reward_id INTEGER NOT NULL,
        reward_title TEXT NOT NULL,
        points_spent INTEGER NOT NULL,
        redemption_code TEXT NOT NULL,
        status TEXT DEFAULT 'claimed',
        created_at TEXT
    )''')

    conn.commit()

    user_count = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        default_users = [
            ("Admin Officer", "admin@ecocoins.ph", generate_password_hash("admin123"), "admin", "ECO-ADM-0001", 0, "active", "2026-10-01 08:00:00"),
            ("Barangay Staff", "staff@ecocoins.ph", generate_password_hash("staff123"), "staff", "ECO-STF-0001", 0, "active", "2026-10-02 08:00:00"),
            ("User", "user@example.com", generate_password_hash("user123"), "resident", "ECO-RES-88219", 1250, "active", "2026-10-10 09:30:00"),
            ("Annie Flores", "annie@example.com", generate_password_hash("user123"), "resident", "ECO-RES-10492", 840, "active", "2026-10-12 11:20:00"),
            ("Theresa Ramos", "theresa@example.com", generate_password_hash("user123"), "resident", "ECO-RES-29381", 960, "active", "2026-10-14 14:15:00"),
            ("Cathrine Santos", "cathrine@example.com", generate_password_hash("user123"), "resident", "ECO-RES-50123", 1100, "active", "2026-10-15 16:40:00"),
            ("Noel Batumbakal", "noel@example.com", generate_password_hash("user123"), "resident", "ECO-RES-77401", 620, "active", "2026-10-16 10:10:00")
        ]
        cur.executemany("INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", default_users)

        default_materials = [
            ("Plastic Bottle", "Plastic", 5, "piece", "active"),
            ("Can", "Metal", 8, "piece", "active"),
            ("Glass Bottle", "Glass", 10, "piece", "active"),
            ("Cardboard / Paper", "Paper", 4, "kg", "active")
        ]
        cur.executemany("INSERT INTO materials (name, category, points_per_unit, unit, status) VALUES (?, ?, ?, ?, ?)", default_materials)

        default_txs = [
            (3, 1, "Plastic Bottle", 2, 10, "REC-20261022-01", "2026-10-22 10:24:00"),
            (3, 2, "Can", 1, 8, "REC-20261021-02", "2026-10-21 16:32:00"),
            (3, 1, "Plastic Bottle", 2, 10, "REC-20261019-03", "2026-10-19 11:20:00"),
            (3, 2, "Can", 3, 24, "REC-20261018-04", "2026-10-18 15:15:00"),
            (3, 1, "Plastic Bottle", 1, 5, "REC-20261016-05", "2026-10-16 09:40:00"),
            (4, 1, "Plastic Bottle", 2, 10, "REC-20261022-06", "2026-10-22 10:24:00"),
            (5, 2, "Can", 3, 24, "REC-20261022-07", "2026-10-22 10:11:00"),
            (6, 1, "Plastic Bottle", 4, 20, "REC-20261022-08", "2026-10-22 09:52:00"),
            (7, 2, "Can", 1, 8, "REC-20261022-09", "2026-10-22 09:30:00")
        ]
        cur.executemany("INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", default_txs)

        conn.commit()
    else:
        staff_exists = cur.execute("SELECT id FROM users WHERE email = 'staff@ecocoins.ph'").fetchone()
        if not staff_exists:
            cur.execute(
                "INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
                ("Barangay Staff", "staff@ecocoins.ph", generate_password_hash("staff123"), "staff", "ECO-STF-0001", 0, "2026-10-02 08:00:00")
            )
            conn.commit()

    cur.execute("DELETE FROM users WHERE email = 'applicant@ecocoins.ph'")
    conn.commit()

    rice_check = cur.execute("SELECT COUNT(*) FROM rewards WHERE title LIKE '%Bigas%' OR title LIKE '%Delata%'").fetchone()[0]
    if rice_check == 0:
        cur.execute("DELETE FROM rewards")
        local_rewards = [
            ("1kg Sinandomeng Rice (Bigas)", "Food Staples", 300, 80, "Barangay Food Bank", "available"),
            ("5kg Dinorado Rice (Bigas)", "Food Staples", 1400, 40, "Barangay Food Bank", "available"),
            ("Delata Pack (2 Sardinas + 1 Corned Beef)", "Canned Goods", 250, 75, "Barangay Relief Hub", "available"),
            ("EcoCoins Heavy-Duty Payong (Umbrella)", "Merchandise", 450, 50, "Barangay Green Store", "available"),
            ("Eco Tote Bag (Reusable)", "Merchandise", 200, 100, "Barangay Green Store", "available"),
            ("Noodles & Coffee Bundle (3 Noodles + 3 Coffee)", "Food Staples", 180, 90, "Barangay Food Bank", "available"),
            ("Family Hygiene Kit (Bath Soap, Detergent, Toothpaste)", "Household", 350, 60, "Barangay Health Center", "available"),
            ("Stainless Water Tumbler (500ml)", "Merchandise", 500, 45, "Barangay Green Store", "available")
        ]
        cur.executemany("INSERT INTO rewards (title, category, points_required, stock, partner_name, status) VALUES (?, ?, ?, ?, ?, ?)", local_rewards)
        conn.commit()

    conn.close()
    sync_to_json()

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

import json
import os
import random
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException

class PaymentRequired(HTTPException):
    code = 402
    description = 'Looks like you got to another page, or no connection.'

app = Flask(__name__)
app.secret_key = 'ecocoins_super_secret_session_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
        created_at TEXT
    )''')

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
            ("Admin Officer", "admin@ecocoins.ph", generate_password_hash("admin123"), "admin", "ECO-ADM-0001", 0, "2026-10-01 08:00:00"),
            ("User", "user@example.com", generate_password_hash("user123"), "resident", "ECO-RES-88219", 1250, "2026-10-10 09:30:00"),
            ("Annie Flores", "annie@example.com", generate_password_hash("user123"), "resident", "ECO-RES-10492", 840, "2026-10-12 11:20:00"),
            ("Theresa Ramos", "theresa@example.com", generate_password_hash("user123"), "resident", "ECO-RES-29381", 960, "2026-10-14 14:15:00"),
            ("Cathrine Santos", "cathrine@example.com", generate_password_hash("user123"), "resident", "ECO-RES-50123", 1100, "2026-10-15 16:40:00"),
            ("Noel Batumbakal", "noel@example.com", generate_password_hash("user123"), "resident", "ECO-RES-77401", 620, "2026-10-16 10:10:00")
        ]
        cur.executemany("INSERT INTO users (full_name, email, password, role, qr_code, points, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", default_users)

        default_materials = [
            ("Plastic Bottle", "Plastic", 5, "piece", "active"),
            ("Can", "Metal", 8, "piece", "active"),
            ("Glass Bottle", "Glass", 10, "piece", "active"),
            ("Cardboard / Paper", "Paper", 4, "kg", "active")
        ]
        cur.executemany("INSERT INTO materials (name, category, points_per_unit, unit, status) VALUES (?, ?, ?, ?, ?)", default_materials)

        default_txs = [
            (2, 1, "Plastic Bottle", 2, 10, "REC-20261022-01", "2026-10-22 10:24:00"),
            (2, 2, "Can", 1, 8, "REC-20261021-02", "2026-10-21 16:32:00"),
            (2, 1, "Plastic Bottle", 2, 10, "REC-20261019-03", "2026-10-19 11:20:00"),
            (2, 2, "Can", 3, 24, "REC-20261018-04", "2026-10-18 15:15:00"),
            (2, 1, "Plastic Bottle", 1, 5, "REC-20261016-05", "2026-10-16 09:40:00"),
            (3, 1, "Plastic Bottle", 2, 10, "REC-20261022-06", "2026-10-22 10:24:00"),
            (4, 2, "Can", 3, 24, "REC-20261022-07", "2026-10-22 10:11:00"),
            (5, 1, "Plastic Bottle", 4, 20, "REC-20261022-08", "2026-10-22 09:52:00"),
            (6, 2, "Can", 1, 8, "REC-20261022-09", "2026-10-22 09:30:00")
        ]
        cur.executemany("INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", default_txs)

        default_rewards = [
            ("10% Off at SM Lipa", "Discounts", 500, 50, "SM City Lipa", "available"),
            ("Eco Tote Bag", "Merchandise", 1000, 30, "Barangay Green Store", "available"),
            ("Discount Voucher (₱50) · Robinsons Lipa", "Discounts", 1800, 40, "Robinsons Place Lipa", "available"),
            ("Free Drink · The Coffee Project", "Partners", 750, 25, "The Coffee Project Lipa", "available"),
            ("EcoCoins Keychain", "Merchandise", 300, 80, "Barangay Green Store", "available"),
            ("Movie Pass (1 Ticket) · SM Cinema Lipa", "Partners", 1500, 20, "SM Cinema Lipa", "available")
        ]
        cur.executemany("INSERT INTO rewards (title, category, points_required, stock, partner_name, status) VALUES (?, ?, ?, ?, ?, ?)", default_rewards)

        default_redemptions = [
            (2, 5, "EcoCoins Keychain", 300, "RDM-88219-01", "claimed", "2026-10-15 14:00:00")
        ]
        cur.executemany("INSERT INTO redemptions (user_id, reward_id, reward_title, points_spent, redemption_code, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", default_redemptions)

        conn.commit()

    conn.close()
    sync_to_json()

init_db()

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

@app.route('/')
def index():
    return render_template('index.html', active_page='index')

@app.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html', active_page='how_it_works')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    email = ''
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db()
        cur = conn.cursor()
        matched = cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
        conn.close()

        if matched:
            matched = dict(matched)
            valid = False
            if matched['password'] in ['user123', 'admin123', password]:
                valid = True
            elif check_password_hash(matched['password'], password):
                valid = True

            if valid:
                session['user_id'] = matched['id']
                session['user_role'] = matched['role']
                if matched['role'] == 'admin':
                    return redirect(url_for('admin'))
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid email or password.'
        else:
            error = 'Invalid email or password.'

    return render_template('login.html', error=error, email=email, active_page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    full_name = ''
    email = ''
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        terms = request.form.get('terms')

        if not full_name or not email or not password:
            error = 'Please fill in all required fields.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters.'
        elif not terms:
            error = 'You must agree to the Terms and Conditions.'
        else:
            conn = get_db()
            cur = conn.cursor()
            existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
            if existing:
                conn.close()
                error = 'An account with this email already exists.'
            else:
                qr_code = f'ECO-RES-{random.randint(10000, 99999)}'
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                hashed_pw = generate_password_hash(password)
                cur.execute(
                    "INSERT INTO users (full_name, email, password, role, qr_code, points, created_at) VALUES (?, ?, ?, 'resident', ?, 0, ?)",
                    (full_name, email, hashed_pw, qr_code, created_at)
                )
                conn.commit()
                new_id = cur.lastrowid
                conn.close()
                sync_to_json()

                session['user_id'] = new_id
                session['user_role'] = 'resident'
                return redirect(url_for('dashboard'))

    return render_template('register.html', error=error, full_name=full_name, email=email, active_page='register')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
    conn.close()

    bottle_count = 0
    can_count = 0
    other_count = 0
    for t in user_txs:
        name = t.get('material_name', '').lower()
        qty = int(t.get('quantity', 0))
        if 'bottle' in name or 'plastic' in name:
            bottle_count += qty
        elif 'can' in name:
            can_count += qty
        else:
            other_count += qty

    return render_template(
        'dashboard.html',
        active_page='dashboard',
        user_transactions=user_txs,
        bottle_count=bottle_count,
        can_count=can_count,
        other_count=other_count
    )

@app.route('/ecopoints')
def ecopoints():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
    conn.close()

    bottle_points = 0
    can_points = 0
    other_points = 0
    for t in user_txs:
        name = t.get('material_name', '').lower()
        pts = int(t.get('points_earned', 0))
        if 'bottle' in name or 'plastic' in name:
            bottle_points += pts
        elif 'can' in name:
            can_points += pts
        else:
            other_points += pts

    total = max(1, bottle_points + can_points + other_points)
    bottle_pct = round((bottle_points / total) * 100)
    can_pct = round((can_points / total) * 100)
    other_pct = round((other_points / total) * 100)

    return render_template(
        'ecopoints.html',
        active_page='ecopoints',
        user_transactions=user_txs,
        bottle_points=bottle_points,
        can_points=can_points,
        other_points=other_points,
        bottle_pct=bottle_pct,
        can_pct=can_pct,
        other_pct=other_pct
    )

@app.route('/history')
def history():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
    conn.close()

    return render_template('history.html', active_page='history', user_transactions=user_txs)

@app.route('/rewards', methods=['GET', 'POST'])
def rewards():
    user = get_current_user()
    message = None
    message_type = 'success'

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        if not user:
            conn.close()
            return redirect(url_for('login'))

        reward_id = int(request.form.get('reward_id', 0))
        reward = cur.execute("SELECT * FROM rewards WHERE id = ?", (reward_id,)).fetchone()

        if not reward:
            message = 'Selected reward not found.'
            message_type = 'danger'
        else:
            reward = dict(reward)
            if user['points'] < reward['points_required']:
                message = 'Insufficient EcoPoints balance.'
                message_type = 'danger'
            elif reward.get('stock', 0) <= 0:
                message = 'This reward is out of stock.'
                message_type = 'danger'
            else:
                code = f'RDM-{random.randint(10000, 99999)}'
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cur.execute(
                    "INSERT INTO redemptions (user_id, reward_id, reward_title, points_spent, redemption_code, status, created_at) VALUES (?, ?, ?, ?, ?, 'claimed', ?)",
                    (user['id'], reward['id'], reward['title'], reward['points_required'], code, now_str)
                )
                cur.execute("UPDATE users SET points = MAX(0, points - ?) WHERE id = ?", (reward['points_required'], user['id']))
                cur.execute("UPDATE rewards SET stock = MAX(0, stock - 1) WHERE id = ?", (reward['id'],))
                conn.commit()

                user['points'] = max(0, user['points'] - reward['points_required'])
                message = f'Reward redeemed successfully! Your voucher code is: {code}'
                message_type = 'success'
                sync_to_json()

    all_rewards = [dict(r) for r in cur.execute("SELECT * FROM rewards ORDER BY points_required ASC").fetchall()]
    user_redemptions = []
    if user:
        user_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
    conn.close()

    user_points = user['points'] if user else 0

    return render_template(
        'rewards.html',
        active_page='rewards',
        rewards=all_rewards,
        redemptions=user_redemptions,
        user_points=user_points,
        message=message,
        message_type=message_type
    )

@app.route('/station-simulator', methods=['GET', 'POST'])
def station_simulator():
    user = get_current_user()
    conn = get_db()
    cur = conn.cursor()
    materials = [dict(r) for r in cur.execute("SELECT * FROM materials ORDER BY id ASC").fetchall()]
    prefill_qr = user['qr_code'] if user else ''
    receipt = None
    error = None

    if request.method == 'POST':
        qr_code = request.form.get('qr_code', '').strip()
        material_id = int(request.form.get('material_id', 0))
        quantity = max(1, int(request.form.get('quantity', 1)))

        resident = cur.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,)).fetchone()
        material = cur.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()

        if not resident:
            error = 'QR Code not found in the resident database.'
        elif not material:
            error = 'Invalid material selected.'
        else:
            resident = dict(resident)
            material = dict(material)
            points_earned = quantity * int(material.get('points_per_unit', 1))
            receipt_no = f'REC-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cur.execute(
                "INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (resident['id'], material['id'], material['name'], quantity, points_earned, receipt_no, now_str)
            )
            cur.execute("UPDATE users SET points = points + ? WHERE id = ?", (points_earned, resident['id']))
            conn.commit()

            new_points = resident['points'] + points_earned
            receipt = {
                'receipt_no': receipt_no,
                'resident_name': resident['full_name'],
                'qr_code': resident['qr_code'],
                'material_name': material['name'],
                'quantity': quantity,
                'unit': material.get('unit', 'piece'),
                'points_earned': points_earned,
                'new_total_points': new_points
            }
            sync_to_json()

    conn.close()

    return render_template(
        'station_simulator.html',
        active_page='station_simulator',
        materials=materials,
        prefill_qr=prefill_qr,
        receipt=receipt,
        error=error
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    tab = request.args.get('tab', 'dashboard')
    feedback = None
    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('admin_action')
        if action == 'save_material':
            name = request.form.get('mat_name', '').strip()
            cat = request.form.get('mat_cat', 'General').strip()
            pts = max(1, int(request.form.get('mat_points', 1)))
            unit = request.form.get('mat_unit', 'piece').strip()
            if name:
                cur.execute(
                    "INSERT INTO materials (name, category, points_per_unit, unit, status) VALUES (?, ?, ?, ?, 'active')",
                    (name, cat, pts, unit)
                )
                conn.commit()
                feedback = 'Material added successfully!'
                sync_to_json()
        elif action == 'save_reward':
            title = request.form.get('rew_title', '').strip()
            cat = request.form.get('rew_category', 'Discounts')
            pts = max(1, int(request.form.get('rew_points', 100)))
            stock = max(0, int(request.form.get('rew_stock', 50)))
            partner = request.form.get('rew_partner', '').strip()
            if title:
                cur.execute(
                    "INSERT INTO rewards (title, category, points_required, stock, partner_name, status) VALUES (?, ?, ?, ?, ?, 'available')",
                    (title, cat, pts, stock, partner)
                )
                conn.commit()
                feedback = 'Reward added successfully!'
                sync_to_json()
        elif action == 'staff_deposit':
            res_id = int(request.form.get('resident_id', 0))
            mat_id = int(request.form.get('mat_id', 0))
            qty = max(1, int(request.form.get('qty', 1)))
            res = cur.execute("SELECT * FROM users WHERE id = ?", (res_id,)).fetchone()
            mat = cur.execute("SELECT * FROM materials WHERE id = ?", (mat_id,)).fetchone()
            if res and mat:
                res = dict(res)
                mat = dict(mat)
                pts = qty * int(mat.get('points_per_unit', 1))
                rcp = f'REC-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cur.execute(
                    "INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (res['id'], mat['id'], mat['name'], qty, pts, rcp, now_str)
                )
                cur.execute("UPDATE users SET points = points + ? WHERE id = ?", (pts, res['id']))
                conn.commit()
                feedback = f"Walk-in deposit recorded for {res['full_name']}! +{pts} points added."
                sync_to_json()

    all_txs = [dict(r) for r in cur.execute("""
        SELECT t.*, u.full_name AS resident_name
        FROM transactions t
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC
    """).fetchall()]

    residents_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY id ASC").fetchall()]
    all_materials = [dict(r) for r in cur.execute("SELECT * FROM materials ORDER BY id ASC").fetchall()]
    all_rewards = [dict(r) for r in cur.execute("SELECT * FROM rewards ORDER BY points_required ASC").fetchall()]
    all_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions ORDER BY created_at DESC").fetchall()]

    today_str = datetime.now().strftime('%Y-%m-%d')
    today_items = sum(int(t.get('quantity', 0)) for t in all_txs if str(t.get('created_at', '')).startswith(today_str))
    total_points = sum(int(t.get('points_earned', 0)) for t in all_txs)

    mat_counts = {'Plastic Bottles': 0, 'Cans': 0, 'Others': 0}
    for t in all_txs:
        m_name = str(t.get('material_name', '')).lower()
        q = int(t.get('quantity', 0))
        if 'bottle' in m_name or 'plastic' in m_name:
            mat_counts['Plastic Bottles'] += q
        elif 'can' in m_name:
            mat_counts['Cans'] += q
        else:
            mat_counts['Others'] += q

    stats = {
        'today_items': today_items,
        'total_points_issued': total_points,
        'total_redemptions': len(all_redemptions),
        'recent_transactions': all_txs[:6],
        'material_counts': mat_counts
    }

    conn.close()

    return render_template(
        'admin.html',
        tab=tab,
        feedback=feedback,
        residents_list=residents_list,
        all_transactions=all_txs,
        all_materials=all_materials,
        all_rewards=all_rewards,
        all_redemptions=all_redemptions,
        stats=stats
    )

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    payload = request.get_json(silent=True) or request.form
    qr_code = payload.get('qr_code', '').strip()
    material_id = int(payload.get('material_id', 0))
    quantity = max(1, int(payload.get('quantity', 1)))

    conn = get_db()
    cur = conn.cursor()
    resident = cur.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,)).fetchone()
    material = cur.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()

    if not resident or not material:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid resident QR or material ID'}), 400

    resident = dict(resident)
    material = dict(material)
    pts = quantity * int(material.get('points_per_unit', 1))
    rcp = f'REC-{datetime.now().strftime("%Y%m%d")}-{random.randint(1000, 9999)}'
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cur.execute(
        "INSERT INTO transactions (user_id, material_id, material_name, quantity, points_earned, receipt_no, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (resident['id'], material['id'], material['name'], quantity, pts, rcp, now_str)
    )
    cur.execute("UPDATE users SET points = points + ? WHERE id = ?", (pts, resident['id']))
    conn.commit()
    conn.close()
    sync_to_json()

    return jsonify({
        'success': True,
        'receipt_no': rcp,
        'resident_name': resident['full_name'],
        'points_earned': pts,
        'current_balance': resident['points'] + pts
    })

@app.route('/402')
def trigger_402():
    return render_template('402.html', active_page='402'), 402

@app.errorhandler(PaymentRequired)
def payment_required_error(e):
    return render_template('402.html', active_page='402'), 402

@app.errorhandler(404)
def not_found_error(e):
    return render_template('404.html', active_page='404'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

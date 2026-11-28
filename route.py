import os
import io
import json
import base64
import math
import random
import re
import secrets
import smtplib
import time
import urllib.parse
import urllib.request
import urllib.error
from email.message import EmailMessage
from PIL import Image
import numpy as np
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, sync_to_json, get_current_user, PaymentRequired
from pdf_reports import generate_participation_report_pdf, generate_materials_report_pdf, generate_deposit_receipt_pdf

def save_image_asset(raw_data, subfolder, filename):
    if not raw_data:
        return None
    if hasattr(raw_data, 'read'):
        img_bytes = raw_data.read()
        if not img_bytes:
            return None
        if os.environ.get('VERCEL'):
            encoded = base64.b64encode(img_bytes).decode('ascii')
            return f"data:image/jpeg;base64,{encoded}"
        folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', subfolder)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, filename)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
        return f"/static/uploads/{subfolder}/{filename}"
    if isinstance(raw_data, str) and raw_data.startswith('data:image'):
        try:
            header, encoded = raw_data.split(',', 1)
            img_bytes = base64.b64decode(encoded)
            if not os.environ.get('VERCEL'):
                folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', subfolder)
                os.makedirs(folder_path, exist_ok=True)
                filepath = os.path.join(folder_path, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_bytes)
                return f"/static/uploads/{subfolder}/{filename}"
        except Exception:
            pass
    return raw_data

def get_staff_barangays(cur, user):
    if not user or user.get('role') != 'staff':
        return []
    all_stations = [dict(r) for r in cur.execute("SELECT * FROM stations WHERE status = 'active'").fetchall()]
    staff_barangays = []
    user_name = (user.get('full_name') or '').strip().lower()
    user_station = (user.get('station_name') or '').strip().lower()
    for st in all_stations:
        assigned = (st.get('assigned_staff') or '').strip().lower()
        st_name = (st.get('station_name') or '').strip().lower()
        st_brgy = (st.get('barangay') or '').strip()
        if not st_brgy:
            continue
        if (assigned and assigned == user_name) or (st_name and st_name in user_station) or (st_brgy.lower() in user_station):
            if st_brgy not in staff_barangays:
                staff_barangays.append(st_brgy)
    if not staff_barangays and user.get('station_name'):
        raw_st = user.get('station_name', '').split(',')[0].strip()
        for prefix in ['Barangay ', 'Brgy. ', 'Brgy ']:
            if raw_st.lower().startswith(prefix.lower()):
                raw_st = raw_st[len(prefix):].strip()
        for suffix in [' Collection Hub', ' Hub', ' Station']:
            if raw_st.lower().endswith(suffix.lower()):
                raw_st = raw_st[:-len(suffix)].strip()
        if raw_st:
            staff_barangays.append(raw_st)
    return staff_barangays

def resident_matches_barangays(resident_barangay, staff_barangays):
    if not staff_barangays:
        return True
    r_brgy = (resident_barangay or '').strip().lower()
    if not r_brgy:
        return False
    return r_brgy in [b.strip().lower() for b in staff_barangays]

def _load_env_key(env_key, default_val=''):
    val = os.environ.get(env_key, '').strip()
    if val:
        return val
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.isfile(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    if k.strip() == env_key:
                        return v.strip().strip('"').strip("'")
        except Exception:
            pass
    return default_val

def _send_smtp_email(msg):
    smtp_host = _load_env_key('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(_load_env_key('SMTP_PORT', '587') or '587')
    smtp_user = _load_env_key('SMTP_USER')
    smtp_pass = _load_env_key('SMTP_PASS').replace(' ', '')
    if not smtp_user or not smtp_pass:
        raise RuntimeError('SMTP credentials not configured')
    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, 465, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=12) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

def validate_id_image_with_ai(raw_bytes, side='front', id_type=''):
    if not raw_bytes:
        return False, 'Uploaded file is empty. Please upload a clear photo of your valid ID.'
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img = img.convert('RGB')
        w, h = img.size
        if w < 120 or h < 80:
            return False, 'Image resolution is too small. Please upload a clearer photo of your valid ID.'
        img.thumbnail((960, 960))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=82)
        jpg_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    except Exception:
        return False, 'Could not read image file. Please upload a valid JPG or PNG photo of your ID.'

    api_key = _load_env_key('GEMINI_API_KEY')
    model_name = _load_env_key('GEMINI_MODEL', 'gemini-flash-lite-latest')
    if not api_key:
        return True, 'ID image attached.'

    side_label = 'BACK' if str(side).lower() == 'back' else 'FRONT'
    id_hint = f" (selected type: {id_type})" if id_type else ""
    prompt = (
        f"You are a strict ID document verifier for a Philippine barangay resident portal. "
        f"Inspect this uploaded {side_label} ID photo{id_hint}. "
        f"Determine if this image actually shows a real physical or printed official/government identification card or official PhilSys document "
        f"(such as Philippine National ID / PhilSys card, ePhilID, PhilSys Transaction Slip, Postal ID, Voter's ID or COMELEC Voter's Certificate, Driver's License, UMID, SSS, Passport, PRC, Senior/PWD ID, School/Student ID, or Barangay ID — either its front or back side). "
        f"You MUST REJECT (is_valid_id: false) any non-ID image such as bottles, plastic items, household objects, food, animals, landscapes, memes, cartoons, screenshots of chats/apps, blank paper, or a plain selfie with no ID card. "
        f"Respond with ONLY valid JSON and no markdown fences: "
        f"{{\"is_valid_id\": true or false, \"detected\": \"short 2-5 word description of what is in the image\", \"reason\": \"concise 1-sentence reason for the user\"}}"
    )

    payload = json.dumps({
        'contents': [{
            'parts': [
                {'text': prompt},
                {'inlineData': {'mimeType': 'image/jpeg', 'data': jpg_b64}}
            ]
        }],
        'generationConfig': {
            'temperature': 0.0,
            'maxOutputTokens': 1024,
            'responseMimeType': 'application/json'
        }
    }).encode('utf-8')

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
            parts = resp_data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
            raw_text = ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()
            raw_text = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_text, flags=re.I | re.S).strip()
            m = re.search(r'\{.*\}', raw_text, flags=re.S)
            if m:
                parsed = json.loads(m.group(0))
                is_valid = bool(parsed.get('is_valid_id'))
                detected = str(parsed.get('detected') or '').strip()
                reason = str(parsed.get('reason') or '').strip()
                if is_valid:
                    return True, reason or 'Valid ID card detected.'
                if detected:
                    return False, f"Invalid ID photo (detected: {detected}). Please upload a real {side_label.lower()} photo of your Valid ID."
                return False, reason or f"This image does not appear to be a real Valid ID. Please upload a clear {side_label.lower()} photo of your ID."
    except Exception:
        return True, 'ID image attached.'

    return True, 'ID image attached.'

def find_duplicate_verified_face(cur, descriptor_raw, exclude_user_id, threshold=0.42):
    if not descriptor_raw:
        return None
    try:
        target_list = json.loads(descriptor_raw)
        if not isinstance(target_list, list) or len(target_list) != 128:
            return None
        target = np.array(target_list, dtype=float)
        if not np.all(np.isfinite(target)) or float(np.linalg.norm(target)) < 0.1:
            return None
    except Exception:
        return None

    rows = cur.execute(
        "SELECT id, full_name, barangay, face_descriptor FROM users WHERE role = 'resident' AND is_verified = 1 AND verification_status = 'verified' AND id != ? AND face_descriptor IS NOT NULL AND face_descriptor != ''",
        (exclude_user_id,)
    ).fetchall()

    best_dup = None
    best_dist = threshold
    for row in rows:
        try:
            stored_list = json.loads(row['face_descriptor'])
            if not isinstance(stored_list, list) or len(stored_list) != 128:
                continue
            stored = np.array(stored_list, dtype=float)
            if not np.all(np.isfinite(stored)) or float(np.linalg.norm(stored)) < 0.1:
                continue
            dist = float(np.linalg.norm(target - stored))
            if dist < best_dist:
                best_dist = dist
                best_dup = dict(row)
        except Exception:
            continue
    return best_dup

def build_dynamic_material_chart(txs, active_materials=None):
    agg = {}
    if active_materials:
        for m in active_materials:
            m_name = (m.get('name') if isinstance(m, dict) else str(m)).strip()
            if m_name and m_name not in agg:
                agg[m_name] = {'name': m_name, 'qty': 0, 'points': 0}
    for t in txs:
        m_name = (t.get('material_name') or 'Other').strip()
        qty = int(t.get('quantity') or 0)
        pts = int(t.get('points_earned') or 0)
        if m_name not in agg:
            agg[m_name] = {'name': m_name, 'qty': 0, 'points': 0}
        agg[m_name]['qty'] += qty
        agg[m_name]['points'] += pts
    items = sorted(agg.values(), key=lambda x: (-x['qty'], -x['points'], x['name']))
    sum_qty = sum(x['qty'] for x in items)
    sum_pts = sum(x['points'] for x in items)
    for x in items:
        x['qty_pct'] = round((x['qty'] / sum_qty) * 100) if sum_qty > 0 else 0
        x['pts_pct'] = round((x['points'] / sum_pts) * 100) if sum_pts > 0 else 0
    return items

def register_routes(app):

    RESIDENT_INACTIVITY_TIMEOUT_SECONDS = 600

    @app.before_request
    def enforce_resident_inactivity_timeout():
        if request.endpoint == 'static':
            return None
        if session.get('user_id') and session.get('user_role') == 'resident':
            now_ts = time.time()
            last_activity = session.get('last_activity')
            if last_activity is not None:
                try:
                    if (now_ts - float(last_activity)) >= RESIDENT_INACTIVITY_TIMEOUT_SECONDS:
                        session.clear()
                        if request.path.startswith('/api/'):
                            return jsonify({
                                'status': 'session_expired',
                                'message': 'You have been automatically logged out after 10 minutes of inactivity.',
                                'redirect': url_for('login', reason='timeout')
                            }), 401
                        return redirect(url_for('login', reason='timeout'))
                except (TypeError, ValueError):
                    pass
            session['last_activity'] = now_ts
        return None

    @app.route('/')
    def index():
        return render_template('index.html', active_page='index')

    @app.route('/how-it-works')
    def how_it_works():
        return render_template('how_it_works.html', active_page='how_it_works')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        existing_user = get_current_user()
        if existing_user:
            if existing_user['role'] == 'admin':
                return redirect(url_for('admin'))
            elif existing_user['role'] == 'staff':
                return redirect(url_for('staff'))
            return redirect(url_for('index'))

        error = None
        error_field = None
        message = 'You have been automatically logged out after 10 minutes of inactivity for your security.' if request.args.get('reason') == 'timeout' else None
        email = ''
        lockout_seconds = 0
        attempts_remaining = None
        MAX_LOGIN_ATTEMPTS = 5
        LOCKOUT_MINUTES = 5

        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            client_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '127.0.0.1').split(',')[0].strip()
            now_dt = datetime.now()
            now_str = now_dt.strftime('%Y-%m-%d %H:%M:%S')

            if not email:
                error = 'Please enter your email address.'
                error_field = 'email'
            elif not password:
                error = 'Please enter your password.'
                error_field = 'password'
            else:
                conn = get_db()
                cur = conn.cursor()

                matched = cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()

                if matched:
                    matched = dict(matched)
                    raw_lockout = (matched.get('lockout_until') or '').strip()
                    if raw_lockout:
                        try:
                            lock_dt = datetime.strptime(raw_lockout, '%Y-%m-%d %H:%M:%S')
                            if lock_dt > now_dt:
                                lockout_seconds = int((lock_dt - now_dt).total_seconds())
                                cur.execute(
                                    "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'account_locked', ?)",
                                    (email.lower(), client_ip, now_str)
                                )
                                conn.commit()
                                conn.close()
                                error = 'Account temporarily locked due to too many failed login attempts.'
                                error_field = 'password'
                                return render_template(
                                    'login.html',
                                    error=error,
                                    error_field=error_field,
                                    message=message,
                                    email=email,
                                    lockout_seconds=lockout_seconds,
                                    attempts_remaining=0,
                                    active_page='login'
                                )
                            else:
                                cur.execute("UPDATE users SET failed_login_attempts = 0, lockout_until = NULL WHERE id = ?", (matched['id'],))
                                conn.commit()
                                matched['failed_login_attempts'] = 0
                        except Exception:
                            pass

                    stored_pw = matched.get('password') or ''
                    valid = False
                    needs_rehash = False
                    if stored_pw.startswith(('scrypt:', 'pbkdf2:')):
                        valid = check_password_hash(stored_pw, password)
                    elif stored_pw == password:
                        valid = True
                        needs_rehash = True

                    if valid:
                        if matched.get('status') == 'inactive':
                            cur.execute(
                                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'inactive_account', ?)",
                                (email.lower(), client_ip, now_str)
                            )
                            conn.commit()
                            conn.close()
                            error = f"Your {matched['role']} account has been deactivated by the Administrator."
                            error_field = 'email'
                        else:
                            if needs_rehash:
                                cur.execute(
                                    "UPDATE users SET password = ?, failed_login_attempts = 0, lockout_until = NULL, last_login_at = ? WHERE id = ?",
                                    (generate_password_hash(password), now_str, matched['id'])
                                )
                            else:
                                cur.execute(
                                    "UPDATE users SET failed_login_attempts = 0, lockout_until = NULL, last_login_at = ? WHERE id = ?",
                                    (now_str, matched['id'])
                                )
                            cur.execute(
                                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 1, 'ok', ?)",
                                (email.lower(), client_ip, now_str)
                            )
                            conn.commit()
                            conn.close()
                            session.clear()
                            session.permanent = True
                            session['user_id'] = matched['id']
                            session['user_role'] = matched['role']
                            if matched['role'] == 'admin':
                                return redirect(url_for('admin'))
                            elif matched['role'] == 'staff':
                                return redirect(url_for('staff'))
                            return redirect(url_for('dashboard'))
                    else:
                        new_fails = int(matched.get('failed_login_attempts') or 0) + 1
                        if new_fails >= MAX_LOGIN_ATTEMPTS:
                            unlock_dt = now_dt + timedelta(minutes=LOCKOUT_MINUTES)
                            lockout_seconds = LOCKOUT_MINUTES * 60
                            attempts_remaining = 0
                            cur.execute(
                                "UPDATE users SET failed_login_attempts = ?, lockout_until = ? WHERE id = ?",
                                (new_fails, unlock_dt.strftime('%Y-%m-%d %H:%M:%S'), matched['id'])
                            )
                            cur.execute(
                                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'lockout_triggered', ?)",
                                (email.lower(), client_ip, now_str)
                            )
                            error = f'Too many failed login attempts. Account temporarily locked for {LOCKOUT_MINUTES} minutes.'
                        else:
                            attempts_remaining = MAX_LOGIN_ATTEMPTS - new_fails
                            cur.execute(
                                "UPDATE users SET failed_login_attempts = ? WHERE id = ?",
                                (new_fails, matched['id'])
                            )
                            cur.execute(
                                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'wrong_password', ?)",
                                (email.lower(), client_ip, now_str)
                            )
                            error = f'Incorrect password. {attempts_remaining} attempt{"s" if attempts_remaining != 1 else ""} remaining before temporary lockout.'
                        conn.commit()
                        conn.close()
                        error_field = 'password'
                else:
                    cur.execute(
                        "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'unknown_email', ?)",
                        (email.lower(), client_ip, now_str)
                    )
                    conn.commit()
                    conn.close()
                    error = 'Invalid email address or password.'
                    error_field = 'email'

        info_msg = request.args.get('msg')
        if info_msg:
            message = info_msg

        return render_template(
            'login.html',
            error=error,
            error_field=error_field,
            message=message,
            email=email,
            lockout_seconds=lockout_seconds,
            attempts_remaining=attempts_remaining,
            active_page='login'
        )

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        existing_user = get_current_user()
        if existing_user:
            if existing_user['role'] == 'admin':
                return redirect(url_for('admin'))
            elif existing_user['role'] == 'staff':
                return redirect(url_for('staff'))
            return redirect(url_for('index'))

        if request.args.get('clear_google') == '1':
            session.pop('google_prefill', None)
            return redirect(url_for('register'))

        google_prefill = session.get('google_prefill') or {}
        google_linked_email = str(google_prefill.get('email') or '').strip().lower()

        error = None
        error_field = None
        first_name = str(google_prefill.get('first_name') or '').strip()[:30]
        last_name = str(google_prefill.get('last_name') or '').strip()[:30]
        email = google_linked_email
        if request.method == 'POST':
            honeypot = request.form.get('website', '').strip()
            if honeypot:
                error = 'Registration request could not be processed.'
                error_field = 'email'
                return render_template('register.html', error=error, error_field=error_field, first_name='', last_name='', email='', google_linked_email=google_linked_email, active_page='register')

            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            if google_linked_email and request.form.get('use_google_email') == '1':
                email = google_linked_email
            else:
                email = request.form.get('email', '').strip().lower()
                if google_linked_email and email != google_linked_email:
                    session.pop('google_prefill', None)
                    google_linked_email = ''
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            terms = request.form.get('terms')

            full_name = f"{first_name} {last_name}".strip() if first_name else request.form.get('full_name', '').strip()
            name_pattern = re.compile(r"^[A-Za-zÀ-ÿ\s.\-']{2,30}$")
            email_pattern = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

            if not first_name:
                error = 'Please enter your first name.'
                error_field = 'first_name'
            elif not name_pattern.match(first_name):
                error = 'First name must be 2–30 letters only (no numbers or symbols).'
                error_field = 'first_name'
            elif not last_name:
                error = 'Please enter your last name.'
                error_field = 'last_name'
            elif not name_pattern.match(last_name):
                error = 'Last name must be 2–30 letters only (no numbers or symbols).'
                error_field = 'last_name'
            elif not email or not email_pattern.match(email):
                error = 'Please enter a valid email address.'
                error_field = 'email'
            elif not password:
                error = 'Please enter a password.'
                error_field = 'password'
            elif len(password) < 8 or len(password) > 64:
                error = 'Password must be 8 to 64 characters long.'
                error_field = 'password'
            elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password) or not re.search(r"[^A-Za-z0-9]", password):
                error = 'Password must include uppercase, lowercase, a number, and a special character.'
                error_field = 'password'
            elif password != confirm_password:
                error = 'The passwords you entered do not match.'
                error_field = 'confirm_password'
            elif not terms:
                error = 'You must agree to the Terms and Conditions.'
                error_field = 'terms'
            else:
                conn = get_db()
                cur = conn.cursor()
                existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
                if existing:
                    conn.close()
                    error = 'An account with this email already exists.'
                    error_field = 'email'
                else:
                    qr_code = f'ECO-RES-{random.randint(10000, 99999)}'
                    while cur.execute("SELECT 1 FROM users WHERE qr_code = ?", (qr_code,)).fetchone():
                        qr_code = f'ECO-RES-{random.randint(10000, 99999)}'
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    hashed_pw = generate_password_hash(password)
                    cur.execute(
                        "INSERT INTO users (full_name, first_name, last_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, ?, ?, 'resident', ?, 0, 'active', ?)",
                        (full_name, first_name, last_name, email, hashed_pw, qr_code, created_at)
                    )
                    conn.commit()
                    new_id = cur.lastrowid
                    conn.close()
                    sync_to_json()

                    session.clear()
                    session.permanent = True
                    session['user_id'] = new_id
                    session['user_role'] = 'resident'
                    session['last_activity'] = time.time()
                    return redirect(url_for('dashboard'))

        return render_template('register.html', error=error, error_field=error_field, first_name=first_name, last_name=last_name, email=email, google_linked_email=google_linked_email, active_page='register')

    @app.route('/logout')
    def logout():
        reason = request.args.get('reason')
        session.clear()
        if reason == 'timeout':
            return redirect(url_for('login', reason='timeout'))
        return redirect(url_for('login'))

    @app.route('/account', methods=['GET', 'POST'])
    def account():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        if request.method == 'POST':
            action = request.form.get('action')
            conn = get_db()
            cur = conn.cursor()

            feedback = None
            feedback_type = 'success'
            feedback_field = None

            if action == 'update_profile':
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                email = request.form.get('email', '').strip()

                full_name = f"{first_name} {last_name}".strip() if first_name else request.form.get('full_name', '').strip()

                if not first_name:
                    feedback = 'Please enter your first name.'
                    feedback_type = 'danger'
                    feedback_field = 'first_name'
                elif not last_name:
                    feedback = 'Please enter your last name.'
                    feedback_type = 'danger'
                    feedback_field = 'last_name'
                elif not email:
                    feedback = 'Please enter your email address.'
                    feedback_type = 'danger'
                    feedback_field = 'email'
                elif len(first_name) < 2 or len(first_name) > 30 or len(last_name) < 2 or len(last_name) > 30:
                    feedback = 'Names must be between 2 and 30 characters.'
                    feedback_type = 'danger'
                    feedback_field = 'first_name' if (len(first_name) < 2 or len(first_name) > 30) else 'last_name'
                elif any(char.isdigit() for char in full_name):
                    feedback = 'Names cannot contain numbers.'
                    feedback_type = 'danger'
                    feedback_field = 'first_name' if any(char.isdigit() for char in first_name) else 'last_name'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email, user['id'])).fetchone()
                    if existing:
                        feedback = 'This email is already in use by another account.'
                        feedback_type = 'danger'
                        feedback_field = 'email'
                    else:
                        cur.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user['id']))
                        conn.commit()
                        sync_to_json()
                        feedback = 'Profile details updated successfully.'
                        feedback_type = 'success'

            elif action == 'change_password':
                current_pw = request.form.get('current_password', '').strip()
                new_pw = request.form.get('new_password', '').strip()
                confirm_pw = request.form.get('confirm_password', '').strip()

                is_valid_current = False
                if user['password'] in ['user123', 'admin123', 'staff123', current_pw]:
                    is_valid_current = True
                elif check_password_hash(user['password'], current_pw):
                    is_valid_current = True

                if not current_pw:
                    feedback = 'Please enter your current password.'
                    feedback_type = 'danger'
                    feedback_field = 'current_password'
                elif not is_valid_current:
                    feedback = 'The password you entered is incorrect.'
                    feedback_type = 'danger'
                    feedback_field = 'current_password'
                elif not new_pw:
                    feedback = 'Please enter a new password.'
                    feedback_type = 'danger'
                    feedback_field = 'new_password'
                elif len(new_pw) < 8:
                    feedback = 'New password must be at least 8 characters long.'
                    feedback_type = 'danger'
                    feedback_field = 'new_password'
                elif new_pw != confirm_pw:
                    feedback = 'New passwords do not match.'
                    feedback_type = 'danger'
                    feedback_field = 'confirm_password'
                else:
                    hashed_pw = generate_password_hash(new_pw)
                    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user['id']))
                    conn.commit()
                    sync_to_json()
                    feedback = 'Password changed successfully!'
                    feedback_type = 'success'

            elif action == 'upload_profile_pic':
                pic_file = request.files.get('profile_picture')
                if not pic_file or not pic_file.filename:
                    feedback = 'Please select an image file to upload.'
                    feedback_type = 'danger'
                else:
                    ext = os.path.splitext(pic_file.filename)[1].lower() or '.jpg'
                    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                        ext = '.jpg'
                    saved_profile_path = save_image_asset(pic_file, 'profiles', f"profile_{user['id']}_{int(datetime.now().timestamp())}{ext}")
                    if saved_profile_path:
                        cur.execute("UPDATE users SET profile_image = ? WHERE id = ?", (saved_profile_path, user['id']))
                        conn.commit()
                        sync_to_json()
                        feedback = 'Profile picture updated successfully!'
                        feedback_type = 'success'
                    else:
                        feedback = 'Could not read the uploaded image.'
                        feedback_type = 'danger'

            elif action == 'reset_verification' and user['role'] == 'resident':
                cur.execute(
                    """UPDATE users
                       SET is_verified = 0, verification_status = 'unverified',
                           face_image = NULL, face_descriptor = NULL, id_image = NULL, id_back_image = NULL,
                           verified_at = NULL, verification_notes = '', verify_cooldown_until = NULL
                       WHERE id = ?""",
                    (user['id'],)
                )
                conn.commit()
                sync_to_json()
                feedback = 'Account verification has been reset to Non-Verified for testing.'
                feedback_type = 'success'

            conn.close()
            session['feedback'] = feedback
            session['feedback_type'] = feedback_type
            session['feedback_field'] = feedback_field
            return redirect(url_for('account'))

        feedback = session.pop('feedback', None)
        feedback_type = session.pop('feedback_type', 'success')
        feedback_field = session.pop('feedback_field', None)

        return render_template(
            'account.html',
            active_page='account',
            user=user,
            feedback=feedback,
            feedback_type=feedback_type,
            feedback_field=feedback_field
        )

    @app.route('/verify-account', methods=['GET', 'POST'])
    def verify_account():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        if user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user['role'] == 'admin':
            return redirect(url_for('admin'))

        raw_cooldown = (user.get('verify_cooldown_until') or '').strip()
        if raw_cooldown:
            try:
                until_dt = datetime.strptime(raw_cooldown, '%Y-%m-%d %H:%M:%S')
                now_dt = datetime.now()
                if until_dt > now_dt:
                    diff_secs = int((until_dt - now_dt).total_seconds())
                    hrs = diff_secs // 3600
                    mins = (diff_secs % 3600) // 60
                    rem_str = f"{hrs}h {mins}m" if hrs > 0 else f"{max(1, mins)}m"
                    session['feedback'] = f"Verification is temporarily locked for 1 day after rejection ({rem_str} remaining, available on {until_dt.strftime('%b %d, %Y %I:%M %p')})."
                    session['feedback_type'] = 'danger'
                    return redirect(url_for('dashboard'))
            except Exception:
                pass

        conn_st = get_db()
        stations_rows = [dict(r) for r in conn_st.execute("SELECT DISTINCT barangay, station_name, assigned_staff FROM stations WHERE status = 'active'").fetchall()]
        conn_st.close()
        barangays = sorted(list({r['barangay'] for r in stations_rows if r.get('barangay')} | {'Pinagkawitan'}))

        error = None
        if request.method == 'POST':
            first_name = request.form.get('first_name', '').strip()
            middle_name = request.form.get('middle_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            birthday = request.form.get('birthday', '').strip()
            gender = request.form.get('gender', '').strip()
            contact_number = request.form.get('contact_number', '').strip()
            province = request.form.get('province', '').strip()
            city = request.form.get('city', '').strip()
            barangay = request.form.get('barangay', '').strip()
            address = request.form.get('address', '').strip()
            zip_code = request.form.get('zip_code', '').strip()
            id_type = request.form.get('id_type', '').strip()
            id_file = request.files.get('id_picture')
            id_back_file = request.files.get('id_back_picture')
            id_image_data = request.form.get('id_image_data', '').strip()
            face_image_data = request.form.get('face_image', '').strip()
            face_descriptor_raw = request.form.get('face_descriptor', '').strip()

            existing_face = (user.get('face_image') or '').strip()
            existing_descriptor = (user.get('face_descriptor') or '').strip()
            existing_id_front = (user.get('id_image') or '').strip()
            existing_id_back = (user.get('id_back_image') or '').strip()

            has_id_front = bool((id_file and id_file.filename) or id_image_data or existing_id_front)
            has_id_back = bool((id_back_file and id_back_file.filename) or existing_id_back)
            has_face = bool(face_image_data or existing_face)

            birthday_error = None
            if birthday:
                try:
                    dob = datetime.strptime(birthday, '%Y-%m-%d').date()
                    today = datetime.now().date()
                    if dob > today:
                        birthday_error = 'Birthday cannot be in the future.'
                    else:
                        age_years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                        if age_years < 12:
                            birthday_error = 'Resident must be at least 12 years old to verify.'
                        elif age_years > 120:
                            birthday_error = 'Please enter a valid birth year.'
                except ValueError:
                    birthday_error = 'Please enter a valid birthday (YYYY-MM-DD).'

            verify_name_pattern = re.compile(r"^[A-Za-zÀ-ÿ\s.\-']{2,30}$")
            verify_mid_pattern = re.compile(r"^[A-Za-zÀ-ÿ\s.\-']{1,30}$")

            if not first_name or not last_name:
                error = 'Please enter your first and last name.'
            elif not verify_name_pattern.match(first_name):
                error = 'First name must be 2–30 letters only.'
            elif not verify_name_pattern.match(last_name):
                error = 'Last name must be 2–30 letters only.'
            elif middle_name and not verify_mid_pattern.match(middle_name):
                error = 'Middle name must be 1–30 letters only.'
            elif not birthday:
                error = 'Please enter your birthday.'
            elif birthday_error:
                error = birthday_error
            elif not contact_number or len(contact_number) > 15:
                error = 'Please enter a valid contact number (max 15 characters).'
            elif not province:
                error = 'Please select your Province.'
            elif not city:
                error = 'Please select your City / Municipality.'
            elif not barangay:
                error = 'Please select your Barangay.'
            elif not address or len(address) > 120:
                error = 'Please enter your residential address (max 120 characters).'
            elif not zip_code or not re.match(r"^\d{4}$", zip_code):
                error = 'Please enter a valid 4-digit ZIP code.'
            elif not id_type:
                error = 'Please select your valid ID type.'
            elif not has_id_front:
                error = 'Please upload the FRONT photo of your valid ID.'
            elif not has_id_back:
                error = 'Please upload the BACK photo of your valid ID.'
            elif not has_face:
                error = 'Please capture your face photo to complete verification.'
            else:
                id_validation_err = None
                if id_file and id_file.filename:
                    front_bytes = id_file.read()
                    id_file.seek(0)
                    ok_front, msg_front = validate_id_image_with_ai(front_bytes, 'front', id_type)
                    if not ok_front:
                        id_validation_err = msg_front
                if not id_validation_err and id_back_file and id_back_file.filename:
                    back_bytes = id_back_file.read()
                    id_back_file.seek(0)
                    ok_back, msg_back = validate_id_image_with_ai(back_bytes, 'back', id_type)
                    if not ok_back:
                        id_validation_err = msg_back

                if id_validation_err:
                    error = id_validation_err
                else:
                    name_parts = [p for p in [first_name, middle_name, last_name] if p]
                    full_name = ' '.join(name_parts)

                    if face_image_data.startswith('data:'):
                        saved_face_path = save_image_asset(face_image_data, 'faces', f"resident_{user['id']}.jpg")
                    else:
                        saved_face_path = existing_face or face_image_data

                    saved_descriptor = face_descriptor_raw or existing_descriptor

                    if id_file and id_file.filename:
                        ext = os.path.splitext(id_file.filename)[1].lower() or '.jpg'
                        saved_id_path = save_image_asset(id_file, 'ids', f"id_front_{user['id']}_{int(datetime.now().timestamp())}{ext}")
                    elif id_image_data:
                        saved_id_path = save_image_asset(id_image_data, 'ids', f"id_front_{user['id']}.jpg")
                    else:
                        saved_id_path = existing_id_front

                    if id_back_file and id_back_file.filename:
                        ext_b = os.path.splitext(id_back_file.filename)[1].lower() or '.jpg'
                        saved_id_back_path = save_image_asset(id_back_file, 'ids', f"id_back_{user['id']}_{int(datetime.now().timestamp())}{ext_b}")
                    else:
                        saved_id_back_path = existing_id_back

                    conn = get_db()
                    cur = conn.cursor()
                    cur.execute(
                        """UPDATE users
                           SET full_name = ?, first_name = ?, middle_name = ?, last_name = ?,
                               birthday = ?, gender = ?, contact_number = ?, province = ?, city = ?, barangay = ?,
                               address = ?, zip_code = ?, id_type = ?, id_image = ?, id_back_image = ?,
                               face_image = ?, face_descriptor = ?,
                               is_verified = 0, verification_status = 'pending',
                               verified_at = NULL, verification_notes = ''
                           WHERE id = ?""",
                        (
                            full_name, first_name, middle_name, last_name,
                            birthday, gender, contact_number, province, city, barangay,
                            address, zip_code, id_type, saved_id_path, saved_id_back_path,
                            saved_face_path, saved_descriptor, user['id']
                        )
                    )
                    conn.commit()
                    conn.close()
                    sync_to_json()

                    session['feedback'] = f'Verification submitted for Barangay {barangay}! Your status is now Pending Staff Confirmation.'
                    session['feedback_type'] = 'success'
                    return redirect(url_for('dashboard'))

        feedback = session.pop('feedback', None)
        feedback_type = session.pop('feedback_type', 'info')

        resp = make_response(render_template(
            'verify_account.html',
            active_page='verify_account',
            user=user,
            barangays=barangays,
            error=error,
            feedback=feedback,
            feedback_type=feedback_type
        ))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return resp

    @app.route('/verify-account/edit-request', methods=['POST'])
    def edit_verification_request():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        if user['role'] != 'resident':
            return redirect(url_for('dashboard'))

        if (user.get('verification_status') or '').lower() == 'pending':
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE users SET is_verified = 0, verification_status = 'unverified', verification_notes = ? WHERE id = ?",
                ('Postponed by resident for double-checking and editing.', user['id'])
            )
            conn.commit()
            conn.close()
            sync_to_json()
            session['feedback'] = 'Verification request postponed from Staff Confirmation. Please review and update your details, then resubmit.'
            session['feedback_type'] = 'info'

        return redirect(url_for('verify_account'))

    @app.route('/api/face-login', methods=['POST'])
    def api_face_login():
        data = request.get_json(silent=True) or {}
        descriptor = data.get('descriptor')
        if not descriptor or not isinstance(descriptor, list) or len(descriptor) != 128:
            return jsonify({'status': 'error', 'message': 'Invalid face descriptor.'}), 400

        try:
            target = np.array(descriptor, dtype=float)
            if not np.all(np.isfinite(target)) or float(np.linalg.norm(target)) < 0.1:
                return jsonify({'status': 'error', 'message': 'Invalid facial biometric vector.'}), 400
        except Exception:
            return jsonify({'status': 'error', 'message': 'Invalid face descriptor.'}), 400

        client_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '127.0.0.1').split(',')[0].strip()
        now_dt = datetime.now()
        now_str = now_dt.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, full_name, email, role, status, qr_code, lockout_until, face_descriptor FROM users WHERE role = 'resident' AND is_verified = 1 AND verification_status = 'verified' AND face_descriptor IS NOT NULL AND face_descriptor != ''"
        ).fetchall()

        STRICT_FACE_THRESHOLD = 0.42
        MIN_MARGIN = 0.06
        scored = []
        for row in rows:
            try:
                stored_list = json.loads(row['face_descriptor'])
                if not isinstance(stored_list, list) or len(stored_list) != 128:
                    continue
                stored = np.array(stored_list, dtype=float)
                if not np.all(np.isfinite(stored)):
                    continue
                dist = float(np.linalg.norm(target - stored))
                scored.append((dist, dict(row)))
            except Exception:
                continue

        scored.sort(key=lambda x: x[0])
        best_match = None
        best_dist = 999.0
        if scored and scored[0][0] < STRICT_FACE_THRESHOLD:
            if len(scored) == 1 or (scored[1][0] - scored[0][0]) >= MIN_MARGIN:
                best_dist, best_match = scored[0]

        if not best_match:
            cur.execute(
                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 0, 'face_not_matched', ?)",
                ('face-login', client_ip, now_str)
            )
            conn.commit()
            conn.close()
            return jsonify({'status': 'not_found', 'message': 'Face not recognized. Please ensure good lighting or sign in with your email and password.'}), 404

        raw_lockout = (best_match.get('lockout_until') or '').strip()
        if raw_lockout:
            try:
                lock_dt = datetime.strptime(raw_lockout, '%Y-%m-%d %H:%M:%S')
                if lock_dt > now_dt:
                    conn.close()
                    return jsonify({'status': 'error', 'message': 'This account is temporarily locked due to failed login attempts. Please try again later.'}), 403
            except Exception:
                pass

        if best_match.get('status') == 'inactive':
            conn.close()
            return jsonify({'status': 'error', 'message': 'Your resident account has been deactivated by the Administrator.'}), 403

        cur.execute(
            "UPDATE users SET failed_login_attempts = 0, lockout_until = NULL, last_login_at = ? WHERE id = ?",
            (now_str, best_match['id'])
        )
        cur.execute(
            "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 1, 'face_login_ok', ?)",
            (best_match['email'].lower(), client_ip, now_str)
        )
        conn.commit()
        conn.close()

        session.clear()
        session.permanent = True
        session['user_id'] = best_match['id']
        session['user_role'] = best_match['role']
        confidence = round(max(0.0, min(100.0, (1.0 - best_dist) * 100.0)), 1)
        return jsonify({
            'status': 'success',
            'full_name': best_match['full_name'],
            'confidence': confidence,
            'redirect': url_for('dashboard')
        })

    @app.route('/api/identify-face', methods=['POST'])
    def api_identify_face():
        data = request.get_json(silent=True) or {}
        descriptor = data.get('descriptor')
        if not descriptor or not isinstance(descriptor, list) or len(descriptor) != 128:
            return jsonify({'status': 'error', 'message': 'Invalid face descriptor.'}), 400

        try:
            target = np.array(descriptor, dtype=float)
            if not np.all(np.isfinite(target)) or float(np.linalg.norm(target)) < 0.1:
                return jsonify({'status': 'error', 'message': 'Invalid facial biometric vector.'}), 400
        except Exception:
            return jsonify({'status': 'error', 'message': 'Invalid face descriptor.'}), 400

        conn = get_db()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, full_name, email, qr_code, points, face_descriptor, face_image FROM users WHERE role = 'resident' AND is_verified = 1 AND verification_status = 'verified' AND face_descriptor IS NOT NULL AND face_descriptor != ''"
        ).fetchall()
        conn.close()

        STRICT_FACE_THRESHOLD = 0.42
        MIN_MARGIN = 0.06
        scored = []
        for row in rows:
            try:
                stored_list = json.loads(row['face_descriptor'])
                if not isinstance(stored_list, list) or len(stored_list) != 128:
                    continue
                stored = np.array(stored_list, dtype=float)
                if not np.all(np.isfinite(stored)):
                    continue
                dist = float(np.linalg.norm(target - stored))
                scored.append((dist, dict(row)))
            except Exception:
                continue

        scored.sort(key=lambda x: x[0])
        best_match = None
        best_dist = 999.0
        if scored and scored[0][0] < STRICT_FACE_THRESHOLD:
            if len(scored) == 1 or (scored[1][0] - scored[0][0]) >= MIN_MARGIN:
                best_dist, best_match = scored[0]

        if best_match:
            confidence = round(max(0.0, min(100.0, (1.0 - best_dist) * 100.0)), 1)
            return jsonify({
                'status': 'success',
                'resident': {
                    'id': best_match['id'],
                    'full_name': best_match['full_name'],
                    'email': best_match['email'],
                    'qr_code': best_match['qr_code'],
                    'points': best_match['points'],
                    'confidence': confidence
                }
            })
        return jsonify({'status': 'not_found', 'message': 'No matching verified resident found.'}), 404

    @app.route('/dashboard')
    def dashboard():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        if user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user['role'] == 'admin':
            return redirect(url_for('admin'))

        conn = get_db()
        cur = conn.cursor()
        user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        user_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        active_materials = [dict(r) for r in cur.execute("SELECT name FROM materials WHERE status = 'active' ORDER BY id ASC").fetchall()]
        conn.close()

        bottle_count = 0
        can_count = 0
        paper_count = 0
        glass_count = 0
        total_items = 0
        lifetime_points = 0

        for t in user_txs:
            name = t.get('material_name', '').lower()
            qty = int(t.get('quantity', 0))
            pts = int(t.get('points_earned', 0))
            total_items += qty
            lifetime_points += pts
            if 'bottle' in name or 'plastic' in name:
                bottle_count += qty
            elif 'can' in name:
                can_count += qty
            elif 'paper' in name or 'cardboard' in name:
                paper_count += qty
            else:
                glass_count += qty

        other_count = paper_count + glass_count

        diverted_kg = round(
            (bottle_count * 0.035) +
            (can_count * 0.015) +
            (paper_count * 1.0) +
            (glass_count * 0.25),
            1
        )

        daily_timeline = {}
        for t in reversed(user_txs):
            dt = str(t.get('created_at', ''))[:10]
            if not dt:
                continue
            if dt not in daily_timeline:
                daily_timeline[dt] = {'items': 0, 'points': 0}
            daily_timeline[dt]['items'] += int(t.get('quantity', 0))
            daily_timeline[dt]['points'] += int(t.get('points_earned', 0))

        if len(daily_timeline) < 4 and daily_timeline:
            sorted_dates = sorted(daily_timeline.keys())
        elif not daily_timeline:
            sorted_dates = [datetime.now().strftime('%Y-%m-%d')]
            daily_timeline[sorted_dates[0]] = {'items': 0, 'points': 0}
        else:
            sorted_dates = sorted(daily_timeline.keys())[-7:]

        timeline_labels = sorted_dates
        timeline_items = [daily_timeline[k]['items'] for k in sorted_dates]
        timeline_points = [daily_timeline[k]['points'] for k in sorted_dates]

        cat_breakdown = {
            'Plastic': {'name': 'Plastic Bottles', 'qty': bottle_count, 'color': '#198754'},
            'Metal': {'name': 'Aluminum Cans', 'qty': can_count, 'color': '#0d6efd'},
            'Paper': {'name': 'Paper & Cardboard', 'qty': paper_count, 'color': '#f59e0b'},
            'Glass': {'name': 'Glass & Others', 'qty': glass_count, 'color': '#8b5cf6'}
        }
        for k in cat_breakdown:
            cat_breakdown[k]['share'] = round((cat_breakdown[k]['qty'] / max(1, total_items)) * 100, 1)

        user_stats = {
            'total_items': total_items,
            'lifetime_points': lifetime_points,
            'diverted_kg': diverted_kg,
            'bottle_count': bottle_count,
            'can_count': can_count,
            'paper_count': paper_count,
            'glass_count': glass_count,
            'other_count': other_count,
            'cat_breakdown': cat_breakdown,
            'dynamic_materials': build_dynamic_material_chart(user_txs, active_materials),
            'timeline_labels': timeline_labels,
            'timeline_items': timeline_items,
            'timeline_points': timeline_points
        }

        feedback = session.pop('feedback', None)
        feedback_type = session.pop('feedback_type', 'success')

        return render_template(
            'dashboard.html',
            active_page='dashboard',
            user_transactions=user_txs,
            user_redemptions=user_redemptions,
            bottle_count=bottle_count,
            can_count=can_count,
            other_count=other_count,
            user_stats=user_stats,
            feedback=feedback,
            feedback_type=feedback_type
        )

    @app.route('/ecopoints')
    def ecopoints():
        user = get_current_user()
        if user and user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user and user['role'] == 'admin':
            return redirect(url_for('admin'))
        if not user:
            return redirect(url_for('login'))

        conn = get_db()
        cur = conn.cursor()
        user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        active_materials = [dict(r) for r in cur.execute("SELECT name FROM materials WHERE status = 'active' ORDER BY id ASC").fetchall()]
        conn.close()

        bottle_points = 0
        can_points = 0
        paper_points = 0
        glass_points = 0
        for t in user_txs:
            name = t.get('material_name', '').lower()
            pts = int(t.get('points_earned', 0))
            if 'bottle' in name or 'plastic' in name:
                bottle_points += pts
            elif 'can' in name or 'metal' in name or 'aluminum' in name:
                can_points += pts
            elif 'paper' in name or 'cardboard' in name:
                paper_points += pts
            else:
                glass_points += pts

        total_earned_points = bottle_points + can_points + paper_points + glass_points
        total = max(1, total_earned_points)
        bottle_pct = round((bottle_points / total) * 100) if total_earned_points > 0 else 0
        can_pct = round((can_points / total) * 100) if total_earned_points > 0 else 0
        paper_pct = round((paper_points / total) * 100) if total_earned_points > 0 else 0
        glass_pct = round((glass_points / total) * 100) if total_earned_points > 0 else 0
        other_points = paper_points + glass_points
        other_pct = round((other_points / total) * 100) if total_earned_points > 0 else 0

        return render_template(
            'ecopoints.html',
            active_page='ecopoints',
            user_transactions=user_txs,
            dynamic_materials=build_dynamic_material_chart(user_txs, active_materials),
            total_earned_points=total_earned_points,
            bottle_points=bottle_points,
            can_points=can_points,
            paper_points=paper_points,
            glass_points=glass_points,
            other_points=other_points,
            bottle_pct=bottle_pct,
            can_pct=can_pct,
            paper_pct=paper_pct,
            glass_pct=glass_pct,
            other_pct=other_pct
        )

    @app.route('/history')
    def history():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        if user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user['role'] == 'admin':
            return redirect(url_for('admin'))

        conn = get_db()
        cur = conn.cursor()
        user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        active_materials = [dict(r) for r in cur.execute("SELECT name FROM materials WHERE status = 'active' ORDER BY id ASC").fetchall()]
        conn.close()

        return render_template('history.html', active_page='history', user_transactions=user_txs)

    @app.route('/reward-history')
    def reward_history():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        if user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user['role'] == 'admin':
            return redirect(url_for('admin'))

        message = session.pop('message', None)
        message_type = session.pop('message_type', 'success')

        conn = get_db()
        cur = conn.cursor()
        user_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        conn.close()

        return render_template('reward_history.html', active_page='reward_history', redemptions=user_redemptions, message=message, message_type=message_type)

    @app.route('/confirm-received', methods=['POST'])
    def confirm_received():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        redemption_id = int(request.form.get('redemption_id', 0))
        conn = get_db()
        cur = conn.cursor()
        redemp = cur.execute("SELECT * FROM redemptions WHERE id = ? AND user_id = ? AND status = 'released'", (redemption_id, user['id'])).fetchone()

        if redemp:
            redemp = dict(redemp)
            cur.execute("UPDATE redemptions SET status = 'received' WHERE id = ?", (redemption_id,))
            conn.commit()
            sync_to_json()
            session['message'] = f"Reward {redemp['reward_title']} ({redemp['redemption_code']}) confirmed received! Thank you for participating in EcoCoins recycling."
            session['message_type'] = 'success'
        else:
            session['message'] = "Voucher not found or not yet released by Barangay Staff."
            session['message_type'] = 'danger'

        conn.close()
        return redirect(url_for('reward_history'))

    @app.route('/confirm-claim', methods=['POST'])
    def confirm_claim():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        prompt = session.pop('claim_prompt', None)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET cancel_count = 0 WHERE id = ?", (user['id'],))
        conn.commit()
        conn.close()

        if prompt:
            session['message'] = f"Reward claim for {prompt['title']} confirmed! Voucher code {prompt['code']} is ready for handover."
        else:
            session['message'] = "Reward claim successfully confirmed! Ready for handover."
        session['message_type'] = 'success'
        return redirect(url_for('rewards'))

    @app.route('/cancel-claim', methods=['POST'])
    def cancel_claim():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        prompt = session.pop('claim_prompt', None)
        redemption_id = int(request.form.get('redemption_id', 0))
        if not redemption_id and prompt:
            redemption_id = int(prompt.get('redemption_id', 0))

        conn = get_db()
        cur = conn.cursor()
        redemp = cur.execute("SELECT * FROM redemptions WHERE id = ? AND user_id = ? AND status = 'claimed'", (redemption_id, user['id'])).fetchone()

        if redemp:
            redemp = dict(redemp)
            cur.execute("UPDATE users SET points = points + ? WHERE id = ?", (redemp['points_spent'], user['id']))
            cur.execute("UPDATE rewards SET stock = stock + 1 WHERE id = ?", (redemp['reward_id'],))
            cur.execute("DELETE FROM redemptions WHERE id = ?", (redemption_id,))

            curr_cancels = int(user.get('cancel_count') or 0) + 1
            now = datetime.now()
            if curr_cancels >= 3:
                timeout_until = (now + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE users SET cancel_count = ?, claim_timeout_until = ? WHERE id = ?", (curr_cancels, timeout_until, user['id']))
                session['message'] = f"Claim cancelled and {redemp['points_spent']} EcoPoints refunded. Warning: Due to persistent cancellations, reward claiming is timed out for 5 minutes."
                session['message_type'] = 'danger'
            elif curr_cancels >= 2:
                timeout_until = (now + timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE users SET cancel_count = ?, claim_timeout_until = ? WHERE id = ?", (curr_cancels, timeout_until, user['id']))
                session['message'] = f"Claim cancelled and {redemp['points_spent']} EcoPoints refunded. Notice: Due to repeated cancellations, reward claiming is timed out for 2 minutes."
                session['message_type'] = 'danger'
            else:
                cur.execute("UPDATE users SET cancel_count = ? WHERE id = ?", (curr_cancels, user['id']))
                session['message'] = f"Claim cancelled and {redemp['points_spent']} EcoPoints have been refunded to your account."
                session['message_type'] = 'success'

            conn.commit()
            sync_to_json()
        else:
            session['message'] = "No active claim found to cancel or claim has already been processed."
            session['message_type'] = 'danger'

        conn.close()
        return redirect(url_for('rewards'))

    @app.route('/rewards', methods=['GET', 'POST'])
    def rewards():
        user = get_current_user()
        if user and user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user and user['role'] == 'admin':
            return redirect(url_for('admin'))

        if request.method == 'POST':
            if not user:
                return redirect(url_for('login'))

            if user.get('role') == 'resident' and not user.get('is_verified'):
                session['message'] = 'Only Verified Residents can redeem rewards. Please complete Facial Recognition and wait for Staff confirmation.'
                session['message_type'] = 'danger'
                return redirect(url_for('rewards'))

            if user.get('claim_timeout_until'):
                try:
                    timeout_dt = datetime.strptime(user['claim_timeout_until'], '%Y-%m-%d %H:%M:%S')
                    if datetime.now() < timeout_dt:
                        rem = int((timeout_dt - datetime.now()).total_seconds())
                        rem_m, rem_s = divmod(rem, 60)
                        session['message'] = f"Reward claiming is on cooldown due to repeated cancellations. Please wait {rem_m}m {rem_s}s before redeeming again."
                        session['message_type'] = 'danger'
                        return redirect(url_for('rewards'))
                except Exception:
                    pass

            conn = get_db()
            cur = conn.cursor()
            reward_id = int(request.form.get('reward_id', 0))
            reward = cur.execute("SELECT * FROM rewards WHERE id = ?", (reward_id,)).fetchone()

            if not reward:
                session['message'] = 'Selected reward not found.'
                session['message_type'] = 'danger'
            else:
                reward = dict(reward)
                if user['points'] < reward['points_required']:
                    session['message'] = 'Insufficient EcoPoints balance.'
                    session['message_type'] = 'danger'
                elif reward.get('stock', 0) <= 0:
                    session['message'] = 'This reward is out of stock.'
                    session['message_type'] = 'danger'
                else:
                    code = f'RDM-{random.randint(10000, 99999)}'
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    cur.execute(
                        "INSERT INTO redemptions (user_id, reward_id, reward_title, points_spent, redemption_code, status, created_at) VALUES (?, ?, ?, ?, ?, 'claimed', ?)",
                        (user['id'], reward['id'], reward['title'], reward['points_required'], code, now_str)
                    )
                    redemption_id = cur.lastrowid
                    cur.execute("UPDATE users SET points = MAX(0, points - ?) WHERE id = ?", (reward['points_required'], user['id']))
                    cur.execute("UPDATE rewards SET stock = MAX(0, stock - 1) WHERE id = ?", (reward['id'],))
                    conn.commit()

                    session['claim_prompt'] = {
                        'redemption_id': redemption_id,
                        'code': code,
                        'title': reward['title'],
                        'points': reward['points_required'],
                        'started_at': now_str
                    }
                    sync_to_json()

            conn.close()
            return redirect(url_for('rewards'))

        message = session.pop('message', None)
        message_type = session.pop('message_type', 'success')

        claim_prompt = session.get('claim_prompt')
        claim_remaining_seconds = 0
        if claim_prompt:
            try:
                started_dt = datetime.strptime(claim_prompt['started_at'], '%Y-%m-%d %H:%M:%S')
                elapsed = (datetime.now() - started_dt).total_seconds()
            except Exception:
                elapsed = 25
            if elapsed >= 20:
                session.pop('claim_prompt', None)
                if user:
                    conn_auto = get_db()
                    cur_auto = conn_auto.cursor()
                    cur_auto.execute("UPDATE users SET cancel_count = 0 WHERE id = ?", (user['id'],))
                    conn_auto.commit()
                    conn_auto.close()
                claim_prompt = None
                claim_remaining_seconds = 0
            else:
                claim_remaining_seconds = max(1, int(20 - elapsed))

        claim_cooldown_seconds = 0
        if user and user.get('claim_timeout_until'):
            try:
                timeout_dt = datetime.strptime(user['claim_timeout_until'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() < timeout_dt:
                    claim_cooldown_seconds = int((timeout_dt - datetime.now()).total_seconds())
                else:
                    conn_cd = get_db()
                    cur_cd = conn_cd.cursor()
                    cur_cd.execute("UPDATE users SET claim_timeout_until = NULL WHERE id = ?", (user['id'],))
                    conn_cd.commit()
                    conn_cd.close()
            except Exception:
                pass

        conn = get_db()
        cur = conn.cursor()
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
            message_type=message_type,
            claim_prompt=claim_prompt,
            claim_remaining_seconds=claim_remaining_seconds,
            claim_cooldown_seconds=claim_cooldown_seconds
        )

    @app.route('/staff', methods=['GET', 'POST'])
    def staff():
        user = get_current_user()
        if not user or user['role'] not in ['staff', 'admin']:
            return redirect(url_for('login'))

        tab = request.form.get('tab') or request.args.get('tab', 'dashboard')
        prefill_qr = request.args.get('qr', '').strip()

        if request.method == 'POST':
            feedback = None
            feedback_type = 'success'
            receipt = None
            conn = get_db()
            cur = conn.cursor()
            staff_barangays = get_staff_barangays(cur, user)

            action = request.form.get('staff_action')
            if action == 'record_deposit':
                qr_code = request.form.get('qr_code', '').strip()
                material_id = int(request.form.get('material_id', 0))
                quantity = max(1, int(request.form.get('quantity', 1)))

                resident = cur.execute("SELECT * FROM users WHERE qr_code = ?", (qr_code,)).fetchone()
                material = cur.execute("SELECT * FROM materials WHERE id = ?", (material_id,)).fetchone()

                if not resident:
                    feedback = 'Resident QR Code not found.'
                    feedback_type = 'danger'
                elif resident['role'] != 'resident':
                    feedback = 'EcoPoints can only be awarded to registered resident accounts. Staff and admin accounts cannot receive points.'
                    feedback_type = 'danger'
                elif not (int(resident['is_verified'] or 0) == 1 and (resident['verification_status'] or '') == 'verified'):
                    feedback = f"Non-Verified Resident Detected ({resident['full_name']}). Resident must complete Facial Recognition and Barangay Staff confirmation before scanning QR or earning EcoPoints."
                    feedback_type = 'danger'
                elif user['role'] == 'staff' and staff_barangays and not resident_matches_barangays(resident['barangay'], staff_barangays):
                    feedback = f"Barangay Mismatch: {resident['full_name']} belongs to Barangay {resident['barangay'] or 'Unassigned'}, not your assigned station (Barangay {', '.join(staff_barangays)})."
                    feedback_type = 'danger'
                elif not material:
                    feedback = 'Invalid material selected.'
                    feedback_type = 'danger'
                else:
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

                    new_total = resident['points'] + pts
                    receipt = {
                        'receipt_no': rcp,
                        'resident_name': resident['full_name'],
                        'qr_code': resident['qr_code'],
                        'material_name': material['name'],
                        'quantity': quantity,
                        'unit': material.get('unit', 'piece'),
                        'points_earned': pts,
                        'new_total_points': new_total,
                        'created_at': now_str
                    }
                    feedback = f"Transaction {rcp} recorded successfully! +{pts} EcoPoints awarded to {resident['full_name']}."
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'release_reward':
                redemption_id = int(request.form.get('redemption_id', 0))
                redemp = cur.execute("SELECT * FROM redemptions WHERE id = ?", (redemption_id,)).fetchone()
                if redemp:
                    redemp = dict(redemp)
                    cur.execute("UPDATE redemptions SET status = 'released' WHERE id = ?", (redemption_id,))
                    conn.commit()
                    feedback = f"Reward voucher {redemp['redemption_code']} released. Waiting for resident confirmation."
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'approve_verification':
                resident_id = int(request.form.get('resident_id', 0))
                target_res = cur.execute("SELECT * FROM users WHERE id = ? AND role = 'resident'", (resident_id,)).fetchone()
                if target_res:
                    target_res = dict(target_res)
                    if user['role'] == 'staff' and staff_barangays and not resident_matches_barangays(target_res.get('barangay'), staff_barangays):
                        feedback = f"Access Denied: {target_res['full_name']} belongs to Barangay {target_res.get('barangay') or 'Unassigned'}, not your assigned station."
                        feedback_type = 'danger'
                    else:
                        dup_face = find_duplicate_verified_face(cur, target_res.get('face_descriptor'), resident_id)
                        if dup_face:
                            cooldown_until = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                            reject_note = f"Rejected: Duplicate facial biometrics detected (matches verified resident {dup_face['full_name']}). You may reapply after 24 hours."
                            cur.execute(
                                "UPDATE users SET is_verified = 0, verification_status = 'rejected', face_image = NULL, face_descriptor = NULL, id_image = NULL, id_back_image = NULL, verified_at = NULL, verification_notes = ?, verify_cooldown_until = ? WHERE id = ?",
                                (reject_note, cooldown_until, resident_id)
                            )
                            conn.commit()
                            sync_to_json()
                            feedback = f"Verification Rejected (Duplicate Face): {target_res['full_name']}'s facial scan matches an already-verified resident ({dup_face['full_name']}). Resident cannot reapply for 24 hours."
                            feedback_type = 'danger'
                        else:
                            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            cur.execute(
                                "UPDATE users SET is_verified = 1, verification_status = 'verified', verified_at = ?, verification_notes = ?, verify_cooldown_until = NULL WHERE id = ?",
                                (now_str, f"Confirmed by {user['full_name']}", resident_id)
                            )
                            conn.commit()
                            sync_to_json()
                            feedback = f"{target_res['full_name']} ({target_res.get('barangay') or 'Barangay'}) is now a Verified Resident!"
                            feedback_type = 'success'
            elif action == 'reject_verification':
                resident_id = int(request.form.get('resident_id', 0))
                reason = request.form.get('reject_reason', 'Submitted details or photo did not match. Please try again after 24 hours.').strip()
                target_res = cur.execute("SELECT * FROM users WHERE id = ? AND role = 'resident'", (resident_id,)).fetchone()
                if target_res:
                    target_res = dict(target_res)
                    if user['role'] == 'staff' and staff_barangays and not resident_matches_barangays(target_res.get('barangay'), staff_barangays):
                        feedback = f"Access Denied: {target_res['full_name']} belongs to Barangay {target_res.get('barangay') or 'Unassigned'}, not your assigned station."
                        feedback_type = 'danger'
                    else:
                        cooldown_until = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute(
                            "UPDATE users SET is_verified = 0, verification_status = 'rejected', face_image = NULL, face_descriptor = NULL, id_image = NULL, id_back_image = NULL, verified_at = NULL, verification_notes = ?, verify_cooldown_until = ? WHERE id = ?",
                            (reason, cooldown_until, resident_id)
                        )
                        conn.commit()
                        sync_to_json()
                        feedback = f"Verification request for {target_res['full_name']} was rejected. Resident cannot reapply for 24 hours."
                        feedback_type = 'danger'

            conn.close()
            session['feedback'] = feedback
            session['feedback_type'] = feedback_type
            if receipt:
                session['receipt'] = receipt
            if action == 'record_deposit' and qr_code:
                return redirect(url_for('staff', tab=tab, qr=qr_code))
            return redirect(url_for('staff', tab=tab))

        feedback = session.pop('feedback', None)
        feedback_type = session.pop('feedback_type', 'success')
        receipt = session.pop('receipt', None)

        conn = get_db()
        cur = conn.cursor()
        staff_barangays = get_staff_barangays(cur, user)

        all_txs_raw = [dict(r) for r in cur.execute("""
            SELECT t.*, u.full_name AS resident_name, u.first_name AS first_name, u.qr_code AS resident_qr, u.barangay AS resident_barangay
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
        """).fetchall()]
        for tx_row in all_txs_raw:
            fn = (tx_row.get('first_name') or '').strip()
            if not fn:
                rn = (tx_row.get('resident_name') or 'Resident').strip()
                fn = rn.split()[0] if rn else 'Resident'
            tx_row['first_name'] = fn

        residents_raw = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY full_name ASC").fetchall()]
        all_materials = [dict(r) for r in cur.execute("SELECT * FROM materials WHERE status = 'active' ORDER BY id ASC").fetchall()]
        all_redemptions_raw = [dict(r) for r in cur.execute("""
            SELECT r.*, u.full_name AS resident_name, u.qr_code AS resident_qr, u.barangay AS resident_barangay
            FROM redemptions r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """).fetchall()]

        if user['role'] == 'staff' and staff_barangays:
            residents_list = [r for r in residents_raw if resident_matches_barangays(r.get('barangay'), staff_barangays)]
            all_txs = [t for t in all_txs_raw if resident_matches_barangays(t.get('resident_barangay'), staff_barangays)]
            all_redemptions = [r for r in all_redemptions_raw if resident_matches_barangays(r.get('resident_barangay'), staff_barangays)]
        else:
            residents_list = residents_raw
            all_txs = all_txs_raw
            all_redemptions = all_redemptions_raw

        all_redemptions.sort(
            key=lambda r: 0 if (r.get('status') or '') == 'claimed' else (1 if (r.get('status') or '') == 'released' else 2)
        )

        total_points_distributed = sum(int(t.get('points_earned', 0)) for t in all_txs)
        pending_claims_count = sum(1 for r in all_redemptions if r.get('status') == 'claimed')
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_txs_count = sum(1 for t in all_txs if t.get('created_at', '').startswith(today_str))

        mat_counts = {'Plastic Bottles': 0, 'Cans': 0, 'Others': 0}
        cat_breakdown = {
            'Plastic': {'name': 'Plastic Bottles', 'qty': 0, 'color': '#198754'},
            'Metal': {'name': 'Aluminum Cans', 'qty': 0, 'color': '#0d6efd'},
            'Paper': {'name': 'Paper & Cardboard', 'qty': 0, 'color': '#f59e0b'},
            'Glass': {'name': 'Glass & Others', 'qty': 0, 'color': '#8b5cf6'}
        }
        total_items_collected = 0
        for t in all_txs:
            m_name = str(t.get('material_name', '')).lower()
            q = int(t.get('quantity', 0))
            total_items_collected += q
            if 'bottle' in m_name or 'plastic' in m_name:
                mat_counts['Plastic Bottles'] += q
                cat_breakdown['Plastic']['qty'] += q
            elif 'can' in m_name:
                mat_counts['Cans'] += q
                cat_breakdown['Metal']['qty'] += q
            elif 'paper' in m_name or 'cardboard' in m_name:
                mat_counts['Others'] += q
                cat_breakdown['Paper']['qty'] += q
            else:
                mat_counts['Others'] += q
                cat_breakdown['Glass']['qty'] += q

        for k in cat_breakdown:
            cat_breakdown[k]['share'] = round((cat_breakdown[k]['qty'] / max(1, total_items_collected)) * 100, 1)

        diverted_kg = round(
            (cat_breakdown['Plastic']['qty'] * 0.035) +
            (cat_breakdown['Metal']['qty'] * 0.015) +
            (cat_breakdown['Paper']['qty'] * 1.0) +
            (cat_breakdown['Glass']['qty'] * 0.25),
            1
        )

        daily_timeline = {}
        for t in reversed(all_txs):
            dt = str(t.get('created_at', ''))[:10]
            if not dt:
                continue
            if dt not in daily_timeline:
                daily_timeline[dt] = {'items': 0, 'points': 0}
            daily_timeline[dt]['items'] += int(t.get('quantity', 0))
            daily_timeline[dt]['points'] += int(t.get('points_earned', 0))

        if len(daily_timeline) < 5:
            base_dates = ['2026-10-22', '2026-10-26', '2026-10-29', '2026-10-31', '2026-11-01']
            for d in base_dates:
                if d not in daily_timeline:
                    daily_timeline[d] = {'items': 0, 'points': 0}

        sorted_dates = sorted(daily_timeline.keys())[-7:]
        timeline_labels = sorted_dates
        timeline_items = [daily_timeline[k]['items'] for k in sorted_dates]
        timeline_points = [daily_timeline[k]['points'] for k in sorted_dates]

        svg_w, svg_h = 560, 240
        pad_l, pad_r, pad_t, pad_b = 40, 24, 25, 35
        plot_w = svg_w - pad_l - pad_r
        plot_h = svg_h - pad_t - pad_b
        n_dates = len(sorted_dates)

        max_it = max(timeline_items) if timeline_items and max(timeline_items) > 0 else 10
        max_pt = max(timeline_points) if timeline_points and max(timeline_points) > 0 else 50
        max_it = int(math.ceil(max_it / 5.0) * 5)
        max_pt = int(math.ceil(max_pt / 25.0) * 25)

        items_coords = []
        pts_coords = []
        for i in range(n_dates):
            x = pad_l + (plot_w * i / (n_dates - 1)) if n_dates > 1 else pad_l + plot_w / 2
            y_it = pad_t + plot_h - (plot_h * (timeline_items[i] / max_it))
            y_pt = pad_t + plot_h - (plot_h * (timeline_points[i] / max_pt))
            items_coords.append({'x': round(x, 1), 'y': round(y_it, 1), 'val': timeline_items[i]})
            pts_coords.append({'x': round(x, 1), 'y': round(y_pt, 1), 'val': timeline_points[i]})

        def build_curve(coords):
            if not coords:
                return '', ''
            p = f"M {coords[0]['x']},{coords[0]['y']}"
            for i in range(1, len(coords)):
                prev = coords[i-1]
                curr = coords[i]
                mx = round((prev['x'] + curr['x']) / 2, 1)
                p += f" C {mx},{prev['y']} {mx},{curr['y']} {curr['x']},{curr['y']}"
            area = f"{p} L {coords[-1]['x']},{pad_t + plot_h} L {coords[0]['x']},{pad_t + plot_h} Z"
            return p, area

        p_items, a_items = build_curve(items_coords)
        p_pts, a_pts = build_curve(pts_coords)

        x_axis_labels = []
        for i, dt in enumerate(sorted_dates):
            x = pad_l + (plot_w * i / (n_dates - 1)) if n_dates > 1 else pad_l + plot_w / 2
            short_lbl = dt[5:].replace('-', '/')
            x_axis_labels.append({'x': round(x, 1), 'y': svg_h - 12, 'text': short_lbl})

        grid_lines = []
        for g_idx in range(5):
            frac = g_idx / 4.0
            y_val = pad_t + plot_h - (plot_h * frac)
            it_val = int(round(max_it * frac))
            grid_lines.append({
                'y': round(y_val, 1),
                'x1': pad_l,
                'x2': svg_w - pad_r,
                'it_label': it_val
            })

        circ = 339.29
        donut_slices = []
        cur_offset = 0.0
        tot_donut = max(1, total_items_collected)
        donut_specs = [
            ('Plastics', cat_breakdown['Plastic']['qty'], '#10b981', 'Plastics'),
            ('Cans', cat_breakdown['Metal']['qty'], '#3b82f6', 'Cans & Metal'),
            ('Paper', cat_breakdown['Paper']['qty'], '#f59e0b', 'Paper & Card'),
            ('Glass/Other', cat_breakdown['Glass']['qty'], '#8b5cf6', 'Glass & Others')
        ]
        for name, qty, color, label in donut_specs:
            if qty > 0:
                seg_len = round((qty / tot_donut) * circ, 2)
                donut_slices.append({
                    'name': name,
                    'label': label,
                    'qty': qty,
                    'pct': round((qty / tot_donut) * 100, 1),
                    'color': color,
                    'dash': f"{seg_len} {round(circ, 2)}",
                    'offset': round(-cur_offset, 2)
                })
                cur_offset += seg_len

        staff_svg = {
            'w': svg_w,
            'h': svg_h,
            'p_items': p_items,
            'a_items': a_items,
            'p_pts': p_pts,
            'a_pts': a_pts,
            'items_coords': items_coords,
            'pts_coords': pts_coords,
            'x_labels': x_axis_labels,
            'grid_lines': grid_lines,
            'donut_slices': donut_slices,
            'total_donut': total_items_collected
        }

        staff_stats = {
            'total_deposits': len(all_txs),
            'today_deposits': today_txs_count,
            'total_points': total_points_distributed,
            'pending_claims': pending_claims_count,
            'total_residents': len(residents_list),
            'recent_deposits': all_txs[:6],
            'pending_claims_list': [r for r in all_redemptions if r.get('status') == 'claimed'][:3],
            'total_items': total_items_collected,
            'diverted_kg': diverted_kg,
            'cat_breakdown': cat_breakdown,
            'dynamic_materials': build_dynamic_material_chart(all_txs),
            'timeline_labels': timeline_labels,
            'timeline_items': timeline_items,
            'timeline_points': timeline_points,
            'svg': staff_svg
        }

        prefill_resident = None
        if prefill_qr:
            for r in residents_list:
                if r.get('qr_code') == prefill_qr:
                    prefill_resident = r
                    break

        pending_verifications = []
        verified_verifications = []
        for r in residents_list:
            v_status = (r.get('verification_status') or 'unverified').lower()
            if v_status == 'pending':
                dup_match = find_duplicate_verified_face(cur, r.get('face_descriptor'), r['id'])
                r['duplicate_face_match'] = dup_match['full_name'] if dup_match else None
                r['has_face_scan'] = bool((r.get('face_descriptor') or '').strip())
                pending_verifications.append(r)
            elif v_status == 'verified' and int(r.get('is_verified') or 0) == 1:
                verified_verifications.append(r)

        conn.close()

        return render_template(
            'staff.html',
            tab=tab,
            feedback=feedback,
            feedback_type=feedback_type,
            receipt=receipt,
            prefill_qr=prefill_qr,
            prefill_resident=prefill_resident,
            residents_list=residents_list,
            all_materials=all_materials,
            all_transactions=all_txs,
            all_redemptions=all_redemptions,
            staff_stats=staff_stats,
            staff_svg=staff_svg,
            pending_verifications=pending_verifications,
            verified_verifications=verified_verifications,
            pending_verifications_count=len(pending_verifications),
            staff_barangays=staff_barangays
        )

    @app.route('/admin', methods=['GET', 'POST'])
    def admin():
        user = get_current_user()
        if not user or user['role'] != 'admin':
            if user and user['role'] == 'staff':
                return redirect(url_for('staff'))
            return redirect(url_for('login'))

        tab = request.form.get('tab') or request.args.get('tab', 'dashboard')

        if request.method == 'POST':
            feedback = None
            feedback_type = 'success'
            conn = get_db()
            cur = conn.cursor()
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
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'edit_material':
                mat_id = int(request.form.get('mat_id', 0))
                name = request.form.get('mat_name', '').strip()
                cat = request.form.get('mat_cat', 'General').strip()
                pts = max(1, int(request.form.get('mat_points', 1)))
                unit = request.form.get('mat_unit', 'piece').strip()
                if not name:
                    feedback = 'Material name is required.'
                    feedback_type = 'danger'
                else:
                    cur.execute(
                        "UPDATE materials SET name = ?, category = ?, points_per_unit = ?, unit = ? WHERE id = ?",
                        (name, cat, pts, unit, mat_id)
                    )
                    conn.commit()
                    feedback = 'Material updated successfully!'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'toggle_material_status':
                mat_id = int(request.form.get('mat_id', 0))
                row = cur.execute("SELECT status FROM materials WHERE id = ?", (mat_id,)).fetchone()
                if row:
                    new_st = 'inactive' if row[0] == 'active' else 'active'
                    cur.execute("UPDATE materials SET status = ? WHERE id = ?", (new_st, mat_id))
                    conn.commit()
                    feedback = f'Material status changed to {new_st}.'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'delete_material':
                mat_id = int(request.form.get('mat_id', 0))
                cur.execute("DELETE FROM materials WHERE id = ?", (mat_id,))
                conn.commit()
                feedback = 'Material deleted successfully.'
                feedback_type = 'info'
                sync_to_json()
            elif action == 'save_reward':
                title = request.form.get('rew_title', '').strip()
                cat = request.form.get('rew_category', 'Food Staples')
                pts = max(1, int(request.form.get('rew_points', 100)))
                stock = max(0, int(request.form.get('rew_stock', 50)))
                partner = request.form.get('rew_partner', '').strip()
                if title:
                    cur.execute(
                        "INSERT INTO rewards (title, category, points_required, stock, partner_name, status) VALUES (?, ?, ?, ?, ?, 'available')",
                        (title, cat, pts, stock, partner)
                    )
                    conn.commit()
                    feedback = 'Community reward added successfully!'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'edit_reward':
                rew_id = int(request.form.get('reward_id', 0))
                title = request.form.get('rew_title', '').strip()
                cat = request.form.get('rew_category', 'Food Staples')
                pts = max(1, int(request.form.get('rew_points', 100)))
                stock = max(0, int(request.form.get('rew_stock', 50)))
                partner = request.form.get('rew_partner', '').strip()
                if not title:
                    feedback = 'Reward title is required.'
                    feedback_type = 'danger'
                else:
                    cur.execute(
                        "UPDATE rewards SET title = ?, category = ?, points_required = ?, stock = ?, partner_name = ? WHERE id = ?",
                        (title, cat, pts, stock, partner, rew_id)
                    )
                    conn.commit()
                    feedback = 'Reward updated successfully!'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'delete_reward':
                rew_id = int(request.form.get('reward_id', 0))
                cur.execute("DELETE FROM rewards WHERE id = ?", (rew_id,))
                conn.commit()
                feedback = 'Reward deleted from catalog.'
                feedback_type = 'info'
                sync_to_json()
            elif action == 'restock_reward':
                rew_id = int(request.form.get('reward_id', 0))
                add_qty = max(1, int(request.form.get('add_qty', 10)))
                cur.execute("UPDATE rewards SET stock = stock + ? WHERE id = ?", (add_qty, rew_id))
                conn.commit()
                feedback = f'Added +{add_qty} units to reward stock.'
                feedback_type = 'success'
                sync_to_json()
            elif action == 'add_resident':
                first_name = request.form.get('res_first_name', '').strip()
                last_name = request.form.get('res_last_name', '').strip()
                name = f"{first_name} {last_name}".strip() if first_name else request.form.get('res_name', '').strip()
                email = request.form.get('res_email', '').strip()
                password = request.form.get('res_password', '').strip()
                confirm_password = request.form.get('res_confirm_password', '').strip()
                pts = max(0, int(request.form.get('res_points', 0)))
                if not name or not email or not password:
                    feedback = 'Resident name, email, and password are required.'
                    feedback_type = 'danger'
                elif len(name) < 2:
                    feedback = 'Resident name must be at least 2 characters.'
                    feedback_type = 'danger'
                elif any(char.isdigit() for char in name):
                    feedback = 'Resident name cannot contain numbers.'
                    feedback_type = 'danger'
                elif len(password) < 8:
                    feedback = 'Password must be at least 8 characters.'
                    feedback_type = 'danger'
                elif confirm_password and password != confirm_password:
                    feedback = 'Passwords do not match. Please confirm your password.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
                    if existing:
                        feedback = 'An account with this email already exists.'
                        feedback_type = 'danger'
                    else:
                        qr = f'ECO-RES-{random.randint(10000, 99999)}'
                        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        pw_hash = generate_password_hash(password)
                        cur.execute(
                            "INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, 'resident', ?, ?, 'active', ?)",
                            (name, email, pw_hash, qr, pts, now_str)
                        )
                        conn.commit()
                        feedback = f'Resident {name} added successfully!'
                        feedback_type = 'success'
                        sync_to_json()
            elif action == 'edit_resident':
                res_id = int(request.form.get('res_id', 0))
                first_name = request.form.get('res_first_name', '').strip()
                last_name = request.form.get('res_last_name', '').strip()
                name = f"{first_name} {last_name}".strip() if first_name else request.form.get('res_name', '').strip()
                email = request.form.get('res_email', '').strip()
                pts = max(0, int(request.form.get('res_points', 0)))
                if not name or not email:
                    feedback = 'Resident name and email are required.'
                    feedback_type = 'danger'
                elif len(name) < 2:
                    feedback = 'Resident name must be at least 2 characters.'
                    feedback_type = 'danger'
                elif any(char.isdigit() for char in name):
                    feedback = 'Resident name cannot contain numbers.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email, res_id)).fetchone()
                    if existing:
                        feedback = 'Email is already used by another account.'
                        feedback_type = 'danger'
                    else:
                        cur.execute("UPDATE users SET full_name = ?, email = ?, points = ? WHERE id = ? AND role = 'resident'", (name, email, pts, res_id))
                        conn.commit()
                        feedback = 'Resident details updated successfully.'
                        feedback_type = 'success'
                        sync_to_json()
            elif action == 'delete_resident':
                res_id = int(request.form.get('res_id', 0))
                cur.execute("DELETE FROM users WHERE id = ? AND role = 'resident'", (res_id,))
                conn.commit()
                feedback = 'Resident account deleted successfully.'
                feedback_type = 'info'
                sync_to_json()
            elif action == 'reset_resident_password':
                res_id = int(request.form.get('res_id', 0))
                new_password = request.form.get('new_password', '').strip()
                if len(new_password) < 8:
                    feedback = 'Password must be at least 8 characters.'
                    feedback_type = 'danger'
                else:
                    hashed_pw = generate_password_hash(new_password)
                    cur.execute("UPDATE users SET password = ? WHERE id = ? AND role = 'resident'", (hashed_pw, res_id))
                    conn.commit()
                    feedback = 'Resident password has been reset successfully.'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'toggle_resident_status':
                res_id = int(request.form.get('res_id', 0))
                row = cur.execute("SELECT status FROM users WHERE id = ? AND role = 'resident'", (res_id,)).fetchone()
                if row:
                    new_st = 'inactive' if row[0] == 'active' else 'active'
                    cur.execute("UPDATE users SET status = ? WHERE id = ? AND role = 'resident'", (new_st, res_id))
                    conn.commit()
                    feedback = f'Resident status changed to {new_st}.'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'add_staff':
                first_name = request.form.get('staff_first_name', '').strip()
                last_name = request.form.get('staff_last_name', '').strip()
                name = f"{first_name} {last_name}".strip() if first_name else request.form.get('staff_name', '').strip()
                email = request.form.get('staff_email', '').strip()
                password = request.form.get('staff_password', '').strip()
                confirm_password = request.form.get('staff_confirm_password', '').strip()
                assigned_station = request.form.get('assigned_station', '').strip() or 'Barangay Pinagkawitan, Lipa City'
                if not name or not email or not password:
                    feedback = 'Please provide staff name, email, and password.'
                    feedback_type = 'danger'
                elif len(name) < 2:
                    feedback = 'Staff name must be at least 2 characters.'
                    feedback_type = 'danger'
                elif any(char.isdigit() for char in name):
                    feedback = 'Staff name cannot contain numbers.'
                    feedback_type = 'danger'
                elif len(password) < 8:
                    feedback = 'Password must be at least 8 characters.'
                    feedback_type = 'danger'
                elif confirm_password and password != confirm_password:
                    feedback = 'Passwords do not match. Please confirm your password.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
                    if existing:
                        feedback = 'An account with this email already exists.'
                        feedback_type = 'danger'
                    else:
                        qr_code = f'ECO-STF-{random.randint(10000, 99999)}'
                        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        hashed_pw = generate_password_hash(password)
                        cur.execute(
                            "INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at, station_name) VALUES (?, ?, ?, 'staff', ?, 0, 'active', ?, ?)",
                            (name, email, hashed_pw, qr_code, created_at, assigned_station)
                        )
                        cur.execute("UPDATE stations SET assigned_staff = ? WHERE station_name = ? OR ? LIKE '%' || station_name || '%'", (name, assigned_station, assigned_station))
                        conn.commit()
                        feedback = f'Staff account for {name} created successfully! They can now log in.'
                        feedback_type = 'success'
                        sync_to_json()
            elif action == 'edit_staff':
                staff_id = int(request.form.get('staff_id', 0))
                name = request.form.get('staff_name', '').strip()
                email = request.form.get('staff_email', '').strip()
                assigned_station = request.form.get('assigned_station', '').strip()
                if not name or not email:
                    feedback = 'Staff name and email are required.'
                    feedback_type = 'danger'
                elif len(name) < 2:
                    feedback = 'Staff name must be at least 2 characters.'
                    feedback_type = 'danger'
                elif any(char.isdigit() for char in name):
                    feedback = 'Staff name cannot contain numbers.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email, staff_id)).fetchone()
                    if existing:
                        feedback = 'Email is already used by another account.'
                        feedback_type = 'danger'
                    else:
                        if assigned_station:
                            cur.execute("UPDATE users SET full_name = ?, email = ?, station_name = ? WHERE id = ? AND role = 'staff'", (name, email, assigned_station, staff_id))
                            cur.execute("UPDATE stations SET assigned_staff = ? WHERE station_name = ? OR ? LIKE '%' || station_name || '%'", (name, assigned_station, assigned_station))
                        else:
                            cur.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ? AND role = 'staff'", (name, email, staff_id))
                        conn.commit()
                        feedback = 'Staff account updated successfully.'
                        feedback_type = 'success'
                        sync_to_json()
            elif action == 'reset_staff_password':
                staff_id = int(request.form.get('staff_id', 0))
                new_password = request.form.get('new_password', '').strip()
                if len(new_password) < 8:
                    feedback = 'Password must be at least 8 characters.'
                    feedback_type = 'danger'
                else:
                    hashed_pw = generate_password_hash(new_password)
                    cur.execute("UPDATE users SET password = ? WHERE id = ? AND role = 'staff'", (hashed_pw, staff_id))
                    conn.commit()
                    feedback = 'Staff password has been reset successfully.'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'toggle_staff_status':
                staff_id = int(request.form.get('staff_id', 0))
                current_st = cur.execute("SELECT status FROM users WHERE id = ? AND role = 'staff'", (staff_id,))
                row = current_st.fetchone()
                if row:
                    current_val = row[0]
                    new_st = 'inactive' if current_val == 'active' else 'active'
                    cur.execute("UPDATE users SET status = ? WHERE id = ? AND role = 'staff'", (new_st, staff_id))
                    conn.commit()
                    feedback = f'Staff status changed to {new_st}.'
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'delete_staff':
                staff_id = int(request.form.get('staff_id', 0))
                cur.execute("DELETE FROM users WHERE id = ? AND role = 'staff'", (staff_id,))
                conn.commit()
                feedback = 'Staff account deleted successfully.'
                feedback_type = 'info'
                sync_to_json()
            elif action == 'add_station':
                stn_name = request.form.get('station_name', '').strip()
                stn_brgy = request.form.get('barangay', 'Pinagkawitan').strip()
                stn_city = request.form.get('city', 'Lipa City').strip()
                stn_code = request.form.get('station_code', '').strip()
                stn_staff = request.form.get('assigned_staff', '').strip()
                if not stn_code:
                    count_stn = cur.execute('SELECT COUNT(*) FROM stations').fetchone()[0]
                    stn_code = f"STN-LP-{count_stn + 1:02d}"
                if not stn_name:
                    stn_name = f"{stn_brgy} Collection Hub"
                loc = f"Barangay {stn_brgy}, {stn_city}"
                cur.execute(
                    "INSERT INTO stations (station_code, station_name, location, barangay, city, assigned_staff, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
                    (stn_code, stn_name, loc, stn_brgy, stn_city, stn_staff, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
                conn.commit()
                feedback = f"Collection station '{stn_name}' registered successfully."
                feedback_type = 'success'
                sync_to_json()
            elif action == 'edit_station':
                stn_id = int(request.form.get('station_id', 0))
                stn_name = request.form.get('station_name', '').strip()
                stn_code = request.form.get('station_code', '').strip()
                stn_brgy = request.form.get('barangay', '').strip()
                stn_city = request.form.get('city', '').strip()
                stn_status = request.form.get('status', 'active').strip()
                loc = f"Barangay {stn_brgy}, {stn_city}" if (stn_brgy and stn_city) else ''
                if not stn_name:
                    feedback = 'Station Hub Name is required.'
                    feedback_type = 'danger'
                else:
                    if loc:
                        cur.execute("UPDATE stations SET station_name = ?, station_code = ?, location = ?, barangay = ?, city = ?, status = ? WHERE id = ?", (stn_name, stn_code, loc, stn_brgy, stn_city, stn_status, stn_id))
                    else:
                        cur.execute("UPDATE stations SET station_name = ?, station_code = ?, status = ? WHERE id = ?", (stn_name, stn_code, stn_status, stn_id))
                    conn.commit()
                    feedback = f"Collection station '{stn_name}' updated successfully."
                    feedback_type = 'success'
                    sync_to_json()
            elif action == 'delete_station':
                stn_id = int(request.form.get('station_id', 0))
                stn_row = cur.execute("SELECT * FROM stations WHERE id = ?", (stn_id,)).fetchone()
                if stn_row:
                    stn = dict(stn_row)
                    stn_staff = (stn.get('assigned_staff') or '').strip()
                    stn_name = (stn.get('station_name') or '').strip()
                    stn_brgy = (stn.get('barangay') or '').strip()

                    staff_assigned = None
                    if stn_staff:
                        staff_assigned = cur.execute("SELECT id, full_name FROM users WHERE role = 'staff' AND full_name = ? AND status = 'active'", (stn_staff,)).fetchone()
                    if not staff_assigned:
                        staff_assigned = cur.execute("SELECT id, full_name FROM users WHERE role = 'staff' AND status = 'active' AND (station_name LIKE ? OR station_name LIKE ?)", (f"%{stn_name}%", f"%{stn_brgy}%")).fetchone()

                    if stn_staff or staff_assigned:
                        staff_name = dict(staff_assigned)['full_name'] if staff_assigned else stn_staff
                        feedback = f"Cannot delete '{stn_name}': Active staff member ({staff_name}) is currently assigned to this station."
                        feedback_type = 'danger'
                    else:
                        cur.execute("DELETE FROM stations WHERE id = ?", (stn_id,))
                        conn.commit()
                        feedback = f"Collection station '{stn_name}' removed successfully."
                        feedback_type = 'info'
                        sync_to_json()

            conn.close()
            session['feedback'] = feedback
            session['feedback_type'] = feedback_type
            return redirect(url_for('admin', tab=tab))

        feedback = session.pop('feedback', None)
        feedback_type = session.pop('feedback_type', 'success')
        conn = get_db()
        cur = conn.cursor()

        all_txs = [dict(r) for r in cur.execute("""
            SELECT t.*, u.full_name AS resident_name, u.qr_code AS resident_qr, u.barangay AS resident_barangay
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
        """).fetchall()]

        residents_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY id ASC").fetchall()]
        staff_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'staff' ORDER BY id ASC").fetchall()]
        all_materials = [dict(r) for r in cur.execute("SELECT * FROM materials ORDER BY id ASC").fetchall()]
        all_rewards = [dict(r) for r in cur.execute("SELECT * FROM rewards ORDER BY points_required ASC").fetchall()]
        all_stations = []
        try:
            all_stations = [dict(r) for r in cur.execute("SELECT * FROM stations ORDER BY id ASC").fetchall()]
            for stn in all_stations:
                stn_staff = (stn.get('assigned_staff') or '').strip()
                stn_name = (stn.get('station_name') or '').strip()
                stn_brgy = (stn.get('barangay') or '').strip()
                has_active_staff = bool(stn_staff) or any(
                    (u.get('station_name') and (stn_name in u['station_name'] or stn_brgy in u['station_name'])) or (stn_staff and u.get('full_name') == stn_staff)
                    for u in staff_list if u.get('role') == 'staff' and u.get('status') == 'active'
                )
                stn['in_use'] = has_active_staff
        except Exception:
            pass
        all_redemptions = [dict(r) for r in cur.execute("""
            SELECT r.*, u.full_name AS resident_name, u.qr_code AS resident_qr, u.barangay AS resident_barangay
            FROM redemptions r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """).fetchall()]

        report_barangays = []
        seen_brgys = set()
        for stn in all_stations:
            b_name = (stn.get('barangay') or '').strip()
            c_name = (stn.get('city') or '').strip()
            if b_name and b_name.lower() not in seen_brgys:
                seen_brgys.add(b_name.lower())
                lbl = f"Barangay {b_name}, {c_name}" if c_name else f"Barangay {b_name}"
                report_barangays.append({'barangay': b_name, 'label': lbl})

        raw_brgy_arg = request.args.get('barangay')
        if tab == 'reports':
            if raw_brgy_arg is None:
                default_brgy = next((rb['barangay'] for rb in report_barangays if rb['barangay'].lower() == 'pinagkawitan'), '')
                selected_barangay = default_brgy or (report_barangays[0]['barangay'] if report_barangays else 'all')
            else:
                selected_barangay = raw_brgy_arg.strip() or 'all'
        else:
            selected_barangay = ''

        selected_barangay_label = 'All Barangays'
        if tab == 'reports' and selected_barangay and selected_barangay.lower() != 'all':
            matched_lbl = next((rb['label'] for rb in report_barangays if rb['barangay'].lower() == selected_barangay.lower()), None)
            selected_barangay_label = matched_lbl or f"Barangay {selected_barangay}"
            residents_list = [r for r in residents_list if resident_matches_barangays(r.get('barangay'), [selected_barangay])]
            all_txs = [t for t in all_txs if resident_matches_barangays(t.get('resident_barangay'), [selected_barangay])]
            all_redemptions = [r for r in all_redemptions if resident_matches_barangays(r.get('resident_barangay'), [selected_barangay])]

        today_str = datetime.now().strftime('%Y-%m-%d')
        today_items = sum(int(t.get('quantity', 0)) for t in all_txs if str(t.get('created_at', '')).startswith(today_str))
        total_points = sum(int(t.get('points_earned', 0)) for t in all_txs)
        total_items_collected = sum(int(t.get('quantity', 0)) for t in all_txs)
        unique_participants = len(set(t['user_id'] for t in all_txs if t.get('user_id')))
        part_rate = round((unique_participants / max(1, len(residents_list))) * 100, 1)

        mat_counts = {'Plastic Bottles': 0, 'Cans': 0, 'Others': 0}
        cat_breakdown = {
            'Plastic': {'name': 'Plastic Bottles', 'qty': 0, 'points': 0, 'color': '#198754'},
            'Metal': {'name': 'Aluminum Cans', 'qty': 0, 'points': 0, 'color': '#0d6efd'},
            'Paper': {'name': 'Paper & Cardboard', 'qty': 0, 'points': 0, 'color': '#f59e0b'},
            'Glass': {'name': 'Glass & Others', 'qty': 0, 'points': 0, 'color': '#8b5cf6'}
        }
        for t in all_txs:
            m_name = str(t.get('material_name', '')).lower()
            q = int(t.get('quantity', 0))
            pts = int(t.get('points_earned', 0))
            if 'bottle' in m_name or 'plastic' in m_name:
                mat_counts['Plastic Bottles'] += q
                cat_breakdown['Plastic']['qty'] += q
                cat_breakdown['Plastic']['points'] += pts
            elif 'can' in m_name:
                mat_counts['Cans'] += q
                cat_breakdown['Metal']['qty'] += q
                cat_breakdown['Metal']['points'] += pts
            elif 'paper' in m_name or 'cardboard' in m_name:
                mat_counts['Others'] += q
                cat_breakdown['Paper']['qty'] += q
                cat_breakdown['Paper']['points'] += pts
            else:
                mat_counts['Others'] += q
                cat_breakdown['Glass']['qty'] += q
                cat_breakdown['Glass']['points'] += pts

        diverted_kg = round(
            (cat_breakdown['Plastic']['qty'] * 0.035) +
            (cat_breakdown['Metal']['qty'] * 0.015) +
            (cat_breakdown['Paper']['qty'] * 1.0) +
            (cat_breakdown['Glass']['qty'] * 0.25),
            1
        )

        for k in cat_breakdown:
            cat_breakdown[k]['share'] = round((cat_breakdown[k]['qty'] / max(1, total_items_collected)) * 100, 1)

        daily_timeline = {}
        for t in reversed(all_txs):
            dt = str(t.get('created_at', ''))[:10]
            if not dt:
                continue
            if dt not in daily_timeline:
                daily_timeline[dt] = {'items': 0, 'points': 0, 'deposits': 0}
            daily_timeline[dt]['items'] += int(t.get('quantity', 0))
            daily_timeline[dt]['points'] += int(t.get('points_earned', 0))
            daily_timeline[dt]['deposits'] += 1

        if len(daily_timeline) < 5:
            base_dates = ['2026-10-22', '2026-10-26', '2026-10-29', '2026-10-31', '2026-11-01']
            for d in base_dates:
                if d not in daily_timeline:
                    daily_timeline[d] = {'items': 0, 'points': 0, 'deposits': 0}

        sorted_dates = sorted(daily_timeline.keys())[-7:]
        timeline_labels = sorted_dates
        timeline_items = [daily_timeline[k]['items'] for k in sorted_dates]
        timeline_points = [daily_timeline[k]['points'] for k in sorted_dates]
        timeline_deposits = [daily_timeline[k]['deposits'] for k in sorted_dates]

        res_activity = {}
        for t in all_txs:
            uid = t.get('user_id')
            if not uid:
                continue
            if uid not in res_activity:
                res_activity[uid] = {
                    'name': t.get('resident_name', 'Unknown'),
                    'qr_code': t.get('resident_qr', '-'),
                    'deposits': 0,
                    'items': 0,
                    'points': 0
                }
            res_activity[uid]['deposits'] += 1
            res_activity[uid]['items'] += int(t.get('quantity', 0))
            res_activity[uid]['points'] += int(t.get('points_earned', 0))

        top_recyclers = sorted(res_activity.values(), key=lambda x: x['points'], reverse=True)[:5]

        stream_palette = ['#198754', '#0d6efd', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#6366f1']
        material_stream_performance = []
        for idx, mat in enumerate(all_materials):
            m_id = mat.get('id')
            m_name = (mat.get('name') or '').strip()
            m_cat = (mat.get('category') or 'General').strip()
            m_qty = 0
            m_pts = 0
            for t in all_txs:
                t_mid = t.get('material_id')
                t_name = (t.get('material_name') or '').strip().lower()
                if (m_id is not None and t_mid == m_id) or (m_name and t_name == m_name.lower()):
                    m_qty += int(t.get('quantity') or 0)
                    m_pts += int(t.get('points_earned') or 0)
            material_stream_performance.append({
                'name': m_name,
                'category': m_cat,
                'qty': m_qty,
                'points': m_pts,
                'color': stream_palette[idx % len(stream_palette)]
            })
        stream_total_qty = sum(x['qty'] for x in material_stream_performance)
        for x in material_stream_performance:
            x['share'] = round((x['qty'] / stream_total_qty) * 100, 1) if stream_total_qty > 0 else 0.0
        material_stream_performance.sort(key=lambda x: (-x['qty'], -x['points'], x['name']))

        stats = {
            'today_items': today_items,
            'total_points_issued': total_points,
            'total_redemptions': len(all_redemptions),
            'recent_transactions': all_txs[:6],
            'material_counts': mat_counts,
            'total_items_collected': total_items_collected,
            'unique_participants': unique_participants,
            'participation_rate': part_rate,
            'diverted_kg': diverted_kg,
            'cat_breakdown': cat_breakdown,
            'material_stream_performance': material_stream_performance,
            'dynamic_materials': build_dynamic_material_chart(all_txs),
            'timeline_labels': timeline_labels,
            'timeline_items': timeline_items,
            'timeline_points': timeline_points,
            'timeline_deposits': timeline_deposits,
            'top_recyclers': top_recyclers
        }

        conn.close()

        return render_template(
            'admin.html',
            tab=tab,
            feedback=feedback,
            feedback_type=feedback_type,
            residents_list=residents_list,
            staff_list=staff_list,
            all_transactions=all_txs,
            all_materials=all_materials,
            all_rewards=all_rewards,
            all_redemptions=all_redemptions,
            all_stations=all_stations,
            report_barangays=report_barangays,
            selected_barangay=selected_barangay,
            selected_barangay_label=selected_barangay_label,
            stats=stats
        )



    @app.route('/api/resident-lookup')
    def api_resident_lookup():
        qr = request.args.get('qr', '').strip()
        if not qr:
            return jsonify({'success': False, 'message': 'QR code required'}), 400

        conn = get_db()
        cur = conn.cursor()
        resident = cur.execute("SELECT id, full_name, email, qr_code, points, role, barangay, is_verified, verification_status FROM users WHERE qr_code = ?", (qr,)).fetchone()
        current_staff = get_current_user()
        staff_barangays = get_staff_barangays(cur, current_staff) if (current_staff and current_staff.get('role') == 'staff') else []
        conn.close()

        if resident:
            res_dict = dict(resident)
            if res_dict.get('role') == 'resident' and not (int(res_dict.get('is_verified') or 0) == 1 and (res_dict.get('verification_status') or '') == 'verified'):
                return jsonify({
                    'success': False,
                    'non_verified': True,
                    'verification_status': res_dict.get('verification_status') or 'unverified',
                    'message': f"Non-Verified Resident Detected ({res_dict['full_name']}). Account must be verified and confirmed by Barangay Staff before scanning QR."
                }), 403
            if staff_barangays and res_dict.get('role') == 'resident' and not resident_matches_barangays(res_dict.get('barangay'), staff_barangays):
                return jsonify({
                    'success': False,
                    'wrong_barangay': True,
                    'message': f"Wrong Barangay Station: {res_dict['full_name']} belongs to Barangay {res_dict.get('barangay') or 'Unassigned'}, not Barangay {', '.join(staff_barangays)}."
                }), 403
            return jsonify({'success': True, 'resident': res_dict})
        return jsonify({'success': False, 'message': 'Resident not found'}), 404

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
        if resident.get('role') == 'resident' and not (int(resident.get('is_verified') or 0) == 1 and (resident.get('verification_status') or '') == 'verified'):
            conn.close()
            return jsonify({
                'success': False,
                'non_verified': True,
                'message': f"Non-Verified Resident Detected ({resident['full_name']}). Account must be verified before earning EcoPoints."
            }), 403
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

    @app.route('/admin/report/participation.pdf')
    def report_participation_pdf():
        user = get_current_user()
        if not user or user['role'] != 'admin':
            return redirect(url_for('login'))
        brgy = request.args.get('barangay', '').strip()
        pdf_data = generate_participation_report_pdf(barangay=brgy)
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        disposition = 'attachment' if request.args.get('download') else 'inline'
        suffix = f"_{brgy.replace(' ', '_')}" if (brgy and brgy.lower() != 'all') else ''
        response.headers['Content-Disposition'] = f'{disposition}; filename=Community_Participation_Report{suffix}.pdf'
        return response

    @app.route('/admin/report/materials.pdf')
    def report_materials_pdf():
        user = get_current_user()
        if not user or user['role'] != 'admin':
            return redirect(url_for('login'))
        brgy = request.args.get('barangay', '').strip()
        pdf_data = generate_materials_report_pdf(barangay=brgy)
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        disposition = 'attachment' if request.args.get('download') else 'inline'
        suffix = f"_{brgy.replace(' ', '_')}" if (brgy and brgy.lower() != 'all') else ''
        response.headers['Content-Disposition'] = f'{disposition}; filename=Collected_Materials_Summary{suffix}.pdf'
        return response

    @app.route('/staff/receipt/<receipt_no>.pdf')
    def receipt_pdf(receipt_no):
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))
        conn = get_db()
        cur = conn.cursor()
        tx = cur.execute("""
            SELECT t.*, u.full_name AS resident_name, u.qr_code, u.points AS current_points
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            WHERE t.receipt_no = ?
        """, (receipt_no,)).fetchone()
        conn.close()
        if not tx:
            if user['role'] == 'staff':
                return redirect(url_for('staff', tab='unit'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        tx = dict(tx)
        if user['role'] not in ['staff', 'admin'] and user['id'] != tx['user_id']:
            return redirect(url_for('dashboard'))
        mat_name = str(tx.get('material_name', ''))
        unit_label = 'piece' if ('bottle' in mat_name.lower() or 'can' in mat_name.lower()) else 'kg'
        staff_display = user['full_name'] if user['role'] in ['staff', 'admin'] else 'Barangay Staff'
        receipt_data = {
            'receipt_no': tx['receipt_no'],
            'created_at': tx['created_at'],
            'staff_name': staff_display,
            'resident_name': tx['resident_name'],
            'qr_code': tx['qr_code'],
            'material_name': tx['material_name'],
            'quantity': tx['quantity'],
            'unit': unit_label,
            'points_earned': tx['points_earned'],
            'new_total_points': tx['current_points']
        }
        pdf_bytes = generate_deposit_receipt_pdf(receipt_data)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        disposition = 'attachment' if request.args.get('download') else 'inline'
        response.headers['Content-Disposition'] = f'{disposition}; filename={receipt_no}.pdf'
        return response

    @app.route('/api/validate-id-image', methods=['POST'])
    def api_validate_id_image():
        user = get_current_user()
        if not user:
            return jsonify({'status': 'error', 'valid': False, 'message': 'Please log in first.'}), 401
        id_file = request.files.get('image')
        side = request.form.get('side', 'front')
        id_type = request.form.get('id_type', '')
        if not id_file or not id_file.filename:
            return jsonify({'status': 'error', 'valid': False, 'message': 'No image uploaded.'}), 400
        raw_bytes = id_file.read()
        is_valid, msg = validate_id_image_with_ai(raw_bytes, side, id_type)
        return jsonify({'status': 'ok', 'valid': is_valid, 'message': msg})

    @app.route('/api/contact-us', methods=['POST'])
    def api_contact_us():
        user = get_current_user()
        if not user:
            return jsonify({'status': 'error', 'message': 'Please log in to send a message.'}), 401

        data = request.get_json(silent=True) or {}
        subject = str(data.get('subject') or '').strip()
        body_text = str(data.get('message') or '').strip()

        if not subject:
            return jsonify({'status': 'error', 'message': 'Please enter a subject for your inquiry.'}), 400
        if not body_text or len(body_text) < 5:
            return jsonify({'status': 'error', 'message': 'Please enter a message (at least 5 characters).'}), 400

        subject = subject[:120]
        body_text = body_text[:2000]
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        def read_env(env_key, default_val=''):
            val = os.environ.get(env_key, '').strip()
            if val:
                return val
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if os.path.isfile(env_path):
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or '=' not in line:
                                continue
                            k, v = line.split('=', 1)
                            if k.strip() == env_key:
                                return v.strip().strip('"').strip("'")
                except Exception:
                    pass
            return default_val

        smtp_host = read_env('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(read_env('SMTP_PORT', '587') or '587')
        smtp_user = read_env('SMTP_USER')
        smtp_pass = read_env('SMTP_PASS').replace(' ', '')
        receiver_email = read_env('CONTACT_RECEIVER_EMAIL') or smtp_user

        email_sent = 0
        smtp_error = None
        if smtp_user and smtp_pass and receiver_email:
            try:
                msg = EmailMessage()
                msg['Subject'] = f"[EcoCoins Contact Us] {subject}"
                msg['From'] = smtp_user
                msg['To'] = receiver_email
                if user.get('email'):
                    msg['Reply-To'] = user['email']
                msg.set_content(
                    f"Resident Name: {user.get('full_name') or 'Resident'}\n"
                    f"Resident Email: {user.get('email') or 'N/A'}\n"
                    f"Barangay: {user.get('barangay') or 'Pinagkawitan'}\n"
                    f"QR Code: {user.get('qr_code') or 'N/A'}\n"
                    f"Sent At: {now_str}\n\n"
                    f"Subject: {subject}\n\n"
                    f"Message:\n{body_text}\n"
                )
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                email_sent = 1
            except Exception as ex:
                smtp_error = str(ex)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                resident_name TEXT,
                resident_email TEXT,
                barangay TEXT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                email_sent INTEGER DEFAULT 0,
                created_at TEXT
            )"""
        )
        cur.execute(
            """INSERT INTO contact_messages (user_id, resident_name, resident_email, barangay, subject, message, email_sent, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user['id'],
                user.get('full_name') or '',
                user.get('email') or '',
                user.get('barangay') or 'Pinagkawitan',
                subject,
                body_text,
                email_sent,
                now_str
            )
        )
        conn.commit()
        cur.close()
        conn.close()

        if email_sent:
            return jsonify({'status': 'success', 'email_sent': True, 'message': 'Your message has been sent! Our barangay EcoCoins team will get back to you soon.'})
        if smtp_error:
            return jsonify({'status': 'success', 'email_sent': False, 'message': 'Your message was saved in our system, though email delivery is currently unavailable.'})
        return jsonify({'status': 'success', 'email_sent': False, 'message': 'Your message has been submitted to the EcoCoins team!'})

    @app.route('/api/forgot-password/send-code', methods=['POST'])
    def api_forgot_password_send_code():
        data = request.get_json(silent=True) or {}
        email = str(data.get('email') or '').strip().lower()
        if not email or not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email):
            return jsonify({'status': 'error', 'message': 'Please enter a valid email address.'}), 400

        conn = get_db()
        cur = conn.cursor()
        user_row = cur.execute("SELECT id, full_name, email, status FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()
        if not user_row:
            conn.close()
            return jsonify({'status': 'error', 'message': 'No account found with that email address.'}), 404

        user_row = dict(user_row)
        if (user_row.get('status') or 'active').lower() != 'active':
            conn.close()
            return jsonify({'status': 'error', 'message': 'This account is currently inactive. Please contact your barangay administrator.'}), 403

        cur.execute(
            """CREATE TABLE IF NOT EXISTS password_reset_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )

        code = f"{secrets.randbelow(900000) + 100000}"
        now_dt = datetime.now()
        now_str = now_dt.strftime('%Y-%m-%d %H:%M:%S')
        expires_str = (now_dt + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

        smtp_user = _load_env_key('SMTP_USER')
        smtp_pass = _load_env_key('SMTP_PASS').replace(' ', '')

        if not smtp_user or not smtp_pass:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Email service is not configured on this server.'}), 500

        try:
            msg = EmailMessage()
            msg['Subject'] = 'EcoCoins Password Reset Verification Code'
            msg['From'] = smtp_user
            msg['To'] = user_row['email']
            msg.set_content(
                f"Hello {user_row.get('full_name') or 'Resident'},\n\n"
                f"Your EcoCoins password reset verification code is:\n\n"
                f"    {code}\n\n"
                f"This code will expire in 15 minutes. If you did not request a password reset, you can safely ignore this email.\n\n"
                f"- EcoCoins Barangay Recycling System\n"
            )
            _send_smtp_email(msg)
        except Exception as ex:
            conn.close()
            err_hint = 'Current Wi-Fi network is blocking Gmail SMTP ports (587/465). Try switching to mobile hotspot or using the Vercel live link.' if '10061' in str(ex) or 'refused' in str(ex).lower() else 'Failed to send verification code email. Please try again in a moment.'
            return jsonify({'status': 'error', 'message': err_hint}), 500

        cur.execute("UPDATE password_reset_codes SET used = 1 WHERE LOWER(email) = LOWER(?) AND used = 0", (email,))
        cur.execute(
            """INSERT INTO password_reset_codes (user_id, email, code_hash, expires_at, attempts, used, created_at)
               VALUES (?, ?, ?, ?, 0, 0, ?)""",
            (user_row['id'], user_row['email'].lower(), generate_password_hash(code), expires_str, now_str)
        )
        conn.commit()
        conn.close()
        session.pop('pw_reset_verified', None)

        return jsonify({'status': 'success', 'message': f"A 6-digit verification code has been sent to {user_row['email']}."})

    @app.route('/api/forgot-password/verify-code', methods=['POST'])
    def api_forgot_password_verify_code():
        data = request.get_json(silent=True) or {}
        email = str(data.get('email') or '').strip().lower()
        code = str(data.get('code') or '').strip()

        if not email or not re.match(r"^\d{6}$", code):
            return jsonify({'status': 'error', 'message': 'Please enter the 6-digit code sent to your email.'}), 400

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS password_reset_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )"""
        )
        row = cur.execute(
            "SELECT * FROM password_reset_codes WHERE LOWER(email) = LOWER(?) AND used = 0 ORDER BY id DESC LIMIT 1",
            (email,)
        ).fetchone()

        if not row:
            conn.close()
            return jsonify({'status': 'error', 'message': 'No active reset code found. Please request a new code.'}), 400

        row = dict(row)
        try:
            exp_dt = datetime.strptime(row['expires_at'], '%Y-%m-%d %H:%M:%S')
        except Exception:
            exp_dt = datetime.min

        if datetime.now() > exp_dt:
            cur.execute("UPDATE password_reset_codes SET used = 1 WHERE id = ?", (row['id'],))
            conn.commit()
            conn.close()
            return jsonify({'status': 'error', 'message': 'This verification code has expired. Please request a new one.'}), 400

        if int(row.get('attempts') or 0) >= 5:
            cur.execute("UPDATE password_reset_codes SET used = 1 WHERE id = ?", (row['id'],))
            conn.commit()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Too many incorrect attempts. Please request a new code.'}), 400

        if not check_password_hash(row['code_hash'], code):
            cur.execute("UPDATE password_reset_codes SET attempts = attempts + 1 WHERE id = ?", (row['id'],))
            conn.commit()
            conn.close()
            return jsonify({'status': 'error', 'message': 'Incorrect verification code. Please check your email and try again.'}), 400

        conn.close()
        session['pw_reset_verified'] = {'email': row['email'], 'user_id': row['user_id'], 'code_id': row['id']}
        return jsonify({'status': 'success', 'message': 'Code verified! Enter your new password below.'})

    @app.route('/api/forgot-password/reset', methods=['POST'])
    def api_forgot_password_reset():
        verified = session.get('pw_reset_verified')
        if not verified or not verified.get('user_id') or not verified.get('code_id'):
            return jsonify({'status': 'error', 'message': 'Reset session expired. Please request a new verification code.'}), 400

        data = request.get_json(silent=True) or {}
        password = str(data.get('password') or '')
        confirm_password = str(data.get('confirm_password') or '')

        if len(password) < 8 or len(password) > 64:
            return jsonify({'status': 'error', 'message': 'Password must be 8 to 64 characters long.'}), 400
        if not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password) or not re.search(r"[^A-Za-z0-9]", password):
            return jsonify({'status': 'error', 'message': 'Password must include uppercase, lowercase, a number, and a special character.'}), 400
        if password != confirm_password:
            return jsonify({'status': 'error', 'message': 'The passwords you entered do not match.'}), 400

        conn = get_db()
        cur = conn.cursor()
        code_row = cur.execute(
            "SELECT * FROM password_reset_codes WHERE id = ? AND used = 0",
            (verified['code_id'],)
        ).fetchone()
        if not code_row:
            conn.close()
            session.pop('pw_reset_verified', None)
            return jsonify({'status': 'error', 'message': 'Reset code already used or expired. Please request a new one.'}), 400

        hashed_pw = generate_password_hash(password)
        cur.execute(
            "UPDATE users SET password = ?, failed_login_attempts = 0, lockout_until = NULL WHERE id = ?",
            (hashed_pw, verified['user_id'])
        )
        cur.execute("UPDATE password_reset_codes SET used = 1 WHERE id = ?", (verified['code_id'],))
        conn.commit()
        conn.close()
        sync_to_json()

        reset_email = verified.get('email', '')
        session.pop('pw_reset_verified', None)
        return jsonify({'status': 'success', 'email': reset_email, 'message': 'Password updated successfully! You can now log in with your new password.'})

    @app.route('/api/google-login', methods=['POST'])
    def api_google_login():
        data = request.get_json(silent=True) or {}
        credential = str(data.get('credential') or '').strip()
        if not credential:
            return jsonify({'status': 'error', 'message': 'Missing Google credential.'}), 400

        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip()
        if not google_client_id:
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if os.path.isfile(env_path):
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or '=' not in line:
                                continue
                            k, v = line.split('=', 1)
                            if k.strip() == 'GOOGLE_CLIENT_ID':
                                google_client_id = v.strip().strip('"').strip("'")
                                break
                except Exception:
                    pass

        if not google_client_id:
            return jsonify({'status': 'error', 'message': 'Google Sign-In is not configured on this server.'}), 500

        verify_url = 'https://oauth2.googleapis.com/tokeninfo?id_token=' + urllib.parse.quote(credential, safe='')
        try:
            with urllib.request.urlopen(verify_url, timeout=10) as resp:
                token_info = json.loads(resp.read().decode('utf-8'))
        except Exception:
            return jsonify({'status': 'error', 'message': 'Could not verify Google sign-in token. Please try again.'}), 401

        aud = str(token_info.get('aud') or '').strip()
        iss = str(token_info.get('iss') or '').strip()
        email_verified = str(token_info.get('email_verified') or '').lower() == 'true'
        email = str(token_info.get('email') or '').strip().lower()

        if aud != google_client_id or iss not in ('accounts.google.com', 'https://accounts.google.com') or not email_verified or not email:
            return jsonify({'status': 'error', 'message': 'Invalid or unverified Google account token.'}), 401

        client_ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '127.0.0.1').split(',')[0].strip()
        now_dt = datetime.now()
        now_str = now_dt.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        cur = conn.cursor()
        matched = cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)).fetchone()

        if matched:
            matched = dict(matched)
            raw_lockout = (matched.get('lockout_until') or '').strip()
            if raw_lockout:
                try:
                    lock_dt = datetime.strptime(raw_lockout, '%Y-%m-%d %H:%M:%S')
                    if lock_dt > now_dt:
                        conn.close()
                        return jsonify({'status': 'error', 'message': 'This account is temporarily locked. Please wait before trying again.'}), 429
                except Exception:
                    pass

            if (matched.get('status') or 'active').lower() != 'active':
                conn.close()
                return jsonify({'status': 'error', 'message': 'This account is currently inactive. Please contact your barangay administrator.'}), 403

            cur.execute(
                "UPDATE users SET failed_login_attempts = 0, lockout_until = NULL, last_login_at = ? WHERE id = ?",
                (now_str, matched['id'])
            )
            cur.execute(
                "INSERT INTO login_attempts (email, ip_address, success, reason, created_at) VALUES (?, ?, 1, 'google_login', ?)",
                (email, client_ip, now_str)
            )
            conn.commit()
            conn.close()
            sync_to_json()

            session.clear()
            session.permanent = True
            session['user_id'] = matched['id']
            session['user_role'] = matched['role']
            session['last_activity'] = time.time()

            if matched['role'] == 'admin':
                target_url = url_for('admin')
            elif matched['role'] == 'staff':
                target_url = url_for('staff')
            else:
                target_url = url_for('dashboard')

            return jsonify({'status': 'success', 'redirect': target_url, 'full_name': matched['full_name']})

        conn.close()

        given_name = str(token_info.get('given_name') or '').strip()
        family_name = str(token_info.get('family_name') or '').strip()
        full_name = str(token_info.get('name') or '').strip()
        if not given_name and full_name:
            parts = full_name.split()
            given_name = parts[0] if parts else ''
            family_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

        given_name = re.sub(r"[^A-Za-zÀ-ÿ\s.\-']", '', given_name).strip()[:30]
        family_name = re.sub(r"[^A-Za-zÀ-ÿ\s.\-']", '', family_name).strip()[:30]

        session['google_prefill'] = {
            'email': email,
            'first_name': given_name,
            'last_name': family_name
        }

        return jsonify({
            'status': 'needs_register',
            'redirect': url_for('register'),
            'email': email,
            'first_name': given_name,
            'last_name': family_name
        })

    @app.route('/api/faq-chat', methods=['POST'])
    def api_faq_chat():
        data = request.get_json(silent=True) or {}
        question = str(data.get('message') or '').strip()
        if not question:
            return jsonify({'status': 'error', 'reply': 'Please type a question about EcoCoins.'}), 400
        if len(question) > 500:
            question = question[:500]

        raw_history = data.get('history') if isinstance(data.get('history'), list) else []

        conn = get_db()
        cur = conn.cursor()
        materials = [dict(r) for r in cur.execute("SELECT name, category, points_per_unit, unit FROM materials WHERE status = 'active' ORDER BY name ASC").fetchall()]
        rewards = [dict(r) for r in cur.execute("SELECT title, category, points_required, stock, partner_name FROM rewards WHERE status = 'active' ORDER BY points_required ASC").fetchall()]
        staff_rows = cur.execute("SELECT DISTINCT barangay FROM users WHERE role = 'staff' AND barangay IS NOT NULL AND barangay != ''").fetchall()
        cur.close()
        conn.close()

        hubs = []
        for r in staff_rows:
            for b in str(r['barangay']).split(','):
                b_clean = b.strip()
                if b_clean and b_clean not in hubs:
                    hubs.append(b_clean)
        if not hubs:
            hubs = ['Pinagkawitan']

        def get_env_val(env_key, default_val=''):
            val = os.environ.get(env_key, '').strip()
            if val:
                return val
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            if os.path.isfile(env_path):
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line or '=' not in line:
                                continue
                            k, v = line.split('=', 1)
                            if k.strip() == env_key:
                                return v.strip().strip('"').strip("'")
                except Exception:
                    pass
            return default_val

        def build_fallback(q_text):
            ql = q_text.lower()
            if any(k in ql for k in ['material', 'plastic', 'bottle', 'can', 'paper', 'cardboard', 'metal', 'glass', 'tin', 'recycl', 'bote', 'lata', 'papel', 'tinatanggap', 'rate', 'points per']):
                if materials:
                    lines = [f"- {m['name']}: {m['points_per_unit']} pts per {m['unit']}" for m in materials[:8]]
                    return "Here are the currently accepted recyclables and their EcoPoints:\n" + "\n".join(lines)
                return "Bring clean recyclables like plastic bottles, cans, paper, and cardboard to your Barangay Collection Hub to earn EcoPoints."
            if any(k in ql for k in ['reward', 'redeem', 'claim', 'prize', 'rice', 'grocery', 'gift', 'palit', 'premyo']):
                if rewards:
                    lines = [f"- {r['title']}: {r['points_required']} pts ({r['stock']} left)" for r in rewards[:6]]
                    return "You can redeem your EcoPoints on the Rewards page, then claim them at the barangay station:\n" + "\n".join(lines)
                return "Go to the Rewards page to redeem EcoPoints for available items, then claim your approved reward at the barangay station."
            if any(k in ql for k in ['verify', 'verification', 'valid id', 'id ', 'beripika', 'pending', 'rejected', 'cooldown']):
                return "To verify your resident account, go to Verify Account and complete 3 steps: (1) live face scan (Left, Right, Blink, Hold still 3s) + Front & Back Valid ID upload, (2) review your personal info & address, and (3) submit for Barangay Staff confirmation."
            if any(k in ql for k in ['face', 'mukha', 'biometric', 'camera', 'liveness', 'face login']):
                return "Verified residents can use Face Login on the Login page. Follow the liveness check (turn Left, turn Right, Blink, then Hold still for 3 seconds) in good lighting. For security, only a strict match to your verified face can sign in."
            if any(k in ql for k in ['qr', 'code', 'scan', 'hub', 'barangay', 'where', 'saan', 'station', 'drop']):
                hub_list = ", ".join(hubs)
                return f"Once verified, open your Resident QR Code from the Dashboard or the top-right user dropdown (My QR Code). Show it to staff at your Barangay Collection Hub ({hub_list}, Lipa City) when dropping off recyclables."
            if any(k in ql for k in ['logout', 'log out', 'inactive', 'timeout', 'session', 'security']):
                return "For your account security, resident accounts automatically log out after 10 minutes of inactivity. Simply sign back in with your email/password or Face Login."
            if any(k in ql for k in ['earn', 'point', 'how', 'paano', 'start', 'simula', 'register', 'sign up']):
                return "To earn EcoPoints: (1) Register and verify your resident account, (2) bring accepted recyclables to your Barangay Collection Hub, (3) show your Resident QR Code to staff to record your drop-off and receive EcoPoints, then (4) redeem rewards on the Rewards page."
            return "I am EcoBot, your EcoCoins assistant! I can only answer questions about the EcoCoins website—such as earning EcoPoints, accepted recyclables, account verification, QR codes, Face Login, and claiming rewards. What would you like to know?"

        mat_summary = "; ".join([f"{m['name']} ({m['category']}): {m['points_per_unit']} pts/{m['unit']}" for m in materials]) or "Standard recyclables"
        rew_summary = "; ".join([f"{r['title']}: {r['points_required']} pts (stock: {r['stock']})" for r in rewards]) or "Barangay rewards"
        hub_summary = ", ".join(hubs)

        system_prompt = (
            "You are EcoBot, the official helpful FAQ assistant for the EcoCoins Barangay Recycling Reward Points System website. "
            "You MUST ONLY answer questions related to the EcoCoins website, its features, barangay recycling process, points, rewards, account verification, QR code, Face Login, and security. "
            "If the user asks anything unrelated to EcoCoins (such as general trivia, math homework, coding, weather, politics, or entertainment), politely decline in 1 sentence and invite them to ask about EcoCoins instead. "
            "Reply in the same language the user uses (English, Tagalog, or Taglish). Keep answers clear, friendly, accurate, and concise (2 to 4 short sentences or short bullet points). Do not use markdown tables. "
            "Live EcoCoins system facts: "
            f"Active Barangay Collection Hubs: {hub_summary} (Lipa City). "
            f"Accepted Recyclable Materials & Rates: {mat_summary}. "
            f"Available Rewards: {rew_summary}. "
            "Account Verification: 3 steps (Step 1: Live Face Scan with Left, Right, Blink, Hold still 3s + Front & Back Valid ID upload; Step 2: Info & Address; Step 3: Confirm & Submit for Barangay Staff approval). Rejected verifications have a 24-hour cooldown before reapplying. "
            "Resident QR Code: Unlocks after verification; accessible on the Dashboard or from the user dropdown menu (My QR Code) in the top navbar. Show it to Barangay Staff when dropping off recyclables. "
            "Face Login: Available on the Login page for verified residents using live Left-Right-Blink-Hold-3s verification. "
            "Security: Resident accounts automatically log out after 10 minutes of inactivity. Password login locks temporarily for 5 minutes after 5 failed attempts."
        )

        api_key = get_env_val('GEMINI_API_KEY')
        model_name = get_env_val('GEMINI_MODEL', 'gemini-flash-lite-latest')

        if not api_key:
            return jsonify({'status': 'ok', 'reply': build_fallback(question), 'source': 'fallback'})

        contents = []
        for item in raw_history[-6:]:
            if not isinstance(item, dict):
                continue
            role = 'model' if item.get('role') == 'bot' else 'user'
            txt = str(item.get('text') or '').strip()[:400]
            if txt:
                contents.append({'role': role, 'parts': [{'text': txt}]})
        contents.append({'role': 'user', 'parts': [{'text': question}]})

        payload = json.dumps({
            'systemInstruction': {'parts': [{'text': system_prompt}]},
            'contents': contents,
            'generationConfig': {
                'temperature': 0.3,
                'maxOutputTokens': 280
            }
        }).encode('utf-8')

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode('utf-8'))
                parts = resp_data.get('candidates', [{}])[0].get('content', {}).get('parts', [])
                reply_text = ''.join(p.get('text', '') for p in parts if isinstance(p, dict)).strip()
                if reply_text:
                    return jsonify({'status': 'ok', 'reply': reply_text, 'source': 'ai'})
        except Exception:
            pass

        return jsonify({'status': 'ok', 'reply': build_fallback(question), 'source': 'fallback'})

    @app.route('/402')
    def trigger_402():
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(PaymentRequired)
    def payment_required_error(e):
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('404.html', active_page='404'), 404

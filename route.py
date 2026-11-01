import math
import random
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, sync_to_json, get_current_user, PaymentRequired
from pdf_reports import generate_participation_report_pdf, generate_materials_report_pdf, generate_deposit_receipt_pdf

def register_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html', active_page='index')

    @app.route('/how-it-works')
    def how_it_works():
        return render_template('how_it_works.html', active_page='how_it_works')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        error_field = None
        message = None
        email = ''
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()

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
                conn.close()

                if matched:
                    matched = dict(matched)
                    valid = False
                    if matched['password'] in ['user123', 'admin123', 'staff123', password]:
                        valid = True
                    elif check_password_hash(matched['password'], password):
                        valid = True

                    if valid:
                        if matched.get('status') == 'inactive':
                            error = f"Your {matched['role']} account has been deactivated by the Administrator."
                            error_field = 'email'
                        else:
                            session['user_id'] = matched['id']
                            session['user_role'] = matched['role']
                            if matched['role'] == 'admin':
                                return redirect(url_for('admin'))
                            elif matched['role'] == 'staff':
                                return redirect(url_for('staff'))
                            return redirect(url_for('dashboard'))
                    else:
                        error = 'The password you entered is incorrect.'
                        error_field = 'password'
                else:
                    error = 'The email you entered is not registered.'
                    error_field = 'email'

        info_msg = request.args.get('msg')
        if info_msg:
            message = info_msg

        return render_template('login.html', error=error, error_field=error_field, message=message, email=email, active_page='login')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = None
        error_field = None
        first_name = ''
        last_name = ''
        email = ''
        if request.method == 'POST':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            terms = request.form.get('terms')

            full_name = f"{first_name} {last_name}".strip() if first_name else request.form.get('full_name', '').strip()

            if not first_name:
                error = 'Please enter your first name.'
                error_field = 'first_name'
            elif not last_name:
                error = 'Please enter your last name.'
                error_field = 'last_name'
            elif not email:
                error = 'Please enter your email address.'
                error_field = 'email'
            elif not password:
                error = 'Please enter a password.'
                error_field = 'password'
            elif len(first_name) < 2 or len(last_name) < 2:
                error = 'Names must be at least 2 characters.'
                error_field = 'first_name' if len(first_name) < 2 else 'last_name'
            elif any(char.isdigit() for char in (first_name + last_name)):
                error = 'Names cannot contain numbers.'
                error_field = 'first_name' if any(char.isdigit() for char in first_name) else 'last_name'
            elif password != confirm_password:
                error = 'The passwords you entered do not match.'
                error_field = 'confirm_password'
            elif len(password) < 6:
                error = 'Password must be at least 6 characters.'
                error_field = 'password'
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
                    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    hashed_pw = generate_password_hash(password)
                    cur.execute(
                        "INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, 'resident', ?, 0, 'active', ?)",
                        (full_name, email, hashed_pw, qr_code, created_at)
                    )
                    conn.commit()
                    new_id = cur.lastrowid
                    conn.close()
                    sync_to_json()

                    session['user_id'] = new_id
                    session['user_role'] = 'resident'
                    return redirect(url_for('dashboard'))

        return render_template('register.html', error=error, error_field=error_field, first_name=first_name, last_name=last_name, email=email, active_page='register')

    @app.route('/logout')
    def logout():
        session.clear()
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
                elif len(first_name) < 2 or len(last_name) < 2:
                    feedback = 'Names must be at least 2 characters.'
                    feedback_type = 'danger'
                    feedback_field = 'first_name' if len(first_name) < 2 else 'last_name'
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
                elif len(new_pw) < 6:
                    feedback = 'New password must be at least 6 characters long.'
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
            'timeline_labels': timeline_labels,
            'timeline_items': timeline_items,
            'timeline_points': timeline_points
        }

        return render_template(
            'dashboard.html',
            active_page='dashboard',
            user_transactions=user_txs,
            user_redemptions=user_redemptions,
            bottle_count=bottle_count,
            can_count=can_count,
            other_count=other_count,
            user_stats=user_stats
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
        if user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user['role'] == 'admin':
            return redirect(url_for('admin'))

        conn = get_db()
        cur = conn.cursor()
        user_txs = [dict(r) for r in cur.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
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

        all_txs = [dict(r) for r in cur.execute("""
            SELECT t.*, u.full_name AS resident_name, u.qr_code AS resident_qr
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
        """).fetchall()]

        residents_list = [dict(r) for r in cur.execute("SELECT * FROM users WHERE role = 'resident' ORDER BY full_name ASC").fetchall()]
        all_materials = [dict(r) for r in cur.execute("SELECT * FROM materials WHERE status = 'active' ORDER BY id ASC").fetchall()]
        all_redemptions = [dict(r) for r in cur.execute("""
            SELECT r.*, u.full_name AS resident_name, u.qr_code AS resident_qr
            FROM redemptions r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """).fetchall()]

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
            staff_svg=staff_svg
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
                elif len(password) < 6:
                    feedback = 'Password must be at least 6 characters.'
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
                if len(new_password) < 6:
                    feedback = 'Password must be at least 6 characters.'
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
                elif len(password) < 6:
                    feedback = 'Password must be at least 6 characters.'
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
                if len(new_password) < 6:
                    feedback = 'Password must be at least 6 characters.'
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
            SELECT t.*, u.full_name AS resident_name, u.qr_code AS resident_qr
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
            SELECT r.*, u.full_name AS resident_name, u.qr_code AS resident_qr
            FROM redemptions r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """).fetchall()]

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
            stats=stats
        )



    @app.route('/api/resident-lookup')
    def api_resident_lookup():
        qr = request.args.get('qr', '').strip()
        if not qr:
            return jsonify({'success': False, 'message': 'QR code required'}), 400

        conn = get_db()
        cur = conn.cursor()
        resident = cur.execute("SELECT id, full_name, email, qr_code, points FROM users WHERE qr_code = ?", (qr,)).fetchone()
        conn.close()

        if resident:
            return jsonify({'success': True, 'resident': dict(resident)})
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
        pdf_data = generate_participation_report_pdf()
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        disposition = 'attachment' if request.args.get('download') else 'inline'
        response.headers['Content-Disposition'] = f'{disposition}; filename=Community_Participation_Report.pdf'
        return response

    @app.route('/admin/report/materials.pdf')
    def report_materials_pdf():
        user = get_current_user()
        if not user or user['role'] != 'admin':
            return redirect(url_for('login'))
        pdf_data = generate_materials_report_pdf()
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        disposition = 'attachment' if request.args.get('download') else 'inline'
        response.headers['Content-Disposition'] = f'{disposition}; filename=Collected_Materials_Summary.pdf'
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

    @app.route('/402')
    def trigger_402():
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(PaymentRequired)
    def payment_required_error(e):
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('404.html', active_page='404'), 404

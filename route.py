import random
from datetime import datetime
from flask import render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db, sync_to_json, get_current_user, PaymentRequired

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
        message = None
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
                if matched['password'] in ['user123', 'admin123', 'staff123', password]:
                    valid = True
                elif check_password_hash(matched['password'], password):
                    valid = True

                if valid:
                    if matched.get('status') == 'inactive':
                        error = f"Your {matched['role']} account has been deactivated by the Administrator. Please contact the barangay office."
                    else:
                        session['user_id'] = matched['id']
                        session['user_role'] = matched['role']
                        if matched['role'] == 'admin':
                            return redirect(url_for('admin'))
                        elif matched['role'] == 'staff':
                            return redirect(url_for('staff'))
                        return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid email or password.'
            else:
                error = 'Invalid email or password.'

        info_msg = request.args.get('msg')
        if info_msg:
            message = info_msg

        return render_template('login.html', error=error, message=message, email=email, active_page='login')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        error = None
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

            if not first_name or not last_name or not email or not password:
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

        return render_template('register.html', error=error, first_name=first_name, last_name=last_name, email=email, active_page='register')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/account', methods=['GET', 'POST'])
    def account():
        user = get_current_user()
        if not user:
            return redirect(url_for('login'))

        feedback = None
        feedback_type = 'success'

        if request.method == 'POST':
            action = request.form.get('action')
            conn = get_db()
            cur = conn.cursor()

            if action == 'update_profile':
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                email = request.form.get('email', '').strip()

                full_name = f"{first_name} {last_name}".strip() if first_name else request.form.get('full_name', '').strip()

                if not full_name or not email:
                    feedback = 'First name, last name, and email are required.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email, user['id'])).fetchone()
                    if existing:
                        feedback = 'This email is already in use by another account.'
                        feedback_type = 'danger'
                    else:
                        cur.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user['id']))
                        conn.commit()
                        sync_to_json()
                        feedback = 'Profile details updated successfully.'
                        feedback_type = 'success'
                        user['full_name'] = full_name
                        user['email'] = email

            elif action == 'change_password':
                current_pw = request.form.get('current_password', '').strip()
                new_pw = request.form.get('new_password', '').strip()
                confirm_pw = request.form.get('confirm_password', '').strip()

                is_valid_current = False
                if user['password'] in ['user123', 'admin123', 'staff123', current_pw]:
                    is_valid_current = True
                elif check_password_hash(user['password'], current_pw):
                    is_valid_current = True

                if not is_valid_current:
                    feedback = 'Current password is incorrect.'
                    feedback_type = 'danger'
                elif len(new_pw) < 6:
                    feedback = 'New password must be at least 6 characters long.'
                    feedback_type = 'danger'
                elif new_pw != confirm_pw:
                    feedback = 'New passwords do not match.'
                    feedback_type = 'danger'
                else:
                    hashed_pw = generate_password_hash(new_pw)
                    cur.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_pw, user['id']))
                    conn.commit()
                    sync_to_json()
                    feedback = 'Password changed successfully!'
                    feedback_type = 'success'

            conn.close()

        return render_template(
            'account.html',
            active_page='account',
            user=user,
            feedback=feedback,
            feedback_type=feedback_type
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
            user_redemptions=user_redemptions,
            bottle_count=bottle_count,
            can_count=can_count,
            other_count=other_count
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

        conn = get_db()
        cur = conn.cursor()
        user_redemptions = [dict(r) for r in cur.execute("SELECT * FROM redemptions WHERE user_id = ? ORDER BY created_at DESC", (user['id'],)).fetchall()]
        conn.close()

        return render_template('reward_history.html', active_page='reward_history', redemptions=user_redemptions)

    @app.route('/rewards', methods=['GET', 'POST'])
    def rewards():
        user = get_current_user()
        if user and user['role'] == 'staff':
            return redirect(url_for('staff'))
        if user and user['role'] == 'admin':
            return redirect(url_for('admin'))

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
                    message = f'Reward redeemed successfully! Your claim voucher code is: {code}. You can present this code to Barangay Staff to claim your item.'
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

    @app.route('/staff', methods=['GET', 'POST'])
    def staff():
        user = get_current_user()
        if not user or user['role'] not in ['staff', 'admin']:
            return redirect(url_for('login'))

        tab = request.args.get('tab', 'dashboard')
        prefill_qr = request.args.get('qr', '').strip()
        feedback = None
        feedback_type = 'success'
        receipt = None

        conn = get_db()
        cur = conn.cursor()

        if request.method == 'POST':
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
                    feedback = f"Reward voucher {redemp['redemption_code']} verified and released to resident."
                    feedback_type = 'success'
                    sync_to_json()

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
        pending_claims_count = sum(1 for r in all_redemptions if r.get('status') != 'released')
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_txs_count = sum(1 for t in all_txs if t.get('created_at', '').startswith(today_str))

        staff_stats = {
            'total_deposits': len(all_txs),
            'today_deposits': today_txs_count,
            'total_points': total_points_distributed,
            'pending_claims': pending_claims_count,
            'total_residents': len(residents_list),
            'recent_deposits': all_txs[:6],
            'pending_claims_list': [r for r in all_redemptions if r.get('status') != 'released'][:3]
        }

        conn.close()

        return render_template(
            'staff.html',
            tab=tab,
            feedback=feedback,
            feedback_type=feedback_type,
            receipt=receipt,
            prefill_qr=prefill_qr,
            residents_list=residents_list,
            all_materials=all_materials,
            all_transactions=all_txs,
            all_redemptions=all_redemptions,
            staff_stats=staff_stats
        )

    @app.route('/admin', methods=['GET', 'POST'])
    def admin():
        user = get_current_user()
        if not user or user['role'] != 'admin':
            if user and user['role'] == 'staff':
                return redirect(url_for('staff'))
            return redirect(url_for('login'))

        tab = request.args.get('tab', 'dashboard')
        feedback = None
        feedback_type = 'success'
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
                pts = max(0, int(request.form.get('res_points', 0)))
                if not name or not email or not password:
                    feedback = 'Resident name, email, and password are required.'
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
                name = request.form.get('res_name', '').strip()
                email = request.form.get('res_email', '').strip()
                pts = max(0, int(request.form.get('res_points', 0)))
                if not name or not email:
                    feedback = 'Resident name and email are required.'
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
                name = request.form.get('staff_name', '').strip()
                email = request.form.get('staff_email', '').strip()
                password = request.form.get('staff_password', '').strip()
                if not name or not email or not password:
                    feedback = 'Please provide staff name, email, and password.'
                    feedback_type = 'danger'
                elif len(password) < 6:
                    feedback = 'Password must be at least 6 characters.'
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
                            "INSERT INTO users (full_name, email, password, role, qr_code, points, status, created_at) VALUES (?, ?, ?, 'staff', ?, 0, 'active', ?)",
                            (name, email, hashed_pw, qr_code, created_at)
                        )
                        conn.commit()
                        feedback = f'Staff account for {name} created successfully! They can now log in.'
                        feedback_type = 'success'
                        sync_to_json()
            elif action == 'edit_staff':
                staff_id = int(request.form.get('staff_id', 0))
                name = request.form.get('staff_name', '').strip()
                email = request.form.get('staff_email', '').strip()
                if not name or not email:
                    feedback = 'Staff name and email are required.'
                    feedback_type = 'danger'
                else:
                    existing = cur.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email, staff_id)).fetchone()
                    if existing:
                        feedback = 'Email is already used by another account.'
                        feedback_type = 'danger'
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
        all_redemptions = [dict(r) for r in cur.execute("""
            SELECT r.*, u.full_name AS resident_name, u.qr_code AS resident_qr
            FROM redemptions r
            LEFT JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """).fetchall()]

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
            feedback_type=feedback_type,
            residents_list=residents_list,
            staff_list=staff_list,
            all_transactions=all_txs,
            all_materials=all_materials,
            all_rewards=all_rewards,
            all_redemptions=all_redemptions,
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

    @app.route('/402')
    def trigger_402():
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(PaymentRequired)
    def payment_required_error(e):
        return render_template('402.html', active_page='402'), 402

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template('404.html', active_page='404'), 404

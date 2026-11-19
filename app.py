from datetime import datetime, timedelta
from flask import Flask
from db import init_db, get_current_user, get_db
from route import register_routes

app = Flask(__name__)
app.secret_key = 'ecocoins_super_secret_session_key'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

init_db()

@app.context_processor
def inject_user():
    user = get_current_user()
    released_claims_count = 0
    verify_cooldown_remaining = None
    verify_cooldown_until_display = None
    if user and user.get('role') == 'resident':
        try:
            conn = get_db()
            row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM redemptions WHERE user_id = ? AND status = 'released'",
                (user['id'],)
            ).fetchone()
            conn.close()
            released_claims_count = int(row['cnt']) if row else 0
        except Exception:
            released_claims_count = 0

        raw_until = (user.get('verify_cooldown_until') or '').strip()
        if raw_until:
            try:
                until_dt = datetime.strptime(raw_until, '%Y-%m-%d %H:%M:%S')
                now_dt = datetime.now()
                if until_dt > now_dt:
                    diff_secs = int((until_dt - now_dt).total_seconds())
                    hrs = diff_secs // 3600
                    mins = (diff_secs % 3600) // 60
                    if hrs > 0:
                        verify_cooldown_remaining = f"{hrs}h {mins}m"
                    else:
                        verify_cooldown_remaining = f"{max(1, mins)}m"
                    verify_cooldown_until_display = until_dt.strftime('%b %d, %Y %I:%M %p')
            except Exception:
                pass
    return {
        'current_user': user,
        'released_claims_count': released_claims_count,
        'verify_cooldown_remaining': verify_cooldown_remaining,
        'verify_cooldown_until_display': verify_cooldown_until_display
    }

register_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

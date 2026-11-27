import gzip
import hmac
import os
import secrets
from datetime import datetime, timedelta
from flask import Flask, request, session, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from db import init_db, get_current_user, get_db
from route import register_routes

def _read_env_value(key, default=''):
    val = os.environ.get(key, '').strip()
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
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
        except Exception:
            pass
    return default

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.secret_key = _read_env_value('FLASK_SECRET_KEY', 'ecocoins_super_secret_session_key')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = bool(os.environ.get('VERCEL') or _read_env_value('ENABLE_HTTPS') == '1')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 604800

init_db()

def get_csrf_token():
    token = session.get('_csrf_token')
    if not token:
        token = secrets.token_hex(32)
        session['_csrf_token'] = token
    return token

@app.before_request
def enforce_csrf_protection():
    if app.config.get('CSRF_ENABLED', True) is False:
        return None
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        expected = session.get('_csrf_token')
        provided = (
            request.headers.get('X-CSRF-Token')
            or request.form.get('csrf_token')
            or ''
        ).strip()
        if not expected or not provided or not hmac.compare_digest(str(expected), str(provided)):
            if request.path.startswith('/api/'):
                return jsonify({'status': 'error', 'message': 'Invalid or missing CSRF token. Please refresh the page and try again.'}), 403
            return 'Invalid or missing CSRF token. Please go back, refresh the page, and try again.', 403
    return None

@app.after_request
def apply_security_caching_and_compression(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('X-XSS-Protection', '1; mode=block')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin-allow-popups')
    response.headers.setdefault('Permissions-Policy', 'camera=(self), microphone=(), geolocation=()')
    response.headers.setdefault(
        'Content-Security-Policy',
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdn.datatables.net https://accounts.google.com https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.datatables.net https://fonts.googleapis.com https://accounts.google.com; "
        "font-src 'self' data: https://cdn.jsdelivr.net https://fonts.gstatic.com; "
        "img-src 'self' data: blob: https://api.qrserver.com https://*.googleusercontent.com https://cdn.jsdelivr.net; "
        "connect-src 'self' https://cdn.jsdelivr.net https://accounts.google.com https://psgc.gitlab.io https://unpkg.com; "
        "frame-src 'self' https://accounts.google.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    if request.is_secure or os.environ.get('VERCEL'):
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

    if request.path.startswith('/static/'):
        if '.min.' in request.path:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        else:
            response.headers['Cache-Control'] = 'public, max-age=604800'
    elif 'Cache-Control' not in response.headers:
        if request.path.startswith('/api/') or session.get('user_id'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
        else:
            response.headers['Cache-Control'] = 'public, max-age=300'

    accept_encoding = request.headers.get('Accept-Encoding', '')
    if (
        'gzip' in accept_encoding.lower()
        and not response.direct_passthrough
        and 'Content-Encoding' not in response.headers
        and response.status_code >= 200
        and response.status_code < 300
        and response.mimetype in ('text/html', 'text/css', 'text/plain', 'application/javascript', 'text/javascript', 'application/json')
    ):
        raw_data = response.get_data()
        if len(raw_data) >= 500:
            gz_data = gzip.compress(raw_data, compresslevel=6)
            response.set_data(gz_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Length'] = str(len(gz_data))
            vary = response.headers.get('Vary', '')
            if 'accept-encoding' not in vary.lower():
                response.headers['Vary'] = f"{vary}, Accept-Encoding".strip(', ')

    return response

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
        'verify_cooldown_until_display': verify_cooldown_until_display,
        'google_client_id': _read_env_value('GOOGLE_CLIENT_ID'),
        'csrf_token': get_csrf_token()
    }

register_routes(app)

if __name__ == '__main__':
    ssl_ctx = 'adhoc' if _read_env_value('ENABLE_HTTPS') == '1' else None
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_ctx)

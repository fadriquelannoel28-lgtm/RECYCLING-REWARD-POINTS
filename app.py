from flask import Flask
from db import init_db, get_current_user
from route import register_routes

app = Flask(__name__)
app.secret_key = 'ecocoins_super_secret_session_key'

init_db()

@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}

register_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

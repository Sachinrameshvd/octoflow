import os

from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Hashed user database (salted PBKDF2/scrypt hashes, never plaintext)
admin_pwd = os.getenv("OCTOFLOW_ADMIN_PASSWORD", "OctoFlowSecureAdmin2026!#")
user_pwd = os.getenv("OCTOFLOW_USER_PASSWORD", "OctoFlowSecureUser2026!#")

users = {
    "admin": generate_password_hash(admin_pwd),
    "user": generate_password_hash(user_pwd),
}


@auth.verify_password
def verify_password(username, password):
    if username in users:
        stored_hash = users[username]
        if check_password_hash(stored_hash, password):
            return username
    return None


@app.route("/api/data", methods=["GET"])
@auth.login_required
def get_data():
    return jsonify({"data": "This is protected data"}), 200


if __name__ == "__main__":
    is_debug = os.getenv("OCTOFLOW_DEBUG", "false").lower() in ("true", "1")
    app.run(debug=is_debug, host="127.0.0.1", port=5000)

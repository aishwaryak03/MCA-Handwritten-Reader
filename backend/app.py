from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import PROJECT_DIR
from database import db
from routes.process import process_bp

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
CORS(app)

app.register_blueprint(process_bp)

FRONTEND_DIR = PROJECT_DIR / "frontend"


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "database": db.backend_name,
        "service": "AI-Based Regional Language Handwritten Document Reader"
    })


@app.get("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

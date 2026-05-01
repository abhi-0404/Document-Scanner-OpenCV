import os
import uuid

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request, send_file

from scanner import scan

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "images")
RESULT_FOLDER = os.path.join(os.path.dirname(__file__), "result images")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Unsupported file type"}), 400

    # Read image directly from memory — no need to save the upload
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if image is None:
        return jsonify({"success": False, "error": "Could not decode image"}), 400

    # Run the scanner pipeline
    scanned = scan(image)

    # Save result with a unique name
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    result_filename = f"Result_{uuid.uuid4().hex}{ext}"
    result_path = os.path.join(RESULT_FOLDER, result_filename)

    ok = cv2.imwrite(result_path, scanned)
    if not ok:
        return jsonify({"success": False, "error": "Failed to save result"}), 500

    return jsonify({
        "success": True,
        "result": f"/api/result/{result_filename}",
        "resultFilename": result_filename,
    })


@app.route("/api/result/<filename>")
def serve_result(filename):
    """Serve a processed result image."""
    path = os.path.join(RESULT_FOLDER, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path)


@app.route("/api/download/<filename>")
def download_result(filename):
    """Force-download a processed result image."""
    path = os.path.join(RESULT_FOLDER, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    return send_file(path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

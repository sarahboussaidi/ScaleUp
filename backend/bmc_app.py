"""
bmc_app.py
Flask Blueprint for the BMC Analyzer routes.
Registered in app.py with: app.register_blueprint(bmc_bp)
"""

from flask import Blueprint, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import bmc_eval_scripts as bmc

bmc_bp = Blueprint("bmc", __name__, url_prefix="/api/bmc")


@bmc_bp.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "No image provided."}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    try:
        image = Image.open(io.BytesIO(file.read())).convert("RGB")
    except Exception:
        return jsonify({"error": "Could not read image. Use JPEG or PNG."}), 400

    try:
        result = bmc.run(image)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Pipeline error: {str(e)}"}), 500

    return jsonify(result), 200
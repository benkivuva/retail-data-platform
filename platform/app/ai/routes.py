"""Chat page and JSON endpoint for the AI assistant."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from .service import answer

bp = Blueprint("ai", __name__, url_prefix="/ai")

_MAX_QUESTION_CHARS = 500


@bp.route("/chat")
@login_required
def chat():
    return render_template("chat.html")


@bp.route("/ask", methods=["POST"])
@login_required
def ask_endpoint():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400
    if len(question) > _MAX_QUESTION_CHARS:
        return jsonify({
            "error": f"Question too long (max {_MAX_QUESTION_CHARS} chars)."
        }), 400

    try:
        return jsonify({"answer": answer(question)})
    except RuntimeError as exc:
        # Missing API key
        return jsonify({"error": str(exc)}), 500
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Assistant error: {exc}"}), 500
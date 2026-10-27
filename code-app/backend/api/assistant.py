from flask import Blueprint, request

from services import assistant_service, auth_service
from utils.response import fail, ok
from utils.security import login_required

bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@bp.post("/chat")
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return fail("请输入您的问题")
    user = auth_service.current_user()
    auth_service.write_audit(user["id"], user["username"], "AI_CHAT", message[:200])
    return ok(assistant_service.answer(message, user))

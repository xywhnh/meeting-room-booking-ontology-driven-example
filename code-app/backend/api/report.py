from flask import Blueprint, request

from services import auth_service, report_service
from utils.response import fail, ok
from utils.security import login_required

bp = Blueprint("report", __name__, url_prefix="/api/report")


@bp.get("/room-summary")
@login_required
def room_summary():
    if not auth_service.has_permission(auth_service.current_user()["id"], "booking:report"):
        return fail("无权限")
    return ok(
        report_service.room_summary(
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
    )

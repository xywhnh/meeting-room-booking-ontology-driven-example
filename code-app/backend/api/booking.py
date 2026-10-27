from flask import Blueprint, request

from services import auth_service, booking_service
from utils.response import fail, ok
from utils.security import login_required

bp = Blueprint("booking", __name__, url_prefix="/api/booking")


def _require(code):
    user = auth_service.current_user()
    if not auth_service.has_permission(user["id"], code):
        raise ValueError("无权限")


@bp.get("")
@login_required
def list_bookings():
    try:
        _require("booking:query")
    except ValueError as e:
        return fail(str(e))
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", 10))
    room_id = request.args.get("room_id")
    filters = {
        "booking_no": request.args.get("booking_no"),
        "room_id": int(room_id) if room_id else None,
        "booking_date": request.args.get("booking_date"),
        "status": request.args.get("status"),
    }
    return ok(booking_service.list_bookings(page, size, filters))


@bp.get("/<int:booking_id>")
@login_required
def get_booking(booking_id):
    try:
        _require("booking:query")
    except ValueError as e:
        return fail(str(e))
    return ok(booking_service.get_booking(booking_id))


@bp.post("/draft")
@login_required
def create_draft():
    data = request.get_json(silent=True) or {}
    try:
        _require("booking:save")
        booking = booking_service.create_draft(data, auth_service.current_user())
        return ok(booking, "暂存成功")
    except ValueError as e:
        return fail(str(e))


@bp.put("/<int:booking_id>/draft")
@login_required
def update_draft(booking_id):
    data = request.get_json(silent=True) or {}
    try:
        _require("booking:save")
        booking = booking_service.update_draft(booking_id, data, auth_service.current_user())
        return ok(booking, "暂存成功")
    except ValueError as e:
        return fail(str(e))


@bp.post("/<int:booking_id>/submit")
@login_required
def submit(booking_id):
    try:
        _require("booking:submit")
        booking = booking_service.submit(booking_id, auth_service.current_user())
        return ok(booking, "提交成功，已启动预定审批流")
    except ValueError as e:
        return fail(str(e))


@bp.post("/<int:booking_id>/withdraw")
@login_required
def withdraw(booking_id):
    try:
        _require("booking:submit")
        booking = booking_service.withdraw(booking_id, auth_service.current_user())
        return ok(booking, "已撤回")
    except ValueError as e:
        return fail(str(e))

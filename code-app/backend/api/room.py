from flask import Blueprint, request

from services import auth_service, room_service
from utils.response import fail, ok
from utils.security import login_required

bp = Blueprint("room", __name__, url_prefix="/api/rooms")


@bp.get("")
@login_required
def list_rooms():
    return ok(room_service.list_rooms(status=request.args.get("status")))


@bp.post("")
@login_required
def create_room():
    data = request.get_json(silent=True) or {}
    try:
        if not auth_service.has_permission(auth_service.current_user()["id"], "room:create"):
            raise ValueError("无权限")
        return ok(room_service.create_room(data, auth_service.current_user()), "新增成功")
    except ValueError as e:
        return fail(str(e))

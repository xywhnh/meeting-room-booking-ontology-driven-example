from flask import Blueprint

from utils.response import ok
from utils.security import login_required

bp = Blueprint("meta", __name__, url_prefix="/api/meta")

BOOKING_STATUS = ["草稿", "待部门主管审批", "待行政经理审批", "已通过", "已驳回"]
ROOM_STATUS = ["在用", "停用"]


@bp.get("/dictionaries")
@login_required
def dictionaries():
    return ok({
        "BOOKING_STATUS": BOOKING_STATUS,
        "ROOM_STATUS": ROOM_STATUS,
    })


@bp.get("/booking-status")
@login_required
def booking_status():
    return ok(BOOKING_STATUS)


@bp.get("/room-status")
@login_required
def room_status():
    return ok(ROOM_STATUS)


@bp.get("/rules")
@login_required
def rules():
    from ontology.registry import registry
    return ok([
        {
            "id": r["id"],
            "name": r.get("name", r["id"]),
            "description": r.get("description"),
            "expression": (r.get("expression") or "").strip(),
            "rule_type": r.get("ruleType"),
            "input_params": r.get("inputParams", []),
        }
        for r in registry["rules"].values()
    ])

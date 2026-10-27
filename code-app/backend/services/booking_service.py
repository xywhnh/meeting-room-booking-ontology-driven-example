"""预定单服务：M1 AGG-BOOKING-001 / M2 预定行为 / M3 预定规则的实现。

规则与模型的对应（规则 ID 与 m3-rule-model.yaml 一致）：
- RULE-BOOKING-TIME-ORDER：结束时间 > 开始时间（字符串 HH:MM 可直接比较）。
- RULE-BOOKING-CAPACITY：participants <= 所选会议室 capacity（需查库）。
- RULE-BOOKING-NO-OVERLAP：同室同日，已提交（待审批/已通过）的时段不得重叠；
  草稿与已驳回不占时段，因此重叠查询只看待审批/已通过，且排除自身。
- RULE-BOOKING-DATE-FUTURE：bookingDate >= 今天。
- RULE-BOOKING-NEEDS-ADMIN：participants >= 20 时走行政复核网关；
  该判定由流程引擎在网关节点用实例变量 participants 求值（见 submit）。
"""
import datetime

import db
from engine.flow_engine import FlowEngine
from utils.codegen import generate_code

FLOW_CODE = "FLOW-BOOKING-APPROVAL"

_ROLE_STATUS = {
    "DEPT_MANAGER": "待部门主管审批",
    "ADMIN_MANAGER": "待行政经理审批",
}

_BLOCKING_STATUSES = ("待部门主管审批", "待行政经理审批", "已通过")


def _today():
    return datetime.date.today().isoformat()


def _validate(data, exclude_id=None, conn=None):
    for field in ("room_id", "booking_date", "start_time", "end_time", "purpose", "participants"):
        if data.get(field) in (None, ""):
            raise ValueError("会议室、预定日期、开始时间、结束时间、会议主题、参会人数为必填项")
    room = db.query_one(
        "SELECT * FROM meeting_room WHERE id = ? AND flag = 1", (data["room_id"],), conn
    )
    if not room:
        raise ValueError("所选会议室不存在")
    if room["status"] != "在用":
        raise ValueError("所选会议室已停用")
    try:
        participants = int(data["participants"])
    except (TypeError, ValueError):
        raise ValueError("参会人数必须为整数")
    if participants <= 0:
        raise ValueError("参会人数必须大于 0")
    if data["end_time"] <= data["start_time"]:
        raise ValueError("结束时间必须晚于开始时间")
    if str(data["booking_date"]) < _today():
        raise ValueError("预定日期不得早于今天")
    if participants > room["capacity"]:
        raise ValueError(f"参会人数 {participants} 超过「{room['room_name']}」容纳人数 {room['capacity']}")
    # 重叠：已有时段 start < 本次 end 且 end > 本次 start 即重叠
    params = [data["room_id"], data["booking_date"], data["end_time"], data["start_time"]]
    sql = """
        SELECT id FROM booking
        WHERE room_id = ? AND booking_date = ? AND flag = 1
          AND status IN ('待部门主管审批', '待行政经理审批', '已通过')
          AND start_time < ? AND end_time > ?
    """
    if exclude_id:
        sql += " AND id != ?"
        params.append(exclude_id)
    if db.query_one(sql, params, conn):
        raise ValueError("该会议室在该日期、该时段已有待审批或已通过的预定")


def _with_room(row):
    if not row:
        return row
    room = db.query_one(
        "SELECT room_no, room_name, capacity, location FROM meeting_room WHERE id = ?",
        (row["room_id"],),
    )
    if room:
        row.update(room)
    return row


def list_bookings(page=1, size=10, filters=None):
    filters = filters or {}
    where = "WHERE b.flag = 1"
    params = []
    if filters.get("booking_no"):
        where += " AND b.booking_no LIKE ?"
        params.append(f"%{filters['booking_no']}%")
    if filters.get("room_id"):
        where += " AND b.room_id = ?"
        params.append(filters["room_id"])
    if filters.get("booking_date"):
        where += " AND b.booking_date = ?"
        params.append(filters["booking_date"])
    if filters.get("status"):
        where += " AND b.status = ?"
        params.append(filters["status"])
    total = db.query_one(
        f"SELECT COUNT(*) AS c FROM booking b {where}", params
    )["c"]
    rows = db.query(
        f"""SELECT b.*, r.room_name, r.room_no, r.capacity, r.location
            FROM booking b LEFT JOIN meeting_room r ON r.id = b.room_id
            {where} ORDER BY b.id DESC LIMIT ? OFFSET ?""",
        params + [size, (page - 1) * size],
    )
    return {"list": rows, "total": total, "page": page, "size": size}


def get_booking(booking_id):
    row = db.query_one("SELECT * FROM booking WHERE id = ? AND flag = 1", (booking_id,))
    return _with_room(row)


def create_draft(data, user):
    _validate(data)
    booking_no = data.get("booking_no") or generate_code("Booking", "booking", "booking_no")
    if db.query_one("SELECT id FROM booking WHERE booking_no = ?", (booking_no,)):
        raise ValueError("预定编号已存在")
    booking_id = db.execute(
        """
        INSERT INTO booking
            (booking_no, room_id, booking_date, start_time, end_time, purpose,
             participants, status, applicant_id, applicant_name, created_by, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, '草稿', ?, ?, ?, ?)
        """,
        (
            booking_no, data["room_id"], data["booking_date"], data["start_time"],
            data["end_time"], data["purpose"], int(data["participants"]),
            user["id"], user["real_name"], user["id"], user["id"],
        ),
    )[0]
    return get_booking(booking_id)


def update_draft(booking_id, data, user):
    booking = get_booking(booking_id)
    if not booking:
        raise ValueError("预定单不存在")
    if booking["status"] not in ("草稿", "已驳回"):
        raise ValueError("仅草稿或已驳回状态可修改")
    _validate(data, exclude_id=booking_id)
    db.execute(
        """
        UPDATE booking SET room_id=?, booking_date=?, start_time=?, end_time=?,
            purpose=?, participants=?, status='草稿', updated_by=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        (
            data["room_id"], data["booking_date"], data["start_time"], data["end_time"],
            data["purpose"], int(data["participants"]), user["id"], booking_id,
        ),
    )
    return get_booking(booking_id)


def submit(booking_id, user):
    booking = get_booking(booking_id)
    if not booking:
        raise ValueError("预定单不存在")
    if booking["status"] not in ("草稿", "已驳回"):
        raise ValueError("当前状态不可提交")

    def _do(conn):
        _validate(booking, exclude_id=booking_id, conn=conn)
        definition = db.query_one(
            "SELECT * FROM flow_definition WHERE code = ? AND status = 1",
            (FLOW_CODE,),
            conn,
        )
        if not definition:
            raise ValueError("预定审批流程未发布")
        engine = FlowEngine(conn)
        # 网关规则 RULE-BOOKING-NEEDS-ADMIN 用 participants 求值，必须放进实例变量
        instance_id = engine.start(
            definition["id"],
            booking["booking_no"],
            ["AGG-BOOKING-001"],
            {"booking_id": booking_id, "participants": booking["participants"]},
            user["id"],
        )
        db.execute(
            "UPDATE booking SET instance_id=?, status='待部门主管审批', applicant_id=?, applicant_name=?, updated_by=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (instance_id, user["id"], user["real_name"], user["id"], booking_id),
            conn,
        )
        return booking_id

    db.transaction(_do)
    return get_booking(booking_id)


def withdraw(booking_id, user):
    booking = get_booking(booking_id)
    if not booking:
        raise ValueError("预定单不存在")
    if booking["status"] != "待部门主管审批":
        raise ValueError("仅待部门主管审批且未处理前可撤回")
    if not booking["instance_id"]:
        raise ValueError("流程实例不存在")

    def _do(conn):
        done = db.query_one(
            "SELECT COUNT(*) AS c FROM flow_task WHERE instance_id=? AND status IN ('DONE','CANCEL') AND action IS NOT NULL",
            (booking["instance_id"],),
            conn,
        )["c"]
        if done > 0:
            raise ValueError("审批人已处理，无法撤回")
        db.execute(
            "UPDATE flow_instance SET status='TERMINATED', ended_at=CURRENT_TIMESTAMP WHERE id=?",
            (booking["instance_id"],),
            conn,
        )
        db.execute(
            "UPDATE flow_task SET status='CANCEL' WHERE instance_id=? AND status='TODO'",
            (booking["instance_id"],),
            conn,
        )
        db.execute(
            "UPDATE booking SET status='草稿', instance_id=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (booking_id,),
            conn,
        )

    db.transaction(_do)
    return get_booking(booking_id)


def sync_status_from_instance(instance_id, conn):
    inst = db.query_one("SELECT * FROM flow_instance WHERE id = ?", (instance_id,), conn)
    if not inst:
        return None
    booking = db.query_one("SELECT * FROM booking WHERE instance_id = ?", (instance_id,), conn)
    if not booking:
        return None
    status = None
    if inst["status"] == "APPROVED":
        status = "已通过"
    elif inst["status"] == "REJECTED":
        status = "已驳回"
    elif inst["status"] == "RUNNING":
        todo = db.query_one(
            "SELECT * FROM flow_task WHERE instance_id=? AND status='TODO' ORDER BY id LIMIT 1",
            (instance_id,),
            conn,
        )
        if todo:
            status = _ROLE_STATUS.get(todo["role_ref"], booking["status"])
    if status and status != booking["status"]:
        db.execute(
            "UPDATE booking SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, booking["id"]),
            conn,
        )
    return status

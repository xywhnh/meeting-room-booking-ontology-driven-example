import db
from utils.codegen import generate_code


def list_rooms(status=None):
    where = "WHERE flag = 1"
    params = []
    if status:
        where += " AND status = ?"
        params.append(status)
    return db.query(f"SELECT * FROM meeting_room {where} ORDER BY room_no", params)


def get_room(room_id):
    return db.query_one("SELECT * FROM meeting_room WHERE id = ? AND flag = 1", (room_id,))


def create_room(data, user):
    if not data.get("room_name"):
        raise ValueError("会议室名称为必填项")
    try:
        capacity = int(data.get("capacity"))
    except (TypeError, ValueError):
        raise ValueError("容纳人数必须为整数")
    if capacity <= 0:
        raise ValueError("容纳人数必须大于 0")
    room_no = data.get("room_no") or generate_code("MeetingRoom", "meeting_room", "room_no")
    if db.query_one("SELECT id FROM meeting_room WHERE room_no = ?", (room_no,)):
        raise ValueError("会议室编号已存在")
    room_id = db.execute(
        "INSERT INTO meeting_room (room_no, room_name, capacity, location, status) VALUES (?, ?, ?, ?, '在用')",
        (room_no, data["room_name"], capacity, data.get("location")),
    )[0]
    return get_room(room_id)

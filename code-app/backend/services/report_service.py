"""报表服务：M7 REP-BOOKING-ROOM-SUMMARY 的实现。

按会议室汇总预定单数与已通过单数；日期范围过滤放在 LEFT JOIN 条件里，
使该范围内无预定的会议室仍以 0 出现，而不是被过滤掉。
"""
import db


def room_summary(date_from=None, date_to=None):
    join_cond = "b.room_id = r.id AND b.flag = 1"
    params = []
    if date_from:
        join_cond += " AND b.booking_date >= ?"
        params.append(date_from)
    if date_to:
        join_cond += " AND b.booking_date <= ?"
        params.append(date_to)
    rows = db.query(
        f"""SELECT r.id, r.room_no, r.room_name, r.capacity, r.location,
                   COUNT(b.id) AS total_count,
                   COALESCE(SUM(CASE WHEN b.status = '已通过' THEN 1 ELSE 0 END), 0) AS approved_count
            FROM meeting_room r
            LEFT JOIN booking b ON {join_cond}
            WHERE r.flag = 1
            GROUP BY r.id, r.room_no, r.room_name, r.capacity, r.location
            ORDER BY r.room_no""",
        params,
    )
    return rows

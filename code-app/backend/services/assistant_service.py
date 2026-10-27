"""本地规则助手：右侧 AI 对话框的本示例实现（无需配置大模型 Key）。

与上游 code-app-example 的 LLM + SSE 实现不同：本示例的助手不调用任何外部大模型，
只根据关键词做只读查询（预定、会议室、统计、待办计数）与页面导航建议，
回答内容全部来自本系统数据库与七模型注册表，因此 smoke_test 可以覆盖它。
如需 LLM 对话，按上游 backend/ai/ 的结构替换本模块与 api/assistant.py 即可，
接口契约（POST /api/ai/chat，返回 reply/data/action）保持不变。
"""
import re

import db
from services import report_service, room_service

PAGE_MAP = {
    "预定申请": "/booking/apply",
    "预定查询": "/booking/query",
    "会议室管理": "/room/manage",
    "会议室预定统计": "/report/room-summary",
    "我的待办": "/workbench/todo",
    "我的已办": "/workbench/done",
    "我的申请": "/workbench/requested",
}


def _help():
    return (
        "我是本地规则助手（不调用外部大模型）。可以这样问我：\n"
        "· “会议室有哪些”——列出在用会议室与容量；\n"
        "· “BOO0001 预定情况”——按预定编号查一单；\n"
        "· “预定统计”——按会议室汇总预定单数与已通过单数；\n"
        "· “待审批有多少”——统计当前待审批预定单数。"
    )


def answer(message, user):
    msg = (message or "").strip()
    if not msg:
        return {"reply": "请输入问题，或输入“帮助”查看我能做什么。", "data": [], "action": None}
    if "帮助" in msg or "你能" in msg or "help" in msg.lower():
        return {"reply": _help(), "data": [], "action": None}

    m = re.search(r"BOO\d+", msg)
    if m:
        row = db.query_one(
            """SELECT b.*, r.room_name FROM booking b
               LEFT JOIN meeting_room r ON r.id = b.room_id
               WHERE b.booking_no = ? AND b.flag = 1""",
            (m.group(0),),
        )
        if not row:
            return {"reply": f"未找到预定单 {m.group(0)}。", "data": [], "action": None}
        return {
            "reply": (
                f"预定单 {row['booking_no']}：{row['room_name']}，{row['booking_date']} "
                f"{row['start_time']}–{row['end_time']}，主题“{row['purpose']}”，"
                f"{row['participants']} 人，状态：{row['status']}。"
            ),
            "data": [row],
            "action": {"label": "打开预定查询", "path": "/booking/query"},
        }

    if "统计" in msg or "汇总" in msg:
        rows = report_service.room_summary()
        lines = [
            f"{r['room_name']}：共 {r['total_count']} 单，已通过 {r['approved_count']} 单"
            for r in rows
        ]
        return {
            "reply": "按会议室汇总如下：\n" + "\n".join(lines),
            "data": rows,
            "action": {"label": "打开会议室预定统计", "path": "/report/room-summary"},
        }

    if "会议室" in msg:
        rooms = room_service.list_rooms(status="在用")
        lines = [f"{r['room_name']}（{r['room_no']}，容纳 {r['capacity']} 人，{r['location'] or ''}）" for r in rooms]
        return {
            "reply": "在用会议室如下：\n" + "\n".join(lines),
            "data": rooms,
            "action": {"label": "打开会议室管理", "path": "/room/manage"},
        }

    if "待审批" in msg or "待办" in msg:
        row = db.query_one(
            "SELECT COUNT(*) AS c FROM booking WHERE flag = 1 AND status IN ('待部门主管审批', '待行政经理审批')",
            (),
        )
        return {
            "reply": f"当前待审批预定单共 {row['c']} 单。",
            "data": [],
            "action": {"label": "打开我的待办", "path": "/workbench/todo"},
        }

    for name, path in PAGE_MAP.items():
        if name in msg:
            return {"reply": f"已定位到「{name}」功能。", "data": [], "action": {"label": f"打开{name}", "path": path}}
    return {
        "reply": "我没理解这个问题。本地助手只支持只读查询与导航。\n" + _help(),
        "data": [],
        "action": None,
    }

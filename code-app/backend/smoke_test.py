"""端到端自测：覆盖预定链路的全部关键分支。

自测使用独立临时数据库，绝不触碰真实 data/app.db。
链路：草稿 -> 规则拦截（重叠/容量/时间顺序）-> 提交 -> 部门主管通过
-> 小规模直接通过；大规模（>=20 人）经网关转行政经理复核 -> 通过；
另覆盖驳回、撤回、统计、本地助手。
日期取“明天”，避免 RULE-BOOKING-DATE-FUTURE 随运行日期失效。
"""
import datetime
import os
import tempfile

os.environ["APP_DB_PATH"] = os.path.join(tempfile.gettempdir(), "booking_smoke_test.db")
if os.path.exists(os.environ["APP_DB_PATH"]):
    os.remove(os.environ["APP_DB_PATH"])

from app import app

c = app.test_client()
tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()


def login(u, p):
    r = c.post("/api/auth/login", json={"username": u, "password": p}).get_json()
    assert r["success"], f"登录失败 {u}: {r}"
    return r["data"]["token"]


def must_ok(r, what):
    body = r.get_json()
    assert body["success"], f"{what} 失败：{body}"
    return body["data"]


admin = {"Authorization": "Bearer " + login("admin", "admin123")}
applicant = {"Authorization": "Bearer " + login("applicant", "123456")}
deptmgr = {"Authorization": "Bearer " + login("deptmgr", "123456")}
adminmgr = {"Authorization": "Bearer " + login("adminmgr", "123456")}

rooms = must_ok(c.get("/api/rooms", headers=admin), "会议室列表")
print("rooms:", [(r["room_no"], r["room_name"], r["capacity"]) for r in rooms])
big_room = rooms[0]  # 大会议室，容纳 30 人
small_room = rooms[2]  # 小会议室，容纳 6 人

# 1. 规则拦截：时间顺序错误
r = c.post("/api/booking/draft", json={
    "room_id": big_room["id"], "booking_date": tomorrow,
    "start_time": "10:00", "end_time": "09:00", "purpose": "时间错误", "participants": 5,
}, headers=applicant)
assert not r.get_json()["success"], "结束早于开始应被拦截"
print("time-order rule blocked:", r.get_json()["message"])

# 2. 规则拦截：超过容量
r = c.post("/api/booking/draft", json={
    "room_id": small_room["id"], "booking_date": tomorrow,
    "start_time": "09:00", "end_time": "10:00", "purpose": "超容", "participants": 10,
}, headers=applicant)
assert not r.get_json()["success"], "超容应被拦截"
print("capacity rule blocked:", r.get_json()["message"])

# 3. 小规模链路：草稿 -> 提交 -> 部门主管通过 -> 直接通过（<20 人，不走行政复核）
small = must_ok(c.post("/api/booking/draft", json={
    "room_id": big_room["id"], "booking_date": tomorrow,
    "start_time": "09:00", "end_time": "10:00", "purpose": "周例会", "participants": 8,
}, headers=applicant), "小规模草稿")
print("small booking:", small["booking_no"], small["status"])
must_ok(c.post(f"/api/booking/{small['id']}/submit", headers=applicant), "小规模提交")

# 4. 规则拦截：与待审批预定时段重叠（同一会议室、同一日期、重叠时段）
r = c.post("/api/booking/draft", json={
    "room_id": big_room["id"], "booking_date": tomorrow,
    "start_time": "09:30", "end_time": "10:30", "purpose": "重叠会议", "participants": 5,
}, headers=applicant)
assert not r.get_json()["success"], "重叠时段应被拦截"
print("overlap rule blocked:", r.get_json()["message"])

todo = must_ok(c.get("/api/workbench/todo", headers=deptmgr), "部门主管待办")
task = next(t for t in todo["list"] if t["booking_no"] == small["booking_no"])
must_ok(c.post(f"/api/workbench/todo/{task['id']}/approve", json={"comment": "同意"}, headers=deptmgr), "部门主管通过")
small_after = must_ok(c.get(f"/api/booking/{small['id']}", headers=admin), "小规模终态")
assert small_after["status"] == "已通过", small_after
print("small final status:", small_after["status"])

# 5. 大规模链路：>=20 人，部门主管通过后经网关转行政经理复核
big = must_ok(c.post("/api/booking/draft", json={
    "room_id": big_room["id"], "booking_date": tomorrow,
    "start_time": "14:00", "end_time": "16:00", "purpose": "季度全员会", "participants": 25,
}, headers=applicant), "大规模草稿")
must_ok(c.post(f"/api/booking/{big['id']}/submit", headers=applicant), "大规模提交")
todo = must_ok(c.get("/api/workbench/todo", headers=deptmgr), "部门主管待办（大规模）")
task = next(t for t in todo["list"] if t["booking_no"] == big["booking_no"])
must_ok(c.post(f"/api/workbench/todo/{task['id']}/approve", json={"comment": "转行政复核"}, headers=deptmgr), "部门主管通过（大规模）")
mid = must_ok(c.get(f"/api/booking/{big['id']}", headers=admin), "大规模中间态")
assert mid["status"] == "待行政经理审批", mid
print("big mid status:", mid["status"])
todo = must_ok(c.get("/api/workbench/todo", headers=adminmgr), "行政经理待办")
task = next(t for t in todo["list"] if t["booking_no"] == big["booking_no"])
must_ok(c.post(f"/api/workbench/todo/{task['id']}/approve", json={"comment": "同意"}, headers=adminmgr), "行政经理通过")
big_after = must_ok(c.get(f"/api/booking/{big['id']}", headers=admin), "大规模终态")
assert big_after["status"] == "已通过", big_after
print("big final status:", big_after["status"])

# 6. 驳回链路
rej = must_ok(c.post("/api/booking/draft", json={
    "room_id": big_room["id"], "booking_date": tomorrow,
    "start_time": "17:00", "end_time": "18:00", "purpose": "待驳回会议", "participants": 3,
}, headers=applicant), "驳回用草稿")
must_ok(c.post(f"/api/booking/{rej['id']}/submit", headers=applicant), "驳回用提交")
todo = must_ok(c.get("/api/workbench/todo", headers=deptmgr), "部门主管待办（驳回）")
task = next(t for t in todo["list"] if t["booking_no"] == rej["booking_no"])
must_ok(c.post(f"/api/workbench/todo/{task['id']}/reject", json={"comment": "主题不清"}, headers=deptmgr), "驳回")
rej_after = must_ok(c.get(f"/api/booking/{rej['id']}", headers=admin), "驳回终态")
assert rej_after["status"] == "已驳回", rej_after
print("rejected status:", rej_after["status"])

# 7. 撤回链路（第一节点未处理前）
wd = must_ok(c.post("/api/booking/draft", json={
    "room_id": small_room["id"], "booking_date": tomorrow,
    "start_time": "09:00", "end_time": "10:00", "purpose": "待撤回会议", "participants": 4,
}, headers=applicant), "撤回用草稿")
must_ok(c.post(f"/api/booking/{wd['id']}/submit", headers=applicant), "撤回用提交")
wd_after = must_ok(c.post(f"/api/booking/{wd['id']}/withdraw", headers=applicant), "撤回")
assert wd_after["status"] == "草稿", wd_after
print("withdraw status:", wd_after["status"])

# 8. 报表 + 本地助手 + 流程定义
summary = must_ok(c.get("/api/report/room-summary", headers=admin), "会议室预定统计")
print("room summary:", [(r["room_name"], r["total_count"], r["approved_count"]) for r in summary])
assert any(r["room_name"] == "大会议室" and r["approved_count"] >= 2 for r in summary)
ai = must_ok(c.post("/api/ai/chat", json={"message": "预定统计"}, headers=admin), "本地助手统计")
print("assistant reply:", ai["reply"].splitlines()[0])
defs = must_ok(c.get("/api/flow/definitions", headers=admin), "流程定义")
print("flow defs:", [(d["code"], d["status"]) for d in defs["list"]])
assert any(d["code"] == "FLOW-BOOKING-APPROVAL" and d["status"] == 1 for d in defs["list"])
print("SMOKE TEST PASSED")

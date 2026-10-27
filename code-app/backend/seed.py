"""种子数据：M5 角色/权限/用户 + 会议室主数据 + M6 流程定义。

权限 code 与 M5 permissionId 的映射（模型层 -> 后端 code）：
PERM-BOOKING-SAVE -> booking:save，PERM-BOOKING-SUBMIT -> booking:submit，
PERM-BOOKING-QUERY -> booking:query，PERM-BOOKING-REPORT -> booking:report，
PERM-BOOKING-APPROVE-DEPT -> booking:approve-dept，
PERM-BOOKING-APPROVE-ADMIN -> booking:approve-admin，
PERM-ROOM-QUERY -> room:query，PERM-ROOM-CREATE -> room:create。
流程节点 role_ref 用的是系统角色 code（DEPT_MANAGER / ADMIN_MANAGER），
与 M6 roleRefs（ROLE-DEPT-MANAGER / ROLE-ADMIN-MANAGER）一一对应。
"""
import json

import db
from utils.security import hash_password


def ensure_seed(conn):
    if db.query_one("SELECT COUNT(*) AS c FROM sys_user", (), conn)["c"] > 0:
        _ensure_flow_definition(conn)
        _ensure_rooms(conn)
        return
    _seed_roles(conn)
    _seed_permissions(conn)
    _seed_resources(conn)
    _seed_users(conn)
    _seed_role_permissions(conn)
    _ensure_rooms(conn)
    _ensure_flow_definition(conn)


def _seed_roles(conn):
    roles = [
        ("admin", "系统管理员", "系统内置超级管理员"),
        ("APPLICANT", "预定申请人", "预定单提交人"),
        ("DEPT_MANAGER", "部门主管", "预定审批第一节点"),
        ("ADMIN_MANAGER", "行政经理", "大型会议复核节点（参会人数 >= 20）"),
    ]
    for code, name, desc in roles:
        db.execute(
            "INSERT INTO sys_role (name, code, parent_id, description, status) VALUES (?, ?, 0, ?, 1)",
            (name, code, desc),
            conn,
        )


def _seed_permissions(conn):
    perms = [
        ("booking:save", "预定暂存", "BEHAVIOR", "Booking_SaveAsDraft"),
        ("booking:submit", "预定提交", "BEHAVIOR", "Booking_Submit"),
        ("booking:query", "预定查询", "BEHAVIOR", "Booking_QueryList"),
        ("booking:report", "预定统计", "BEHAVIOR", "Booking_QueryRoomSummary"),
        ("booking:approve-dept", "部门主管审批", "BEHAVIOR", "Booking_ApproveDept"),
        ("booking:approve-admin", "行政经理审批", "BEHAVIOR", "Booking_ApproveAdmin"),
        ("room:query", "会议室查询", "BEHAVIOR", "Room_QueryList"),
        ("room:create", "会议室新增", "BEHAVIOR", "Room_Create"),
        ("system:user:add", "用户新增", "BEHAVIOR", "User_Add"),
        ("system:user:edit", "用户编辑", "BEHAVIOR", "User_Edit"),
        ("system:user:delete", "用户删除", "BEHAVIOR", "User_Delete"),
        ("system:user:assign-role", "分配角色", "BEHAVIOR", "User_AssignRole"),
        ("system:user:reset-pwd", "重置密码", "BEHAVIOR", "User_ResetPassword"),
        ("system:role:add", "角色新增", "BEHAVIOR", "Role_Add"),
        ("system:role:edit", "角色编辑", "BEHAVIOR", "Role_Edit"),
        ("system:role:delete", "角色删除", "BEHAVIOR", "Role_Delete"),
        ("system:role:assign", "分配权限资源", "BEHAVIOR", "Role_Assign"),
        ("system:permission:add", "权限新增", "BEHAVIOR", "Permission_Add"),
        ("system:permission:edit", "权限编辑", "BEHAVIOR", "Permission_Edit"),
        ("system:permission:delete", "权限删除", "BEHAVIOR", "Permission_Delete"),
        ("system:resource:add", "资源新增", "BEHAVIOR", "Resource_Add"),
        ("system:resource:edit", "资源编辑", "BEHAVIOR", "Resource_Edit"),
        ("system:resource:delete", "资源删除", "BEHAVIOR", "Resource_Delete"),
        ("flow:definition:add", "流程新增", "BEHAVIOR", "Flow_Add"),
        ("flow:definition:edit", "流程编辑", "BEHAVIOR", "Flow_Edit"),
        ("flow:definition:publish", "流程发布", "BEHAVIOR", "Flow_Publish"),
        ("flow:instance:terminate", "强制终止", "BEHAVIOR", "Flow_Terminate"),
        ("flow:task:transfer", "任务转办", "BEHAVIOR", "Flow_Transfer"),
        ("flow:task:urge", "任务催办", "BEHAVIOR", "Flow_Urge"),
    ]
    for code, name, tt, ref in perms:
        db.execute(
            "INSERT INTO sys_permission (code, name, target_type, target_ref, data_scope, status) VALUES (?, ?, ?, ?, 'ALL', 1)",
            (code, name, tt, ref),
            conn,
        )


def _seed_resources(conn):
    resources = [
        (None, "预定管理", "menu-booking", None, "DIRECTORY", None, "Calendar", 10),
        ("menu-booking", "预定申请", "menu-booking-apply", "booking:save", "MENU", "/booking/apply", "CalendarPlus", 11),
        ("menu-booking", "预定查询", "menu-booking-query", "booking:query", "MENU", "/booking/query", "Search", 12),
        ("menu-booking", "会议室管理", "menu-room", "room:query", "MENU", "/room/manage", "DoorOpen", 13),
        ("menu-booking", "会议室预定统计", "menu-room-summary", "booking:report", "MENU", "/report/room-summary", "BarChart3", 14),
        (None, "审批中心", "menu-workbench", None, "DIRECTORY", None, "ClipboardList", 20),
        ("menu-workbench", "我的待办", "menu-workbench-todo", None, "MENU", "/workbench/todo", "Inbox", 21),
        ("menu-workbench", "我的已办", "menu-workbench-done", None, "MENU", "/workbench/done", "CheckSquare", 22),
        ("menu-workbench", "我的申请", "menu-workbench-requested", None, "MENU", "/workbench/requested", "FileText", 23),
        (None, "流程管理", "menu-flow", None, "DIRECTORY", None, "GitBranch", 30),
        ("menu-flow", "流程定义", "menu-flow-definition", "flow:manage", "MENU", "/flow/definitions", "Workflow", 31),
        ("menu-flow", "流程实例", "menu-flow-instance", "flow:manage", "MENU", "/flow/instances", "List", 32),
        ("menu-flow", "任务管理", "menu-flow-task", "flow:manage", "MENU", "/flow/tasks", "ListChecks", 33),
        (None, "系统管理", "menu-system", None, "DIRECTORY", None, "Settings", 40),
        ("menu-system", "用户管理", "menu-system-user", "system:manage", "MENU", "/system/users", "User", 41),
        ("menu-system", "角色管理", "menu-system-role", "system:manage", "MENU", "/system/roles", "Shield", 42),
        ("menu-system", "权限管理", "menu-system-permission", "system:manage", "MENU", "/system/permissions", "Key", 43),
        ("menu-system", "资源管理", "menu-system-resource", "system:manage", "MENU", "/system/resources", "Menu", 44),
    ]
    id_map = {}
    for parent_code, name, code, pc, rtype, path, icon, sort in resources:
        parent_id = id_map.get(parent_code, 0) if parent_code else 0
        rid = db.execute(
            """
            INSERT INTO sys_resource (parent_id, name, code, permission_code, type, path, component, icon, sort_order, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (parent_id, name, code, pc, rtype, path, None, icon, sort),
            conn,
        )[0]
        id_map[code] = rid


def _seed_users(conn):
    users = [
        ("admin", "admin123", "管理员", "admin"),
        ("applicant", "123456", "李预定", "APPLICANT"),
        ("deptmgr", "123456", "王主管", "DEPT_MANAGER"),
        ("adminmgr", "123456", "赵行政", "ADMIN_MANAGER"),
    ]
    for username, pwd, real_name, role_code in users:
        uid = db.execute(
            "INSERT INTO sys_user (username, password, real_name, actor_type, status) VALUES (?, ?, ?, 'HUMAN', 1)",
            (username, hash_password(pwd), real_name),
            conn,
        )[0]
        role = db.query_one("SELECT id FROM sys_role WHERE code = ?", (role_code,), conn)
        db.execute("INSERT INTO sys_user_role (user_id, role_id) VALUES (?, ?)", (uid, role["id"]), conn)


def _seed_role_permissions(conn):
    mapping = {
        "APPLICANT": ["booking:save", "booking:submit", "booking:query", "booking:report", "room:query"],
        "DEPT_MANAGER": ["booking:approve-dept", "booking:query", "booking:report", "room:query"],
        "ADMIN_MANAGER": ["booking:approve-admin", "booking:query", "booking:report", "room:query"],
    }
    for role_code, perm_codes in mapping.items():
        role = db.query_one("SELECT id FROM sys_role WHERE code = ?", (role_code,), conn)
        for pc in perm_codes:
            perm = db.query_one("SELECT id FROM sys_permission WHERE code = ?", (pc,), conn)
            db.execute(
                "INSERT INTO sys_role_permission (role_id, permission_id) VALUES (?, ?)",
                (role["id"], perm["id"]),
                conn,
            )


def _ensure_rooms(conn):
    rooms = [
        ("MEE0001", "大会议室", 30, "3楼301"),
        ("MEE0002", "中会议室", 12, "2楼201"),
        ("MEE0003", "小会议室", 6, "2楼202"),
    ]
    for room_no, room_name, capacity, location in rooms:
        if db.query_one("SELECT id FROM meeting_room WHERE room_no = ?", (room_no,), conn):
            continue
        db.execute(
            "INSERT INTO meeting_room (room_no, room_name, capacity, location, status) VALUES (?, ?, ?, ?, '在用')",
            (room_no, room_name, capacity, location),
            conn,
        )


def _ensure_flow_definition(conn):
    from ontology.registry import registry
    flows = registry.get("flows", {})
    for code, flow in flows.items():
        if db.query_one("SELECT id FROM flow_definition WHERE code = ?", (code,), conn):
            continue
        trigger = flow.get("trigger", {})
        db.execute(
            """
            INSERT INTO flow_definition (code, name, flow_type, trigger_type, trigger_behavior, description, node_graph, version, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1)
            """,
            (
                code, flow.get("name", code), flow.get("flowType", "APPROVAL"),
                trigger.get("triggerType", "MANUAL"), trigger.get("behaviorRef"),
                flow.get("description"), json.dumps(flow.get("nodeGraph", {}), ensure_ascii=False),
            ),
            conn,
        )

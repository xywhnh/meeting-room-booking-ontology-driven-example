#!/usr/bin/env python3
"""七模型一致性门禁（对应 SKILL.md 阶段二）。

检查项：
1. M2 triggerType=USER_ACTION 的行为，须被至少一个 MU 动作引用；
   MU 引用的行为须存在。
2. M7 behaviorRef 与 M2 queryReportRef 严格一对一。
3. M6 的 roleRef / behaviorRef / subFlowRef / ruleRef 引用均须存在；
   SUB_FLOW_CALL 调用图无环。
4. M2 appliedRules / requiredPermissions 引用须存在（M3 / M5）。
5. M1 的 AggregateRootRef 目标聚合须存在；M7 sourceObjects 须存在。

用法：python3 scripts/check_models.py
"""
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("需要 PyYAML：pip install pyyaml")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "code-app" / "models"


def load(name):
    with open(MODELS / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main():
    errors = []
    m1 = load("m1-object-model.yaml")
    m2 = load("m2-behavior-model.yaml")
    m3 = load("m3-rule-model.yaml")
    m5 = load("m5-actor-model.yaml")
    m6 = load("m6-flow-model.yaml")
    m7 = load("m7-report-model.yaml")
    mu = load("mu-ui-model.yaml")
    manifest = json.loads((MODELS / "manifest.json").read_text(encoding="utf-8"))

    aggregates = {a["id"] for a in m1.get("aggregates", [])}
    for agg in m1.get("aggregates", []):
        for attr in agg.get("attributes", []):
            target = attr.get("targetAggregate")
            if target and target not in aggregates:
                errors.append(f"M1 {agg['id']}.{attr['name']} 引用不存在的聚合 {target}")

    behaviors = {b["id"]: b for b in m2.get("behaviors", [])}
    rules = {r["id"] for r in m3.get("rules", [])}
    permissions = {p["permissionId"] for p in m5.get("permissions", [])}
    for b in m2.get("behaviors", []):
        for r in b.get("appliedRules", []):
            if r not in rules:
                errors.append(f"M2 {b['id']} 引用不存在的规则 {r}")
        for p in b.get("requiredPermissions", []):
            if p not in permissions:
                errors.append(f"M2 {b['id']} 引用不存在的权限 {p}")
        if b.get("ownerEntity") not in aggregates:
            errors.append(f"M2 {b['id']} ownerEntity {b.get('ownerEntity')} 不存在")

    for p in m5.get("permissions", []):
        if p.get("targetType") == "BEHAVIOR" and p.get("targetRef") not in behaviors:
            errors.append(f"M5 {p['permissionId']} 引用不存在的行为 {p.get('targetRef')}")

    # MU <-> M2
    mu_refs = set()
    for screen in mu.get("screens", []):
        for action in screen.get("actions", []):
            ref = action.get("behaviorRef")
            mu_refs.add(ref)
            if ref not in behaviors:
                errors.append(f"MU {screen['screenId']} 引用不存在的行为 {ref}")
    for b in m2.get("behaviors", []):
        if b.get("triggerType") == "USER_ACTION" and b["id"] not in mu_refs:
            errors.append(f"M2 {b['id']}（USER_ACTION）未被任何 MU 动作引用")

    # M7 <-> M2 一对一
    report_by_behavior = {}
    for rep in m7.get("query_reports", []):
        ref = rep.get("behaviorRef")
        if ref not in behaviors:
            errors.append(f"M7 {rep['id']} 引用不存在的行为 {ref}")
            continue
        if ref in report_by_behavior:
            errors.append(f"M7 {rep['id']} 与 {report_by_behavior[ref]} 共享行为 {ref}，不是一对一")
        report_by_behavior[ref] = rep["id"]
        for src in rep.get("sourceObjects", []):
            if src.get("objectRef") not in aggregates:
                errors.append(f"M7 {rep['id']} 引用不存在的聚合 {src.get('objectRef')}")
    for b in m2.get("behaviors", []):
        ref = b.get("queryReportRef")
        if ref:
            ids = {r["id"] for r in m7.get("query_reports", [])}
            if ref not in ids:
                errors.append(f"M2 {b['id']} queryReportRef {ref} 不存在")
            elif report_by_behavior.get(b["id"]) != ref:
                errors.append(f"M2 {b['id']} 与 M7 的 queryReportRef 双向不一致")

    # M6 引用 + 子流无环
    flows = {f["id"]: f for f in m6.get("flows", [])}
    roles = {r["roleId"] for r in m5.get("roles", [])}
    edges = {}
    for flow in m6.get("flows", []):
        for r in flow.get("roleRefs", []):
            if r not in roles:
                errors.append(f"M6 {flow['id']} 引用不存在的角色 {r}")
        for obj in flow.get("businessObjectRefs", []):
            if obj not in aggregates:
                errors.append(f"M6 {flow['id']} 引用不存在的聚合 {obj}")
        trig = flow.get("trigger", {})
        if trig.get("behaviorRef") and trig["behaviorRef"] not in behaviors:
            errors.append(f"M6 {flow['id']} trigger 引用不存在的行为 {trig.get('behaviorRef')}")
        nodes = {n["id"]: n for n in flow.get("nodeGraph", {}).get("nodes", [])}
        calls = []
        for node in nodes.values():
            for branch in node.get("branches", []):
                if branch.get("rule_ref") and branch["rule_ref"] not in rules:
                    errors.append(f"M6 {flow['id']} 节点 {node['id']} 引用不存在的规则 {branch['rule_ref']}")
            if node.get("behavior_ref") and node["behavior_ref"] not in behaviors:
                errors.append(f"M6 {flow['id']} 节点 {node['id']} 引用不存在的行为 {node['behavior_ref']}")
            if node.get("sub_flow_ref"):
                if node["sub_flow_ref"] not in flows:
                    errors.append(f"M6 {flow['id']} 节点 {node['id']} 引用不存在的子流 {node['sub_flow_ref']}")
                else:
                    calls.append(node["sub_flow_ref"])
        edges[flow["id"]] = calls
    # DFS 判环
    visiting, visited = set(), set()

    def dfs(node, path):
        if node in visiting:
            errors.append(f"M6 子流调用成环：{' -> '.join(path + [node])}")
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in edges.get(node, []):
            dfs(nxt, path + [node])
        visiting.discard(node)
        visited.add(node)

    for flow_id in flows:
        dfs(flow_id, [])

    # manifest 列出的模型文件须全部存在
    for name in manifest.get("model_files", []):
        if not (MODELS / name).exists():
            errors.append(f"manifest 列出但缺失的模型文件：{name}")

    if errors:
        print(f"一致性检查失败（{len(errors)} 项）：")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("七模型一致性检查通过：M2<->MU、M7<->M2、M6 引用与子流无环、M3/M5 引用均已核对。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

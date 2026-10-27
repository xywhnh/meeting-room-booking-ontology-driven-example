# 会议室预定管理系统：ontology-driven-dev 端到端示例

用 [sharptoolbox/ontology-driven-dev](https://github.com/sharptoolbox/ontology-driven-dev)
的七模型方法，从需求规格、七模型 YAML 到可运行系统，完整走一遍的示例。
业务域是**会议室预定审批**（申请人提交 → 部门主管审批 → 大人数会议行政复核），
与上游的销售合同示例、客户示例均不同，场景由本示例设计。

## 先说清楚的三个点

1. **“本体”在这里指什么**：上游技能的“本体模型”是七模型 YAML 规约
   （M1 对象 / M2 行为 / M3 规则 / M5 主体 / M6 流程 / M7 报表 / MU 界面），
   是 DDD 风格的领域模型驱动应用规约，**不是 OWL/RDF 形式本体**。
   本示例沿用上游的叫法，但在文档里处处注明这一点，不把它冒充为形式化本体。
2. **来源与改动**：上游版本为提交 `49a9eff`（MIT 许可）。本示例复制了上游
   `techbase/` Python 技术底座（code-paas：Flask + SQLite + React/TS）到 `code-app/` 后改造：
   客户示例域全部替换为会议室预定域；新增会议室主数据、预定统计、本地规则助手；
   其余底座代码（系统管理、流程引擎、工作台）保持原样，未改上游仓库本身。
3. **人工确认门禁**：上游 SKILL 要求阶段一八个阶段逐阶段停下等人确认。
   本示例的场景由用户授权助手设计，因此八个阶段的企业专属选择由助手代设，
   集中列在需求文档附录 B，**未冒充为用户已逐项确认**。改作真实项目时须逐项确认。

## 目录结构

```
.
├── 会议室预定需求规格说明书-V9.md   # 阶段一产物（含附录 A 追溯、附录 B 示例设定、附录 C 建模基线）
├── code-app/
│   ├── models/                      # 阶段二产物：七模型 YAML + manifest.json（运行时注册表由此加载）
│   ├── backend/                     # 阶段三产物：Flask + SQLite 后端
│   └── frontend/                    # 阶段三产物：React + TS 前端
└── scripts/
    └── check_models.py              # 阶段二一致性门禁：M2↔MU、M7↔M2、M6 引用与子流无环
```

## 快速启动

```bash
# 后端
cd code-app/backend
pip install -r requirements.txt
python app.py            # http://localhost:5000

# 前端开发（二选一）
cd code-app/frontend
npm install
npm run dev              # http://localhost:5173（代理 /api 到后端）
# 或生产模式：npm run build 后访问 http://localhost:5000（由 Flask 托管）
```

默认账号（仅示例，生产前必须修改）：`admin / admin123`（管理员）、
`applicant / 123456`（申请人）、`deptmgr / 123456`（部门主管）、
`adminmgr / 123456`（行政经理）。

## 验证（本示例实际跑通过的）

```bash
python scripts/check_models.py     # 七模型一致性门禁通过
cd code-app/backend
python smoke_test.py               # 端到端自测通过（见 code-app/README.md 第 7 节清单）
```

自测覆盖：时间顺序 / 容量 / 重叠三条规则拦截；小规模（< 20 人）直接通过；
大规模（≥ 20 人）经网关转行政经理复核；驳回；撤回；会议室预定统计；本地助手；
流程定义已发布。自测用独立临时数据库，不触碰 `data/app.db`。

手动走一遍（小规模）：`applicant` 登录 → 预定申请 → 选大会议室、填明天 09:00–10:00、
8 人 → 暂存 → 提交；`deptmgr` 登录 → 我的待办 → 通过 → 预定变为已通过。
手动走一遍（大规模）：同上但填 25 人，`deptmgr` 通过后预定变为“待行政经理审批”，
再用 `adminmgr` 通过才变为已通过。

## 设计要点

- **网关是真的在跑**：M6 网关分支用 M3 规则 `RULE-BOOKING-NEEDS-ADMIN`
  （`participants >= 20`）求值，提交时把 `participants` 放进流程实例变量，
  流程引擎据此决定是否生成行政复核任务；不是前端写死的分支。
- **规则不是只写在文档里**：R-01～R-04 在暂存与提交时都由后端校验，
  违反时返回中文业务提示（前端 toast 显示）；R-03 的重叠查询只看待审批 / 已通过，
  草稿与已驳回不占时段。
- **模型是唯一语义来源**：表、接口、菜单、权限、流程、报表均可回溯到某个模型元素，
  追溯表见需求文档附录 A；`scripts/check_models.py` 把其中可机检的部分自动化了。
- **右侧助手是本地规则版**：不调用外部大模型，只做只读查询与导航，因此开箱即跑、
  可被自测覆盖；与上游 LLM + SSE 实现的区别与替换方法见 `code-app/README.md` 第 8 节。

## 不在本示例范围内的

- Go 版底座（`go-techbase/`）未使用，本示例选 Python 版。
- 生产部署：WSGI 部署、JWT 密钥轮换、默认账号修改、备份均未做；`app.py` 的 Flask
  开发服务器仅用于演示。
- 上游 SKILL 阶段一的八轮人工确认（见上文第 3 点）。

## 许可

上游 ontology-driven-dev 与 code-paas 底座均为 MIT 许可；本示例的自有部分（会议室预定域
的模型、服务、页面、文档）同样以 MIT 许可发布。`code-app/backend/config.yaml` 里的
JWT 密钥与默认账号仅为示例值，切勿用于生产。

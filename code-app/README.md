# 会议室预定管理系统（code-app）

用 [sharptoolbox/ontology-driven-dev](https://github.com/sharptoolbox/ontology-driven-dev)
的七模型方法与 `code-paas` Python 技术底座，从需求规格、七模型 YAML 到可运行系统
的端到端示例。业务域为**会议室预定审批**，与上游的销售合同示例、客户示例均不同。

> 术语说明：这里的“本体模型”指该技能的七模型 YAML 规约（对象 / 行为 / 规则 /
> 主体 / 流程 / 报表 / UI），不是 OWL/RDF 形式本体。详见项目根 README 的说明。

## 1. 功能范围

- **预定申请**：会议室下拉选择（跳选主数据）、日期、时段、主题、人数；暂存 / 提交双按钮
- **预定审批**：部门主管先审；参会人数 ≥ 20 人时经网关转行政经理复核，否则直接通过；驳回、退回、撤回
- **预定查询**：按预定编号、会议室、日期、状态查询，分页
- **会议室管理**：在用会议室列表与新增（种子含大 / 中 / 小会议室各 1 间）
- **报表中心**：会议室预定统计（按会议室汇总单数与已通过单数，可按日期范围过滤）
- **审批中心**：我的待办、我的已办、我的申请
- **流程管理 / 系统管理**：沿用 code-paas 底座（流程定义、实例、任务；用户 / 角色 / 权限 / 资源）
- **右侧助手**：本地规则助手（见第 8 节），无需配置大模型 Key

## 2. 技术栈

| 层 | 选型 |
|---|---|
| 数据库 | SQLite 3（WAL） |
| 后端 | Python 3.10+ + Flask（单体分层，`sqlite3` 直连，无 ORM） |
| 认证 | PyJWT + werkzeug |
| 规则 | simpleeval（M3 网关规则求值；容量 / 重叠等需查库规则由服务层用同一规则 ID 落实） |
| 前端 | React 18 + TypeScript + Vite + Vanilla CSS |
| 流程设计器 | react-flow |

## 3. 快速启动

### 3.1 后端

```bash
cd code-app/backend
pip install -r requirements.txt
python app.py            # http://localhost:5000
```

首次启动自动建库并写入种子（角色 / 权限 / 资源 / 用户 / 会议室 / 流程定义）。

### 3.2 前端

```bash
cd code-app/frontend
npm install
npm run dev              # 开发模式 http://localhost:5173（代理 /api）
# 或
npm run build            # 构建后由 Flask 托管，访问 http://localhost:5000
```

## 4. 默认账号（仅示例，生产部署前必须修改）

| 账号 | 密码 | 角色 | 说明 |
|---|---|---|---|
| `admin` | `admin123` | 系统管理员 | 全部功能 |
| `applicant` | `123456` | 预定申请人 | 预定申请 / 查询 / 统计 |
| `deptmgr` | `123456` | 部门主管 | 预定审批第一节点 |
| `adminmgr` | `123456` | 行政经理 | 大型会议复核节点 |

## 5. 典型业务流程

1. `applicant` 登录 → 预定管理 → 预定申请，选会议室、填日期时段与人数 → 暂存 → 提交；
2. `deptmgr` 登录 → 审批中心 → 我的待办 → 处理（通过 / 驳回 / 退回）；
   - 参会人数 < 20 人：通过后直接变为已通过；
   - 参会人数 ≥ 20 人：通过后转 `adminmgr` 行政经理复核；
3. `applicant` 登录 → 我的申请 查看进度；预定查询 查看已通过的预定；
   第一节点未处理前可在我的申请里撤回（回到草稿）；
4. 报表中心 → 会议室预定统计 查看各会议室单数与已通过单数。

## 6. 本体模型映射

- 对象模型 M1 → `backend/schema.sql` 业务表（预定单含 5 默认字段，逻辑删除 `flag=0`）
- 行为模型 M2 → `backend/services/booking_service.py`、`room_service.py`、`report_service.py` + `backend/api/*.py`
- 规则模型 M3 → `backend/services/booking_service.py`（规则 ID 与 M3 一致）+ 流程网关规则求值
- 主体模型 M5 → 种子角色 / 权限（`backend/seed.py`，含 M5 permissionId 到后端权限 code 的映射注释）
- 流程模型 M6 → `code-app/models/m6-flow-model.yaml` nodeGraph → `flow_definition`（种子写入，状态为已发布）
- 查询报表 M7 → `backend/services/report_service.py` + 预定查询
- UI 模型 MU → 菜单（`sys_resource`）+ 前端页面

编号约定：对象英文别名前 3 位大写 + 4 位流水号（预定单 `BOO0001`、会议室 `MEE0001`），
由 `backend/utils/codegen.py` 在事务内生成。

## 7. 自测

```bash
cd code-app/backend
python smoke_test.py
```

覆盖：时间顺序 / 容量 / 重叠三条规则拦截；小规模直接通过；大规模经网关转行政复核；
驳回；撤回；会议室预定统计；本地助手；流程定义已发布。
自测使用独立临时数据库，不触碰 `data/app.db`。

模型一致性门禁：

```bash
python scripts/check_models.py
```

核对 M2↔MU、M7↔M2 一对一、M6 引用与子流无环、M3 / M5 引用。

## 8. 右侧助手说明（与上游的区别，务必读）

上游 `code-app-example` 的 AI 对话是 LLM + SSE 实现，需要在界面配置 OpenAI 兼容服务。
本示例的右侧助手是**本地规则助手**（`backend/services/assistant_service.py` + `POST /api/ai/chat`），
不调用任何外部大模型，只做只读查询（会议室、按编号查预定、预定统计、待审批计数）与页面导航。
这样做的好处是示例开箱即跑、且可被 `smoke_test.py` 覆盖；代价是它回答不了开放式业务问题。
如需 LLM 对话，按上游 `backend/ai/` 的结构替换本模块即可，接口契约保持不变。

## 9. 目录结构

```
code-app/
├── models/                  # 会议室预定域七模型 YAML + manifest（阶段二产物，运行时注册表由此加载）
├── backend/
│   ├── app.py  schema.sql  seed.py  db.py  config.yaml
│   ├── ontology/registry.py # 运行时语义注册表
│   ├── engine/flow_engine.py # 工作流引擎（网关规则求值 / 审批结果路由）
│   ├── services/            # 预定 / 会议室 / 报表 / 本地助手 / 工作台 / 领域规则
│   ├── api/                 # REST 接口 + 本地助手
│   └── utils/               # 编号生成、JWT
└── frontend/src/            # React 页面 + 右侧助手组件
```

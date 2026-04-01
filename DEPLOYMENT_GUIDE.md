# SAS-TradingGraph 项目部署指南

## ✅ API Key 配置完成

你提供的 DeepSeek API Key 已存储到 `.env` 文件（已加入 `.gitignore` 不会推送到 GitHub）：

```bash
DEEPSEEK_API_KEY=sk-34391d7cce224c278a21a5bf15c3f7b9
```

---

## 📦 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/terlivy/SAS-TradingGraph.git
cd SAS-TradingGraph
```

### 2. 安装依赖

```bash
# 推荐用 Python 3.10+ (因为 langchain 在 Python 3.14 有兼容性警告)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装核心包
pip install -r requirements.txt

# 如果是第一次，也可以直接安装
pip install langgraph langchain-deepseek langchain-openai python-dotenv tavily-python
```

### 3. 配置环境变量

`.env` 文件已自动创建。确保包含：

```bash
DEEPSEEK_API_KEY=sk-34391d7cce224c278a21a5bf15c3f7b9
TAVILY_API_KEY=tvly-xxxx  # 可选，用于市场数据 API
```

### 4. 运行示例

#### 方式 A：快速测试（无 LLM 调用）

```bash
python -c "
from sas_gates import sas_gate_router, SAS_AgentState

# 测试 SAS Gate 路由
test_state = {
    'messages': [],
    'stock_ticker': 'NVDA',
    'analyst_results': {},
    'bull_case': 'Test bullish case',
    'bear_case': 'Test bearish case',
    'debate_history': [],
    'risk_assessment': {'risk_level': 'medium'},
    'rollback_count': 0,
    'current_phase': 'implementation',
    'execution_trace': [],
    'approval_status': 'auto_approved',
}

result = sas_gate_router(test_state)
print(f'✓ SAS Gate 路由结果: {result}')
"
```

#### 方式 B：完整分析流程（需要 API Key）

```bash
# 单个股票分析
python run.py --ticker NVDA --date 2026-04-01 --analysts market,news --debug

# 看多/看空辩论
python run.py --ticker TSLA --date 2026-04-01 --analysts market,social,news --debate --debug

# 风险评估模式
python run.py --ticker SPY --date 2026-04-01 --risk-mode high --debug
```

---

## 🏗️ 项目结构

```
SAS-TradingGraph/
├── sas_trading_graph.py      # 融合主类（SAS v1.5 + TradingAgents）
├── sas_setup.py              # Graph 构造器（LangGraph DAG）
├── sas_gates.py              # SAS 门控引擎（路由 + 审批）
├── sas_states.py             # SAS_AgentState 状态定义
├── sas_conditional_logic.py   # 条件逻辑（继承 TA）
├── run.py                    # CLI 快速启动脚本
├── test_sas.py               # 测试套件
├── requirements.txt          # 依赖
├── .env.example              # 环境变量模板
├── .env                      # 实际环境变量（已配置）
├── .gitignore                # Git 忽略规则
├── README.md                 # 项目说明
└── tradingagents/            # TradingAgents v0.2.3 完整源码
    ├── agents/
    ├── graph/
    ├── llm_clients/
    └── ...
```

---

## 🔧 SAS v1.5 融合特性

### 核心：六阶段门控

```
1️⃣ 接收任务 (L1_SC_Planner)
    ↓
2️⃣ 制定计划 (SAS_Planner)
    ↓
3️⃣ 方案设计 (分析师小组)
    ↓
4️⃣ 实施工作 (Trader + Debate)
    ↓
5️⃣ 质量检查 (SAS_Gate)
    ├→ 低风险 → 6️⃣ 交付成果 (Portfolio Manager)
    ├→ 中风险 → 需人工审批
    └→ 高风险 / 3次回退 → 直接升级
    ↓
6️⃣ 复盘归档 (成绩单 + 执行轨迹)
```

### SAS Gate 自动审批三级路由

| 风险等级 | 决策 | 说明 |
|---------|------|------|
| **低** | ✅ 自动通过 | `deliver` → Portfolio Manager |
| **中** | ⏳ 人工审批 | `human_review` → END (等待用户决策) |
| **高** | ↩️ 自动回退 | `rollback` → 重新规划（最多3次） |
| **超过3次回退** | 🚀 强制升级 | `human_review` → 必须人工审批 |

### 执行铁律

```
1. 不擅自做主 → SAS Gate 把控审批
2. 不隐瞒问题 → 完整的 execution_trace
3. 不重复犯错 → rollback_count 限制
4. 不浪费资源 → 复杂度分级 L1/L2/L3
```

---

## 📊 运行日志示例

```bash
$ python run.py --ticker NVDA --date 2026-04-01 --debug

=== SAS-TradingGraph 初始化 ===
✓ Graph 创建成功
✓ LLM 客户端: DeepSeek Chat (sk-3439...)

=== 第1阶段：接收任务 ===
🎯 任务: 分析 NVDA (2026-04-01)
📊 选择分析师: [market, news]
⏱️ 复杂度: L2 (中等)

=== 第2阶段：制定计划 ===
SC_PLANNER: "根据复杂度 L2，将采用标准流程...
需要完成以下工作:
  1. 市场情绪分析
  2. 新闻面爬取
  3. 看多/看空辩论
  4. 风险评估"

=== 第3阶段：方案设计 ===
MARKET_ANALYST: "截至 2026-04-01，NVDA...
- 技术形态: 上升趋势
- 成交量: 正常偏低
- 评分: 7/10"

NEWS_ANALYST: "最近新闻动向:
- AI 芯片需求持续...
- 竞争压力来自...
- 评分: 6/10"

=== 第4阶段：实施工作 ===
BULL_RESEARCHER: "看多理由: AI 算力需求..."
BEAR_RESEARCHER: "看空理由: PE 估值过高..."

=== 第5阶段：质量检查 (SAS_Gate) ===
🔍 风险评估:
  - 看多得分: 7/10
  - 看空得分: 6/10
  - 综合风险: medium
  - 审批: ⏳ 需人工确认

📋 成绩单:
  ├─ Market Analyst: ✅ 完成
  ├─ News Analyst: ✅ 完成
  ├─ Bull Case: 看多得分 7/10
  ├─ Bear Case: 看空得分 6/10
  └─ Risk Level: medium (需人工审批)

⚠️ 等待用户决策: approve / reject / rollback
```

---

## 🧪 测试套件

已提供 `test_sas.py`，包含以下测试：

```bash
# 运行所有测试
python test_sas.py

# 输出示例
=== SAS_TradingAgentsGraph 初始化测试 ===
Graph 创建成功!

=== SAS Gate 路由器测试 ===
中风险测试 -> 结果: human_review
超过3次回退 -> 结果: human_review
高风险 -> 结果: rollback
低风险 -> 结果: deliver

=== SAS 六阶段状态测试 ===
  phase_1_receive_task: 接收任务 - 确认需求、评估复杂度
  phase_2_plan: 制定计划 - 详细步骤、风险识别
  phase_3_design: 方案设计 - 方案细化、可行性论证
  phase_4_implementation: 实施工作 - 按计划执行、记录决策
  phase_5_qc: 质量检查 - 自检、验证、复核
  phase_6_delivery_and_archive: 交付成果 - 完整交付物、复盘归档

=== 测试完成! ===
```

---

## 📚 核心 API

### SAS_TradingAgentsGraph 类

```python
from sas_trading_graph import SAS_TradingAgentsGraph

# 初始化
graph = SAS_TradingAgentsGraph()

# 执行分析
result = graph.analyze(
    ticker="NVDA",
    date="2026-04-01",
    analysts=["market", "news", "fundamentals"],
    complexity_level="L2",
    risk_tolerance="medium"
)

# 查看成绩单
print(result['scorecard'])
```

### SAS Gate 路由

```python
from sas_gates import sas_gate_router, SAS_AgentState

state: SAS_AgentState = {...}
decision = sas_gate_router(state)

# 返回值:
# - "deliver" → 交付给 Portfolio Manager
# - "rollback" → 回到规划阶段
# - "human_review" → 升级到用户审批
```

---

## 🚀 部署生产

### Docker 化（可选）

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 8000
CMD ["python", "run.py", "--serve"]
```

```bash
docker build -t sas-tradinggraph .
docker run -e DEEPSEEK_API_KEY=sk-xxxxx sas-tradinggraph
```

---

## ⚠️ 常见问题

### Q: DeepSeek API 费用?
**A:** DeepSeek Chat 模型成本极低（约 0.14¥ per 1M tokens），比 GPT-4 便宜 50+ 倍。此项目日常测试成本 < 1¥。

### Q: 能否离线使用?
**A:** 不能，需要 API 调用。但可以写 Mock LLM 进行本地测试：
```python
from sas_gates import create_sas_planner_node

# 使用 Mock LLM
mock_llm = lambda x: "mock_response"
planner = create_sas_planner_node(mock_llm)
```

### Q: 支持其他 LLM 吗?
**A:** 支持。修改 `sas_trading_graph.py` 的 `create_llm_client()` 调用：
```python
# 改为 OpenAI
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
```

### Q: 能否实时交易?
**A:** 此项目仅用于**分析和研究**。实时交易需额外：
1. 实时行情接口（券商 API）
2. 风控系统
3. 资金管理模块
4. 合规审计

---

## 📞 支持和反馈

- **GitHub Issues**: https://github.com/terlivy/SAS-TradingGraph/issues
- **相关项目**:
  - SAS 准则: https://github.com/terlivy/SAS
  - TradingAgents: https://github.com/TauricResearch/TradingAgents

---

## 📄 许可证

Apache License 2.0

---

**更新于**: 2026-04-01  
**SAS 版本**: v1.5.0 CEO 模式  
**TradingAgents 版本**: v0.2.3  
**融合版本**: v1.0

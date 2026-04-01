# SAS-TradingGraph

> **SAS v1.5 CEO 模式** × **TradingAgents LangGraph 多智能体** = 严格治理 × 强执行力的 AI 投研团队操作系统

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg?style=flat-square)](https://opensource.org/license/apache-2-0)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg?style=flat-square)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg?style=flat-square)](https://langchain-ai.github.io/langgraph/)

---

## 是什么

**SAS-TradingGraph** 是 [Snoopy Agent Smart（SAS）v1.5 工作准则](https://github.com/terlivy/SAS) 与 [TradingAgents（45k ⭐）](https://github.com/TauricResearch/TradingAgents) 的深度融合框架。

在 TradingAgents 强大的多分析师并行 + 辩证辩论 + 风险闭环执行能力之上，叠加了 SAS v1.5 的：

- **CEO 模式四层角色分工**（L0 用户 → L1 主脑 → L2 Leader → L3 Worker）
- **六阶段门控流水线**（接收任务 → 制定计划 → 执行工作 → 质量检查 → 交付成果 → 归档记忆）
- **四铁律执行规范**（不擅自做主、不隐瞒问题、不重复犯错、不浪费资源）
- **自动审批引擎**（低风险 auto_pass，高风险强制人工）
- **任务级成绩单**（每个 Agent 的执行记录、风险评分、归档可查）

**定位**：全球第一个多 Agent 协作规范化的量化投研框架。

---

## 核心架构

### 执行流程

```
START
  → L1_SC_Planner（接收任务 + 制定计划 + 复杂度判断 L1/L2/L3）
  → [用户审批 Gate] — L1 自动通过，L2/L3 需确认
  → 并行分析师团队（市场 + 情绪 + 新闻 + 基本面）
  → Bull/Bear 研究员辩论（看多 vs 看空）
  → Research Manager（综合研判）
  → Trader（生成交易计划）
  → 风险辩论团队（激进/中性/保守）
  → SAS_Gate（质量检查 + 风险评分）
  │    ├─ 低风险（<0.30）→ 自动归档交付
  │    ├─ 中风险（0.30–0.70）→ 回退到 Planner（≤3次）
  │    └─ 高风险（≥0.70）→ 终止
  → sas_archive（归档 + 成绩单）
  → END
```

### 关键差异：SAS 治理 vs 纯 TradingAgents

| 维度 | 纯 TradingAgents | SAS-TradingGraph |
|------|----------------|----------------|
| 用户参与 | 无（全自动） | 仅 2 个决策点 |
| 执行规范 | 隐式（prompt 里散落） | **显式**：六阶段门控 + 铁律 |
| 错误处理 | 辩论失败即终止 | **回退机制**：最多 3 轮回退重做 |
| 风险控制 | 风险辩论最终决定 | **双重保障**：辩论 + SAS 评分 Gate |
| 决策追溯 | 仅最终报告 | **完整成绩单**：每步 Agent 执行记录 |

---

## 快速开始

### 1. 安装

```bash
git clone https://github.com/terlivy/SAS-TradingGraph.git
cd SAS-TradingGraph
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

**最小配置（DeepSeek）**：
```bash
export LLM_PROVIDER=deepseek
export DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 3. 运行

```bash
python run.py --ticker NVDA --date 2026-04-01
python run.py --ticker AAPL --date 2026-04-01 --analysts market,news
python run.py --ticker TSLA --date 2026-04-01 --no-auto-approve
```

### 4. Python API

```python
from sas_trading_graph import SAS_TradingAgentsGraph

config = {
    "llm_provider": "deepseek",
    "api_key": "sk-xxxx",
    "deep_think_llm": "deepseek-chat",
    "quick_think_llm": "deepseek-chat",
    "sas_llm": "qwen-plus",
}

graph = SAS_TradingAgentsGraph(debug=True, config=config)
state, decision = graph.propagate("NVDA", "2026-04-01")

print("SAS 阶段:", state["current_stage"])
print("风险评分:", state["risk_score"])
print("审批状态:", state["sas_approval_status"])
print("最终决策:", decision)
```

---

## 文件结构

```
SAS-TradingGraph/
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example
├── run.py                         # 快速运行脚本
│
├── sas_trading_graph.py           # 【融合主类】SAS_TradingAgentsGraph
├── sas_setup.py                   # 【融合核心】SAS_GraphSetup
├── sas_states.py                  # 【融合核心】SAS_AgentState
├── sas_gates.py                   # 【融合核心】SAS 门控函数
├── sas_conditional_logic.py       # 【融合核心】SAS 条件逻辑
│
└── tradingagents/                 # TradingAgents 源码（v0.2.3）
    ├── agents/
    ├── dataflows/
    ├── llm_clients/
    └── graph/
```

---

## 相关项目

| 项目 | GitHub | 说明 |
|------|--------|------|
| **SAS 工作准则** | [terlivy/SAS](https://github.com/terlivy/SAS) | SAS v1.5 完整方法论文档 |
| **TradingAgents** | [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | 多智能体金融交易框架（45k ⭐） |
| **SAS-script** | [terlivy/SAS-script](https://github.com/terlivy/SAS-script) | SAS 自动化脚本工具集 |

---

## 免责声明

本项目仅用于**研究与教育目的**。AI 生成的投研分析**不构成投资建议**。使用者需自行承担投资风险。

---

*SAS-TradingGraph — 让 AI 投研有章可循，有据可查。*

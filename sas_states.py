"""
sas_states.py
SAS v1.5 + TradingAgents 融合 — SAS 扩展状态

定义 SAS_AgentState：继承 TradingAgents AgentState 的全部字段，
追加 SAS v1.5 CEO 模式专用字段。

为什么不用继承：
  Python TypedDict 不支持真正的多重继承（AgentState → MessagesState → TypedDict）。
  因此 SAS_AgentState 是独立的 TypedDict，但字段完全兼容 AgentState，
  运行时完全等效。LangGraph 只检查运行时字段存在性，不检查类型注解。
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict

# TradingAgents AgentState 的所有字段（从 MessagesState 继承）
from tradingagents.agents.utils.agent_states import AgentState


class SAS_AgentState(TypedDict, total=False):
    """SAS v1.5 扩展状态 — 完全兼容 AgentState 所有字段"""

    # === AgentState 原生字段 ===
    company_of_interest: Annotated[str, "正在交易分析的公司"]
    trade_date: Annotated[str, "交易日期"]
    sender: Annotated[str, "发送消息的 Agent"]
    market_report: Annotated[str, "市场分析师报告"]
    sentiment_report: Annotated[str, "社交媒体分析师报告"]
    news_report: Annotated[str, "新闻分析师报告"]
    fundamentals_report: Annotated[str, "基本面分析师报告"]
    investment_debate_state: AgentState.__annotations__.get("investment_debate_state")  # type: ignore
    investment_plan: Annotated[str, "分析师生成的投资计划"]
    trader_investment_plan: Annotated[str, "交易员生成的投资计划"]
    risk_debate_state: AgentState.__annotations__.get("risk_debate_state")  # type: ignore
    final_trade_decision: Annotated[str, "风险分析师的最终决策"]

    # === SAS v1.5 CEO 模式新增字段 ===
    current_stage: Annotated[
        str,
        "SAS 六阶段当前阶段: 接收任务 | 制定计划 | 执行工作 | 质量检查 | 交付成果 | 归档记忆",
    ]
    complexity_level: Annotated[
        str,
        "任务复杂度: L1(简单/快速) | L2(中等/标准) | L3(复杂/完整)",
    ]
    sas_approval_status: Annotated[
        str,
        "SAS 审批状态: pending | auto_pass | human_review | rejected",
    ]
    rollback_count: Annotated[
        int,
        "回退次数（≤3，超过则强制 human_review）",
    ]
    plan_summary: Annotated[
        str,
        "L1 SC Planner 输出的任务计划摘要（供 L0 用户审批）",
    ]
    risk_score: Annotated[
        float,
        "SAS Gate 计算的风险评分（0.0–1.0），用于自动审批判断",
    ]
    leader_autonomy: Annotated[
        bool,
        "Leader 是否在 L2 层获得自治权限（绕过 L0 审批）",
    ]
    task_scorecard: Annotated[
        dict,
        "任务级成绩单（各 Agent 执行记录、状态、原因分析）",
    ]
    execution_log: Annotated[
        list,
        "执行日志（每步关键决策的记录）",
    ]


# ── SAS 六阶段常量 ──────────────────────────────────────────────────────────
SAS_STAGES = [
    "接收任务",
    "制定计划",
    "执行工作",
    "质量检查",
    "交付成果",
    "归档记忆",
]

COMPLEXITY_LEVELS = ["L1", "L2", "L3"]

APPROVAL_STATUS = ["pending", "auto_pass", "human_review", "rejected"]

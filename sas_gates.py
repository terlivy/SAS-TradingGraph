"""
sas_gates.py
SAS v1.5 + TradingAgents 融合 — SAS 门控引擎

包含两类函数：
  1. 路由函数（router functions）— 传给 add_conditional_edges 的第二个参数
  2. 节点函数（node functions）— 传给 add_node 的实际执行函数

路由函数签名：(state: SAS_AgentState) -> str
节点函数签名：(state: SAS_AgentState) -> dict[str, Any]
"""

from typing import Any, Literal

from sas_states import SAS_AgentState


# ════════════════════════════════════════════════════════════════════════════
# 路由函数（Router Functions）— add_conditional_edges 的第二个参数
# ════════════════════════════════════════════════════════════════════════════

MAX_ROLLBACK = 3
RISK_THRESHOLD_HIGH = 0.70
RISK_THRESHOLD_LOW = 0.30


def sas_stage_router(state: SAS_AgentState) -> Literal[
    "plan_approval",
    "analyst_team",
    "trader",
    "sas_gate",
    "portfolio_manager",
    "archive",
    "end",
]:
    """SAS 六阶段主路由 — 根据 current_stage 决定下一步节点。"""
    stage = state.get("current_stage", "接收任务")

    if stage == "接收任务":
        return "plan_approval"
    elif stage == "制定计划":
        return "analyst_team"
    elif stage == "执行工作":
        return "trader"
    elif stage == "质量检查":
        return "sas_gate"
    elif stage == "交付成果":
        return "portfolio_manager"
    elif stage == "归档记忆":
        return "archive"
    else:
        return "end"


def sas_plan_approval_router(
    state: SAS_AgentState,
) -> Literal["analyst_team", "end"]:
    """
    L0 用户 Gate — 计划审批。
    - leader_autonomy=True（简单任务 L1）：自动通过
    - 其他：pending 等待外部确认（或 auto_pass 强制通过）
    """
    if state.get("leader_autonomy", False):
        return "analyst_team"
    approval = state.get("sas_approval_status", "pending")
    if approval in ("auto_pass", "human_review"):
        return "analyst_team"
    return "end"


def sas_gate_router(state: SAS_AgentState) -> Literal[
    "sas_archive",
    "plan_approval",
    "end",
]:
    """
    SAS 质量检查 Gate — 自动审批引擎。

    决策逻辑（优先级从高到低）：
      1. rollback_count >= 3        → end（超过回退上限，终止）
      2. risk_score < 0.30          → sas_archive（低风险，auto_pass）
      3. risk_score >= 0.70         → end（高风险，强制人工/终止）
      4. 0.30 <= risk_score < 0.70  → plan_approval（中等风险，回退重做）
    """
    rollback = state.get("rollback_count", 0)
    risk = state.get("risk_score", 0.5)

    if rollback >= MAX_ROLLBACK:
        return "end"
    if risk < RISK_THRESHOLD_LOW:
        return "sas_archive"
    if risk >= RISK_THRESHOLD_HIGH:
        return "end"
    return "plan_approval"


# ════════════════════════════════════════════════════════════════════════════
# 节点函数（Node Functions）— 传给 add_node 的执行函数
# ════════════════════════════════════════════════════════════════════════════

def create_sas_planner_node(llm):
    """
    L1 SC Planner 节点（接收任务 → 制定计划 → 复杂度判断）

    职责：
      1. 解析用户输入（股票代码 + 日期）
      2. 判断任务复杂度（L1/L2/L3）
      3. 生成 plan_summary 供 L0 审批
      4. 设置 leader_autonomy 标志
      5. 初始化 execution_log 和 task_scorecard
    """

    def sas_planner_node(state: SAS_AgentState) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        import re

        company = state.get("company_of_interest", "")
        trade_date = state.get("trade_date", "")
        messages = state.get("messages", [])
        user_request = messages[-1].content if messages else ""

        system_prompt = (
            "你是一个严格遵循 SAS v1.5 工作准则的 L1 主脑（SC）。\n"
            "【你的职责】接收任务 → 制定计划 → 判断复杂度（L1/L2/L3）。\n\n"
            "【执行铁律】\n"
            "  1. 不擅自做主 — 超出权限时必须上报\n"
            "  2. 不隐瞒问题 — 风险必须立即预警\n"
            "  3. 不重复犯错 — 历史错误库是必查项\n"
            "  4. 不浪费资源 — 选最合适的模型，不盲目堆砌\n\n"
            "【复杂度分级】\n"
            "  L1（简单）：单一技术指标分析、日内热点追踪、新闻快评\n"
            "  L2（中等）：多维度分析师报告（市场+情绪+新闻+基本面）、标准辩论流程\n"
            "  L3（复杂）：跨市场比较、期权/衍生品分析、合规审查、全流程多重审批\n\n"
            f"【当前任务】股票：{company}，日期：{trade_date}\n"
            f"【用户请求】{user_request}\n\n"
            "请分析并输出（JSON格式）：\n"
            "{\n"
            '  "complexity_level": "L1/L2/L3 及理由",\n'
            '  "plan_summary": "计划摘要（分析维度、所需Agent、预期输出）",\n'
            '  "leader_autonomy": true/false,\n'
            '  "current_stage": "制定计划"\n'
            "}"
        )

        response = llm.invoke([SystemMessage(content=system_prompt)])
        content = response.content if hasattr(response, "content") else str(response)

        result: dict[str, Any] = {
            "current_stage": "制定计划",
            "sas_approval_status": "pending",
            "rollback_count": 0,
            "risk_score": 0.0,
            "task_scorecard": {},
            "execution_log": [],
        }

        m = re.search(r'complexity_level["\s:]+([LL]?[123])', content, re.I)
        if m:
            result["complexity_level"] = f"L{m.group(1)[-1]}"
        else:
            result["complexity_level"] = "L2"

        if "L1" in result["complexity_level"]:
            result["leader_autonomy"] = True
            result["sas_approval_status"] = "auto_pass"
        else:
            result["leader_autonomy"] = False

        plan_m = re.search(r'plan_summary["\s:]+(.+?)(?=\n\n|\Z)', content, re.DOTALL)
        result["plan_summary"] = plan_m.group(1).strip()[:500] if plan_m else content[:500]

        result["execution_log"] = [
            {
                "stage": "接收任务",
                "agent": "L1_SC_Planner",
                "action": "任务解析 + 复杂度判断",
                "result": result["complexity_level"],
            }
        ]

        return result

    return sas_planner_node


def create_sas_gate_node(llm):
    """
    SAS 质量检查 Gate 节点 — 计算风险评分，决定路由。
    """

    def sas_gate_node(state: SAS_AgentState) -> dict[str, Any]:
        from langchain_core.messages import SystemMessage
        import re

        reports = []
        for key in ["market_report", "sentiment_report", "news_report", "fundamentals_report"]:
            if state.get(key):
                reports.append(state[key][:1000])

        trader_plan = state.get("trader_investment_plan", "")[:1000]
        risk_debate_state = state.get("risk_debate_state", {})
        if isinstance(risk_debate_state, dict):
            risk_debate = risk_debate_state.get("judge_decision", "")[:500]
        else:
            risk_debate = ""

        context = "\n\n".join(reports) + f"\n\n交易计划：{trader_plan}\n\n风控意见：{risk_debate}"

        system_prompt = (
            "你是一个严格遵循 SAS v1.5 工作准则的风险评估专家。\n"
            "【执行铁律：不隐瞒问题 — 发现风险立即预警，不等到爆发】\n\n"
            "请分析以下投研材料，给出一个 0.0–1.0 的风险评分：\n"
            "  0.0–0.30 = 低风险（可以 auto_pass）\n"
            "  0.31–0.69 = 中等风险（建议回退优化）\n"
            "  0.70–1.00 = 高风险（需要人工审批或终止）\n\n"
            f"材料：\n{context[:3000]}\n\n"
            '请输出 JSON：{"risk_score": 0.xx, "reason": "不超过100字的原因"}'
        )

        response = llm.invoke([SystemMessage(content=system_prompt)])
        content = response.content if hasattr(response, "content") else str(response)

        risk_score = 0.5
        try:
            m = re.search(r'risk_score["\s:]+([0-9.]+)', content)
            if m:
                risk_score = float(m.group(1))
        except Exception:
            pass

        rollback = state.get("rollback_count", 0)
        if rollback >= MAX_ROLLBACK:
            approval = "rejected"
        elif risk_score < RISK_THRESHOLD_LOW:
            approval = "auto_pass"
        elif risk_score >= RISK_THRESHOLD_HIGH:
            approval = "human_review"
        else:
            approval = "pending"

        scorecard = dict(state.get("task_scorecard", {}))
        scorecard["SAS_Gate"] = {"risk_score": risk_score, "approval": approval}

        return {
            "risk_score": risk_score,
            "sas_approval_status": approval,
            "rollback_count": rollback,
            "task_scorecard": scorecard,
        }

    return sas_gate_node


def sas_archive_node(state: SAS_AgentState) -> dict[str, Any]:
    """
    SAS 归档记忆节点 — 写入任务成绩单和执行日志。
    """
    scorecard = dict(state.get("task_scorecard", {}))
    execution_log = list(state.get("execution_log", []))
    execution_log.append({
        "stage": "归档记忆",
        "agent": "SAS_System",
        "action": "任务归档",
        "result": "完成",
        "scorecard_summary": {k: v.get("approval", v.get("result", "")) for k, v in scorecard.items()},
    })
    return {
        "current_stage": "归档记忆",
        "task_scorecard": scorecard,
        "execution_log": execution_log,
    }

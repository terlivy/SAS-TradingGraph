"""
sas_conditional_logic.py
SAS v1.5 + TradingAgents 融合 — 扩展条件逻辑

继承 TradingAgents ConditionalLogic 的所有路由函数，
追加 SAS 六阶段门控路由函数。
"""

from typing import Literal

from tradingagents.graph.conditional_logic import ConditionalLogic

from sas_states import SAS_AgentState
from sas_gates import (
    sas_plan_approval_router,
    sas_gate_router,
    MAX_ROLLBACK,
)


class SAS_ConditionalLogic(ConditionalLogic):
    """
    扩展 TradingAgents ConditionalLogic，
    追加 SAS v1.5 CEO 模式专用路由函数。
    """

    def __init__(self, max_debate_rounds: int = 1, max_risk_discuss_rounds: int = 1):
        super().__init__(max_debate_rounds, max_risk_discuss_rounds)

    def sas_plan_approval_router(
        self, state: SAS_AgentState
    ) -> Literal["analyst_team", "end"]:
        """L0 用户计划审批 Gate — 简单任务自动通过，复杂任务等待确认"""
        return sas_plan_approval_router(state)

    def sas_gate_router(
        self, state: SAS_AgentState
    ) -> Literal["sas_archive", "plan_approval", "end"]:
        """SAS 质量检查 Gate — 基于风险评分自动路由"""
        return sas_gate_router(state)

    def sas_rollback_router(
        self, state: SAS_AgentState
    ) -> Literal["plan_approval", "end"]:
        """回退路由 — rollback_count >= MAX_ROLLBACK 时强制终止"""
        current = state.get("rollback_count", 0)
        if current >= MAX_ROLLBACK:
            return "end"
        return "plan_approval"

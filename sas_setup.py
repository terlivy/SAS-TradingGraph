"""
sas_setup.py
SAS v1.5 + TradingAgents 融合 — SAS 增强版 GraphSetup

继承 TradingAgents GraphSetup，保留全部 TA 执行节点和边，
在 START 后插入 SAS 六阶段治理层，
在 END 前追加 SAS 归档节点。

关键设计原则：
  1. 不破坏原有 TA graph 的任何节点和边
  2. SAS 治理层完全作为 wrapper，不侵入 TA 核心逻辑
  3. 使用 SAS_AgentState（AgentState 超集），运行时完全兼容
"""

from typing import Any, Dict

from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI

from tradingagents.agents import *
from tradingagents.graph.conditional_logic import ConditionalLogic
from tradingagents.graph.setup import GraphSetup

from sas_states import SAS_AgentState
from sas_gates import (
    create_sas_planner_node,
    create_sas_gate_node,
    sas_archive_node,
    sas_plan_approval_router,
    sas_gate_router,
)
from sas_conditional_logic import SAS_ConditionalLogic


class SAS_GraphSetup(GraphSetup):
    """
    SAS v1.5 增强版 GraphSetup。

    在 TradingAgents 六类分析师 + 辩论 + 风控的完整执行链基础上，
    包裹 SAS v1.5 六阶段治理层：

      START → L1_SC_Planner → [plan_approval] → 分析师并行
            → 辩论 → Trader → 风险辩论 → SAS_Gate
            → [低风险→归档 | 中风险→回退 | 高风险→终止]
            → 归档 → END
    """

    def __init__(
        self,
        quick_thinking_llm: ChatOpenAI,
        deep_thinking_llm: ChatOpenAI,
        tool_nodes: Dict[str, ToolNode],
        bull_memory,
        bear_memory,
        trader_memory,
        invest_judge_memory,
        portfolio_manager_memory,
        conditional_logic: ConditionalLogic | SAS_ConditionalLogic,
        sas_llm: ChatOpenAI | None = None,
    ):
        super().__init__(
            quick_thinking_llm,
            deep_thinking_llm,
            tool_nodes,
            bull_memory,
            bear_memory,
            trader_memory,
            invest_judge_memory,
            portfolio_manager_memory,
            conditional_logic,
        )
        self.sas_llm = sas_llm or deep_thinking_llm

    def setup_graph(
        self, selected_analysts=["market", "social", "news", "fundamentals"]
    ):
        """构建 SAS 六阶段治理 + TradingAgents 执行层的融合 Graph。"""

        if len(selected_analysts) == 0:
            raise ValueError("SAS-TradingGraph: 必须至少选择一个分析师！")

        # ── 1. SAS 治理节点 ──────────────────────────────────────────────
        sas_planner = create_sas_planner_node(self.sas_llm)
        sas_gate = create_sas_gate_node(self.sas_llm)
        sas_archive = sas_archive_node

        # ── 2. TradingAgents 执行节点（从父类复制，用 SAS_AgentState）────
        analyst_nodes: Dict[str, Any] = {}
        delete_nodes: Dict[str, Any] = {}
        tool_nodes: Dict[str, Any] = {}

        for _at in selected_analysts:
            if _at == "market":
                analyst_nodes[_at] = create_market_analyst(self.quick_thinking_llm)
                delete_nodes[_at] = create_msg_delete()
                tool_nodes[_at] = self.tool_nodes["market"]
            elif _at == "social":
                analyst_nodes[_at] = create_social_media_analyst(self.quick_thinking_llm)
                delete_nodes[_at] = create_msg_delete()
                tool_nodes[_at] = self.tool_nodes["social"]
            elif _at == "news":
                analyst_nodes[_at] = create_news_analyst(self.quick_thinking_llm)
                delete_nodes[_at] = create_msg_delete()
                tool_nodes[_at] = self.tool_nodes["news"]
            elif _at == "fundamentals":
                analyst_nodes[_at] = create_fundamentals_analyst(self.quick_thinking_llm)
                delete_nodes[_at] = create_msg_delete()
                tool_nodes[_at] = self.tool_nodes["fundamentals"]

        bull_researcher_node = create_bull_researcher(self.quick_thinking_llm, self.bull_memory)
        bear_researcher_node = create_bear_researcher(self.quick_thinking_llm, self.bear_memory)
        research_manager_node = create_research_manager(self.deep_thinking_llm, self.invest_judge_memory)
        trader_node = create_trader(self.quick_thinking_llm, self.trader_memory)
        aggressive_analyst = create_aggressive_debator(self.quick_thinking_llm)
        neutral_analyst = create_neutral_debator(self.quick_thinking_llm)
        conservative_analyst = create_conservative_debator(self.quick_thinking_llm)
        portfolio_manager_node = create_portfolio_manager(self.deep_thinking_llm, self.portfolio_manager_memory)

        # ── 3. 创建工作流（使用 SAS_AgentState）──────────────────────────
        workflow = StateGraph(SAS_AgentState)

        # 添加 SAS 节点
        workflow.add_node("L1_SC_Planner", sas_planner)
        workflow.add_node("SAS_Gate", sas_gate)
        workflow.add_node("sas_archive", sas_archive)

        # 添加 TA 节点
        for _at, node in analyst_nodes.items():
            workflow.add_node(f"{_at.capitalize()} Analyst", node)
            workflow.add_node(f"Msg Clear {_at.capitalize()}", delete_nodes[_at])
            workflow.add_node(f"tools_{_at}", tool_nodes[_at])

        workflow.add_node("Bull Researcher", bull_researcher_node)
        workflow.add_node("Bear Researcher", bear_researcher_node)
        workflow.add_node("Research Manager", research_manager_node)
        workflow.add_node("Trader", trader_node)
        workflow.add_node("Aggressive Analyst", aggressive_analyst)
        workflow.add_node("Neutral Analyst", neutral_analyst)
        workflow.add_node("Conservative Analyst", conservative_analyst)
        workflow.add_node("Portfolio Manager", portfolio_manager_node)

        # ── 4. SAS 六阶段边 ─────────────────────────────────────────────
        # START → L1_SC_Planner
        workflow.add_edge(START, "L1_SC_Planner")

        # L1_SC_Planner → plan_approval
        workflow.add_conditional_edges(
            "L1_SC_Planner",
            sas_plan_approval_router,
            {
                "analyst_team": f"{selected_analysts[0].capitalize()} Analyst",
                "end": END,
            },
        )

        # ── 5. TradingAgents 分析师顺序链 ───────────────────────────────
        for i, analyst_type in enumerate(selected_analysts):
            current = f"{analyst_type.capitalize()} Analyst"
            current_tools = f"tools_{analyst_type}"
            current_clear = f"Msg Clear {analyst_type.capitalize()}"

            workflow.add_conditional_edges(
                current,
                getattr(self.conditional_logic, f"should_continue_{analyst_type}"),
                [current_tools, current_clear],
            )
            workflow.add_edge(current_tools, current)

            if i < len(selected_analysts) - 1:
                workflow.add_edge(current_clear, f"{selected_analysts[i+1].capitalize()} Analyst")
            else:
                workflow.add_edge(current_clear, "Bull Researcher")

        # ── 6. TradingAgents 辩论链（完全保留）──────────────────────────
        workflow.add_conditional_edges(
            "Bull Researcher",
            self.conditional_logic.should_continue_debate,
            {"Bear Researcher": "Bear Researcher", "Research Manager": "Research Manager"},
        )
        workflow.add_conditional_edges(
            "Bear Researcher",
            self.conditional_logic.should_continue_debate,
            {"Bull Researcher": "Bull Researcher", "Research Manager": "Research Manager"},
        )
        workflow.add_edge("Research Manager", "Trader")
        workflow.add_edge("Trader", "Aggressive Analyst")

        # 风险辩论
        workflow.add_conditional_edges(
            "Aggressive Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {"Conservative Analyst": "Conservative Analyst", "Portfolio Manager": "Portfolio Manager"},
        )
        workflow.add_conditional_edges(
            "Conservative Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {"Neutral Analyst": "Neutral Analyst", "Portfolio Manager": "Portfolio Manager"},
        )
        workflow.add_conditional_edges(
            "Neutral Analyst",
            self.conditional_logic.should_continue_risk_analysis,
            {"Aggressive Analyst": "Aggressive Analyst", "Portfolio Manager": "Portfolio Manager"},
        )

        # ── 7. SAS Gate 接入 ───────────────────────────────────────────
        workflow.add_edge("Portfolio Manager", "SAS_Gate")

        workflow.add_conditional_edges(
            "SAS_Gate",
            sas_gate_router,
            {
                "sas_archive": "sas_archive",      # 低风险 → 归档
                "plan_approval": "L1_SC_Planner",  # 中风险 → 回退（≤3次）
                "end": END,                          # 高风险/超限 → 终止
            },
        )

        # ── 8. 归档 → END ──────────────────────────────────────────────
        workflow.add_edge("sas_archive", END)

        # ── 9. 编译 ────────────────────────────────────────────────────
        compiled = workflow.compile()
        compiled.sas_governed = True  # type: ignore
        compiled.sas_version = "v1.5.0"  # type: ignore

        return compiled

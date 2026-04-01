"""
sas_trading_graph.py
SAS v1.5 + TradingAgents 融合 — SAS 治理版主类

用法：
    from sas_trading_graph import SAS_TradingAgentsGraph

    graph = SAS_TradingAgentsGraph(debug=True, config=my_config)
    state, decision = graph.propagate("NVDA", "2026-04-01")

    print("SAS 阶段:", state["current_stage"])
    print("风险评分:", state["risk_score"])
    print("审批状态:", state["sas_approval_status"])
    print("最终决策:", decision)
"""

import os
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from tradingagents.llm_clients import create_llm_client
from tradingagents.agents import FinancialSituationMemory
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config

from sas_setup import SAS_GraphSetup
from sas_conditional_logic import SAS_ConditionalLogic
from sas_states import SAS_AgentState


class SAS_TradingAgentsGraph:
    """
    SAS v1.5 CEO 模式 × TradingAgents 融合版主类。

    对外接口与 TradingAgentsGraph 完全一致（propagate / process_signal），
    内部替换 GraphSetup 为 SAS_GraphSetup，追加 SAS 六阶段治理层。

    用户参与点（仅两个）：
      1. plan_approval：计划审批（L2/L3 任务）
      2. sas_gate：高风险人工复核
    """

    def __init__(
        self,
        selected_analysts: List[str] | None = None,
        debug: bool = False,
        config: Dict[str, Any] | None = None,
        callbacks: Optional[List] = None,
    ):
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.callbacks = callbacks or []
        self.selected_analysts = selected_analysts or [
            "market", "social", "news", "fundamentals"
        ]

        set_config(self.config)

        os.makedirs(
            os.path.join(self.config.get("project_dir", "."), "dataflows/data_cache"),
            exist_ok=True,
        )

        # LLM 初始化
        llm_kwargs = self._get_provider_kwargs()
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],
            base_url=self.config.get("base_url"),
            api_key=self.config.get("api_key"),
        )
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],
            base_url=self.config.get("base_url"),
            api_key=self.config.get("api_key"),
        )
        sas_llm_model = self.config.get("sas_llm", self.config["deep_think_llm"])
        sas_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=sas_llm_model,
            base_url=self.config.get("base_url"),
            api_key=self.config.get("api_key"),
        )

        # 内存初始化
        self.bull_memory = FinancialSituationMemory()
        self.bear_memory = FinancialSituationMemory()
        self.trader_memory = FinancialSituationMemory()
        self.invest_judge_memory = FinancialSituationMemory()
        self.portfolio_manager_memory = FinancialSituationMemory()

        # ToolNode 初始化
        self.tool_nodes: Dict[str, ToolNode] = {}
        for _at in self.selected_analysts:
            if _at == "market":
                from tradingagents.agents.utils.core_stock_tools import get_stock_data, get_indicators
                self.tool_nodes[_at] = ToolNode([get_stock_data, get_indicators])
            elif _at == "social":
                from tradingagents.agents.utils.agent_utils import get_global_news
                self.tool_nodes[_at] = ToolNode([get_global_news])
            elif _at == "news":
                from tradingagents.agents.utils.news_data_tools import get_news
                self.tool_nodes[_at] = ToolNode([get_news])
            elif _at == "fundamentals":
                from tradingagents.agents.utils.fundamental_data_tools import (
                    get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement
                )
                self.tool_nodes[_at] = ToolNode([
                    get_fundamentals, get_balance_sheet, get_cashflow, get_income_statement
                ])

        # SAS 条件逻辑 + GraphSetup
        sas_conditional = SAS_ConditionalLogic(
            max_debate_rounds=self.config.get("max_debate_rounds", 2),
            max_risk_discuss_rounds=self.config.get("max_risk_discuss_rounds", 2),
        )

        sas_graph_setup = SAS_GraphSetup(
            quick_thinking_llm=quick_client,
            deep_thinking_llm=deep_client,
            tool_nodes=self.tool_nodes,
            bull_memory=self.bull_memory,
            bear_memory=self.bear_memory,
            trader_memory=self.trader_memory,
            invest_judge_memory=self.invest_judge_memory,
            portfolio_manager_memory=self.portfolio_manager_memory,
            conditional_logic=sas_conditional,
            sas_llm=sas_client,
        )

        self.graph = sas_graph_setup.setup_graph(self.selected_analysts)

        self.log_states_dict: Dict[str, Any] = {}

    def propagate(
        self,
        company_of_interest: str,
        trade_date: str,
        user_approved: bool = True,
    ) -> Tuple[SAS_AgentState, str]:
        """
        执行 SAS 治理下的完整投研流程。

        Args:
            company_of_interest: 股票代码，如 "NVDA", "AAPL"
            trade_date: 分析日期，格式 "YYYY-MM-DD"
            user_approved: L0 用户是否审批通过（传入 True 模拟自动通过）

        Returns:
            (final_state, final_decision)
        """
        input_state: SAS_AgentState = {
            "company_of_interest": company_of_interest,
            "trade_date": trade_date,
            "sender": "user",
            "messages": [
                HumanMessage(
                    content=f"请分析 {company_of_interest} 在 {trade_date} 的投资价值"
                )
            ],
            "current_stage": "接收任务",
            "complexity_level": "L2",
            "sas_approval_status": "auto_pass" if user_approved else "pending",
            "rollback_count": 0,
            "risk_score": 0.0,
            "leader_autonomy": True,
            "plan_summary": "",
            "task_scorecard": {},
            "execution_log": [],
            "market_report": "",
            "sentiment_report": "",
            "news_report": "",
            "fundamentals_report": "",
            "investment_plan": "",
            "trader_investment_plan": "",
            "final_trade_decision": "",
        }

        if not user_approved:
            input_state["sas_approval_status"] = "pending"
            input_state["leader_autonomy"] = False

        final_state: SAS_AgentState = self.graph.invoke(input_state)  # type: ignore

        decision = self.process_signal(final_state.get("final_trade_decision", ""))

        if self.debug:
            print(f"\n{'='*60}")
            print(f"  SAS-TradingGraph 执行报告")
            print(f"{'='*60}")
            print(f"  股票: {company_of_interest}")
            print(f"  日期: {trade_date}")
            print(f"  SAS 阶段: {final_state.get('current_stage', 'N/A')}")
            print(f"  复杂度: {final_state.get('complexity_level', 'N/A')}")
            print(f"  风险评分: {final_state.get('risk_score', 'N/A')}")
            print(f"  审批状态: {final_state.get('sas_approval_status', 'N/A')}")
            print(f"  回退次数: {final_state.get('rollback_count', 0)}")
            print(f"  最终决策: {decision}")
            print(f"{'='*60}\n")

        self.curr_state = final_state
        self.ticker = company_of_interest

        return final_state, decision

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        provider = self.config.get("llm_provider", "openai")
        return {"model": self.config.get("default_llm", "gpt-4o")}

    def process_signal(self, full_signal: str) -> str:
        if not full_signal:
            return "HOLD（暂无明确信号）"
        return full_signal[-500:].strip()

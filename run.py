"""
run.py — SAS-TradingGraph 快速运行脚本

用法：
    python run.py --ticker NVDA --date 2026-04-01
    python run.py --ticker AAPL --date 2026-04-01 --provider deepseek
    python run.py --ticker TSLA --date 2026-04-01 --no-auto-approve
    python run.py --ticker NVDA --date 2026-04-01 --analysts market,news --debug
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="SAS-TradingGraph 快速运行脚本")
    parser.add_argument("--ticker", required=True, help="股票代码，如 NVDA")
    parser.add_argument("--date", required=True, help="分析日期，格式 YYYY-MM-DD")
    parser.add_argument(
        "--provider",
        default=os.getenv("LLM_PROVIDER", "deepseek"),
        choices=["deepseek", "openai", "google", "qwen", "xai", "anthropic"],
    )
    parser.add_argument(
        "--analysts",
        default="market,social,news,fundamentals",
        help="启用的分析师，逗号分隔（默认全部）",
    )
    parser.add_argument(
        "--no-auto-approve", action="store_true",
        help="禁用自动审批（演示 SAS L0 Gate）",
    )
    parser.add_argument("--debug", action="store_true", help="开启调试输出")
    return parser.parse_args()


def build_config(args) -> dict:
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("DASHSCOPE_API_KEY")
        or ""
    )
    config = {
        "llm_provider": args.provider,
        "api_key": api_key,
        "base_url": None,
        "deep_think_llm": os.getenv("DEEP_THINK_LLM", "deepseek-chat"),
        "quick_think_llm": os.getenv("QUICK_THINK_LLM", "deepseek-chat"),
        "sas_llm": os.getenv("SAS_LLM_MODEL", "qwen-plus"),
        "max_debate_rounds": int(os.getenv("MAX_DEBATE_ROUNDS", "2")),
        "max_risk_discuss_rounds": 2,
        "project_dir": str(Path(__file__).parent / "data"),
    }
    if args.provider == "deepseek":
        config["base_url"] = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    elif args.provider == "qwen":
        config["base_url"] = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
        config["api_key"] = os.getenv("DASHSCOPE_API_KEY", api_key)
    return config


def parse_analysts(analysts_str: str) -> list:
    valid = {"market", "social", "news", "fundamentals"}
    selected = [a.strip() for a in analysts_str.split(",")]
    return [a for a in selected if a in valid] or ["market", "social", "news", "fundamentals"]


def main():
    args = parse_args()
    config = build_config(args)
    selected_analysts = parse_analysts(args.analysts)

    if not config["api_key"]:
        print("错误：未找到 API Key！请设置环境变量：")
        print("  export DEEPSEEK_API_KEY=sk-xxxx  # DeepSeek")
        print("  export OPENAI_API_KEY=sk-xxxx    # OpenAI")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"  SAS-TradingGraph 快速启动")
    print(f"{'='*60}")
    print(f"  股票代码 : {args.ticker}")
    print(f"  分析日期 : {args.date}")
    print(f"  LLM Provider: {args.provider}")
    print(f"  分析师   : {', '.join(selected_analysts)}")
    print(f"  自动审批 : {'否（L0 Gate 演示）' if args.no_auto_approve else '是（L1 自动通过）'}")
    print(f"{'='*60}\n")

    from sas_trading_graph import SAS_TradingAgentsGraph

    graph = SAS_TradingAgentsGraph(
        selected_analysts=selected_analysts,
        debug=args.debug or True,
        config=config,
    )

    print("初始化完成，开始执行 SAS 六阶段治理流程...\n")

    final_state, decision = graph.propagate(
        company_of_interest=args.ticker.upper(),
        trade_date=args.date,
        user_approved=not args.no_auto_approve,
    )

    print(f"\n{'='*60}")
    print(f"  执行完成")
    print(f"{'='*60}")
    print(f"  SAS 阶段     : {final_state.get('current_stage', 'N/A')}")
    print(f"  复杂度等级   : {final_state.get('complexity_level', 'N/A')}")
    print(f"  风险评分     : {final_state.get('risk_score', 'N/A')}")
    print(f"  审批状态     : {final_state.get('sas_approval_status', 'N/A')}")
    print(f"  回退次数     : {final_state.get('rollback_count', 0)}")
    plan_summary = final_state.get("plan_summary", "")
    print(f"  计划摘要     : {plan_summary[:100]}..." if plan_summary else "  计划摘要     : N/A")
    print(f"\n  【最终决策】")
    print(f"  {decision}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

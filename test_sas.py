import os
os.environ['DEEPSEEK_API_KEY'] = 'sk-34391d7cce224c278a21a5bf15c3f7b9'
os.environ['TAVILY_API_KEY'] = 'tvly-placeholder'

import sys
# Use the WSL path where tradingagents lives
sys.path.insert(0, '/tmp/sas-tradinggraph')

print("=== SAS_TradingAgentsGraph 初始化测试 ===")
from sas_trading_graph import SAS_TradingAgentsGraph

graph = SAS_TradingAgentsGraph()
print("Graph 创建成功!")

print()
print("=== SAS Gate 路由器测试 ===")
from sas_gates import sas_gate_router, SAS_AgentState

test_state: SAS_AgentState = {
    'messages': [],
    'stock_ticker': 'NVDA',
    'analyst_results': {},
    'bull_case': 'Test bullish case for NVDA',
    'bear_case': 'Test bearish case for NVDA',
    'debate_history': [],
    'risk_assessment': {'risk_level': 'medium', 'concerns': ['volatility']},
    'rollback_count': 0,
    'current_phase': 'implementation',
    'execution_trace': [],
    'approval_status': 'auto_approved',
}
result = sas_gate_router(test_state)
print(f"中风险测试 -> 结果: {result}")

test_state['rollback_count'] = 4
result2 = sas_gate_router(test_state)
print(f"超过3次回退 -> 结果: {result2}")

test_state['risk_assessment']['risk_level'] = 'high'
test_state['rollback_count'] = 0
result3 = sas_gate_router(test_state)
print(f"高风险 -> 结果: {result3}")

test_state['risk_assessment']['risk_level'] = 'low'
result4 = sas_gate_router(test_state)
print(f"低风险 -> 结果: {result4}")

print()
print("=== SAS Planner 节点测试 ===")
from sas_gates import create_sas_planner_node
planner = create_sas_planner_node(graph.deep_thinking_llm)
print("SAS Planner 创建成功!")

print()
print("=== SAS Gate 节点测试 ===")
from sas_gates import create_sas_gate_node
gate = create_sas_gate_node(graph.deep_thinking_llm)
print("SAS Gate 创建成功!")

print()
print("=== SAS 六阶段状态测试 ===")
from sas_states import SAS_AgentState, PHASE_DESCRIPTIONS
for phase, desc in PHASE_DESCRIPTIONS.items():
    print(f"  {phase}: {desc}")

print()
print("=== 测试完成! ===")

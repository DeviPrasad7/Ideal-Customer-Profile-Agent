from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.state import GraphState
from agent.nodes import (
    monitor_node,
    score_node,
    hitl_gateway_node,
    tech_stack_detector_node,
    enricher_node,
    competitor_intel_node,
    cross_validator_node,
    summarizer_node,
    output_dispatcher_node,
    consolidation_node
)

def route_post_monitoring(state: GraphState) -> Literal["hitl_gateway_node", "parallel_enrichment_start"]:
    # Conditional logic based on website url in data
    website_url = state.get("data", {}).get("website_url")
    if not website_url:
        return "hitl_gateway_node"
    return "parallel_enrichment_start"

def route_post_enrichment(state: GraphState) -> Literal["competitor_intel_node", "cross_validator_node"]:
    tech_stack = state.get("data", {}).get("tech_stack", [])
    if tech_stack:
        return "competitor_intel_node"
    return "cross_validator_node"

def route_post_validation(state: GraphState) -> Literal["hitl_gateway_node", "summarizer_node"]:
    confidence = state.get("confidence_score", 1.0)
    conflict = state.get("has_conflict", False)
    if confidence < 0.40 or conflict:
        return "hitl_gateway_node"
    return "summarizer_node"

# Initialize graph
workflow = StateGraph(GraphState)

# Add nodes
workflow.add_node("monitor_node", monitor_node)
workflow.add_node("score_node", score_node)
workflow.add_node("post_monitor_consolidation", consolidation_node)
workflow.add_node("hitl_gateway_node", hitl_gateway_node)

workflow.add_node("tech_stack_detector_node", tech_stack_detector_node)
workflow.add_node("enricher_node", enricher_node)
workflow.add_node("post_enrichment_consolidation", consolidation_node)

workflow.add_node("competitor_intel_node", competitor_intel_node)
workflow.add_node("cross_validator_node", cross_validator_node)
workflow.add_node("summarizer_node", summarizer_node)
workflow.add_node("output_dispatcher_node", output_dispatcher_node)

# ==============================================================================
# Graph Routing & Wiring
# ==============================================================================

# Phase 2: Monitoring & Scoring run in parallel
workflow.add_edge(START, "monitor_node")
workflow.add_edge(START, "score_node")

# Converge parallel branches
workflow.add_edge("monitor_node", "post_monitor_consolidation")
workflow.add_edge("score_node", "post_monitor_consolidation")

# Website Validation Routing (Phase 3)
workflow.add_conditional_edges(
    "post_monitor_consolidation",
    route_post_monitoring,
    {
        "hitl_gateway_node": "hitl_gateway_node",
        "parallel_enrichment_start": "tech_stack_detector_node" 
    }
)

# Phase 4: Parallel Enrichment
workflow.add_edge("hitl_gateway_node", "tech_stack_detector_node") # Resume after HITL
workflow.add_edge("hitl_gateway_node", "enricher_node") # Start parallel branch

workflow.add_edge("post_monitor_consolidation", "tech_stack_detector_node")
workflow.add_edge("post_monitor_consolidation", "enricher_node")

# Converge Phase 4
workflow.add_edge("tech_stack_detector_node", "post_enrichment_consolidation")
workflow.add_edge("enricher_node", "post_enrichment_consolidation")

# Phase 5 & 6: Competitor Intel (Conditional) & Validation
workflow.add_conditional_edges(
    "post_enrichment_consolidation",
    route_post_enrichment,
    {
        "competitor_intel_node": "competitor_intel_node",
        "cross_validator_node": "cross_validator_node"
    }
)
workflow.add_edge("competitor_intel_node", "cross_validator_node")

# Phase 7: Confidence Check & Summarization
workflow.add_conditional_edges(
    "cross_validator_node",
    route_post_validation,
    {
        "hitl_gateway_node": "hitl_gateway_node",
        "summarizer_node": "summarizer_node"
    }
)

# Phase 8: Final HITL Gateway before output
workflow.add_edge("summarizer_node", "output_dispatcher_node")
workflow.add_edge("hitl_gateway_node", "output_dispatcher_node") # Final review convergence

workflow.add_edge("output_dispatcher_node", END)

# Memory Checkpointer
memory = MemorySaver()

# Compile the workflow with interrupt (HITL) on specific node
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["hitl_gateway_node"] # Native HITL gateway
)

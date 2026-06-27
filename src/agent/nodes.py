import time
from typing import Any
from agent.state import GraphState, ValidationNote
from agent.utils import Toolbox, CircuitBreakerState, MonitoringService

toolbox = Toolbox()

def monitor_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    try:
        # Circuit Breaker Check
        cb_state = toolbox.circuit_breaker.check_health("RSS_SOURCE")
        if cb_state == CircuitBreakerState.OPEN:
            MonitoringService.log_warning(prospect_id, "RSS source unavailable, skipping")
            return {"executed_agents": ["monitor_node"]}
        
        # Mock poll external sources
        toolbox.circuit_breaker.record_success("RSS_SOURCE")
        return {
            "executed_agents": ["monitor_node"],
            "data": {"raw_signals": ["signal1", "signal2"]}
        }
    except Exception as e:
        toolbox.circuit_breaker.record_failure("RSS_SOURCE")
        MonitoringService.log_error(prospect_id, f"MONITOR_ERROR: {str(e)}")
        return {"executed_agents": ["monitor_node"]}

def score_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    try:
        signals = state.get("data", {}).get("raw_signals", [])
        if not signals:
            MonitoringService.log_info(prospect_id, "No signals passed filter")
            return {
                "executed_agents": ["score_node"],
                "overall_status": "NO_ACTION"
            }
        
        return {
            "executed_agents": ["score_node"],
            "data": {"scored_signals": ["signal1"]}
        }
    except Exception as e:
        MonitoringService.log_error(prospect_id, f"SCORE_ERROR: {str(e)}")
        return {"executed_agents": ["score_node"]}

def hitl_gateway_node(state: GraphState) -> dict[str, Any]:
    # In LangGraph, to trigger an interrupt, we can simply rely on the routing.
    # However, this node might just prepare the state or handle the response after resuming.
    human_override = state.get("human_override_payload")
    if human_override:
        return {
            "executed_agents": ["hitl_gateway_node"],
            "data": {"website_url": human_override}, # Example of applying override
            "human_override_payload": None # Reset after applying
        }
    return {"executed_agents": ["hitl_gateway_node"]}

def tech_stack_detector_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    try:
        cb_state = toolbox.circuit_breaker.check_health("TECH_DETECTION_API")
        if cb_state == CircuitBreakerState.OPEN:
            return {"executed_agents": ["tech_stack_detector_node"]}
            
        toolbox.circuit_breaker.record_success("TECH_DETECTION_API")
        return {
            "executed_agents": ["tech_stack_detector_node"],
            "data": {"tech_stack": [{"technology": "Python", "category": "Language"}]},
            "tech_detection_status": "SUCCESS"
        }
    except Exception as e:
        toolbox.circuit_breaker.record_failure("TECH_DETECTION_API")
        MonitoringService.log_warning(prospect_id, f"TECH_DETECTION_ERROR: {str(e)}")
        return {
            "executed_agents": ["tech_stack_detector_node"],
            "tech_detection_status": "PARTIAL"
        }

def enricher_node(state: GraphState) -> dict[str, Any]:
    try:
        toolbox.circuit_breaker.record_success("CRUNCHBASE_API")
        return {
            "executed_agents": ["enricher_node"],
            "data": {"firmographics": {"employeeCount": 150, "revenue": "10M"}}
        }
    except Exception as e:
        toolbox.circuit_breaker.record_failure("CRUNCHBASE_API")
        return {"executed_agents": ["enricher_node"]}

def competitor_intel_node(state: GraphState) -> dict[str, Any]:
    tech_stack = state.get("data", {}).get("tech_stack", [])
    if tech_stack:
        return {
            "executed_agents": ["competitor_intel_node"],
            "data": {"competitor_intel": {"competitor1": "pain_points"}}
        }
    return {"executed_agents": ["competitor_intel_node"]}

def cross_validator_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    firmographics = state.get("data", {}).get("firmographics", {})
    
    # Mock validation logic
    if firmographics.get("employeeCount") == 500: # Example conflict
        note = ValidationNote(level="WARN", message="Data conflict detected", source_agent="validator", timestamp=time.time())
        MonitoringService.log_warning(prospect_id, "Data conflict detected")
        return {
            "executed_agents": ["cross_validator_node"],
            "confidence_score": 0.70,
            "has_conflict": True,
            "validation_notes": [note]
        }
    
    return {
        "executed_agents": ["cross_validator_node"],
        "confidence_score": 0.95,
        "has_conflict": False
    }

def summarizer_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    try:
        cb_state = toolbox.circuit_breaker.check_health("LLM_API")
        if cb_state == CircuitBreakerState.OPEN:
            MonitoringService.log_warning(prospect_id, "LLM circuit open, using fallback")
            return {
                "executed_agents": ["summarizer_node"],
                "data": {"summary_object": "FALLBACK SUMMARY"}
            }
        
        summary = toolbox.generate_text("Prompt", "Fallback")
        toolbox.circuit_breaker.record_success("LLM_API")
        return {
            "executed_agents": ["summarizer_node"],
            "data": {"summary_object": summary}
        }
    except Exception as e:
        toolbox.circuit_breaker.record_failure("LLM_API")
        return {
            "executed_agents": ["summarizer_node"],
            "data": {"summary_object": "FALLBACK SUMMARY"}
        }

def output_dispatcher_node(state: GraphState) -> dict[str, Any]:
    prospect_id = state.get("prospect_id", "unknown")
    try:
        toolbox.emit_event("PROSPECT_COMPLETED", {"prospect": prospect_id, "status": "done"})
        MonitoringService.log_success(prospect_id, "Execution Time: X ms")
        return {
            "executed_agents": ["output_dispatcher_node"],
            "overall_status": "COMPLETED"
        }
    except Exception as e:
        MonitoringService.log_error(prospect_id, "OUTPUT_FAILED")
        return {"executed_agents": ["output_dispatcher_node"]}

def consolidation_node(state: GraphState) -> dict[str, Any]:
    """Node used strictly to converge parallel flows."""
    return {}

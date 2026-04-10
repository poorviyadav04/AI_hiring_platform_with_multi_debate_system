"""
Scoring utilities for candidate evaluation.
Now MCP-aware: uses MCP registry internally for tool discovery.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements


def calculate_overall_score(
    candidate: CandidateProfile,
    job: JobRequirements
) -> Dict[str, Any]:
    """
    Calculate overall candidate score using MCP scoring server.
    
    This function is MCP-aware: it uses the MCP registry internally 
    to call scoring tools via the MCP protocol.
    
    Args:
        candidate: Candidate profile
        job: Job requirements
        
    Returns:
        Dict with overall_score, component_scores, and detailed breakdown
    """
    try:
        from mcp_servers import get_registry
        
        registry = get_registry()
        
        # Call scoring tools via MCP protocol
        result = registry.execute(
            "scoring",
            "calculate_overall_score_full",  # Full scoring with breakdown
            candidate=candidate,
            job=job
        )
        
        return result
        
    except Exception as e:
        # Fallback to direct implementation if MCP not available
        print(f"⚠️ MCP scoring unavailable, using fallback: {e}")
        return _calculate_overall_score_fallback(candidate, job)


def _calculate_overall_score_fallback(
    candidate: CandidateProfile,
    job: JobRequirements
) -> Dict[str, Any]:
    """Fallback when MCP not available - calls deterministic scoring."""
    # Use existing detailed implementation
    return calculate_overall_score_original(candidate, job)

"""
Memory Server - MCP Server for memory/RAG tools.

Exposes memory query functionality via MCP protocol.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_servers.mcp_base import (
    MCPServer, ToolParameter, ToolParameterType
)
from tools.memory_query import get_memory_helper
from data.schemas import CandidateProfile, JobRequirements


class MemoryServer(MCPServer):
    """
    MCP Server for memory and RAG tools.
    
    Provides:
    - Find similar past hires
    - Find similar past rejections
    - Check decision consistency
    - Get candidate history
    - Get memory statistics
    """
    
    def __init__(self):
        """Initialize memory server."""
        super().__init__(
            name="memory",
            description="Memory and RAG query tools for past decisions"
        )
        self.memory = get_memory_helper()
        self.register_tools()
    
    def register_tools(self):
        """Register all memory tools."""
        
        # Tool 1: Find similar hires
        self.register_tool(
            name="find_similar_hires",
            handler=self._find_similar_hires,
            description="Find similar candidates who were hired",
            parameters=[
                ToolParameter(
                    name="candidate_id",
                    param_type=ToolParameterType.STRING,
                    description="Current candidate ID"
                ),
                ToolParameter(
                    name="job_title",
                    param_type=ToolParameterType.STRING,
                    description="Job title"
                ),
                ToolParameter(
                    name="top_k",
                    param_type=ToolParameterType.INTEGER,
                    description="Number of similar cases to return",
                    required=False,
                    default=3
                )
            ],
            version="1.0.0"
        )
        
        # Tool 2: Find similar rejections
        self.register_tool(
            name="find_similar_rejections",
            handler=self._find_similar_rejections,
            description="Find similar candidates who were rejected",
            parameters=[
                ToolParameter(
                    name="candidate_id",
                    param_type=ToolParameterType.STRING,
                    description="Current candidate ID"
                 ),
                ToolParameter(
                    name="job_title",
                    param_type=ToolParameterType.STRING,
                    description="Job title"
                ),
                ToolParameter(
                    name="top_k",
                    param_type=ToolParameterType.INTEGER,
                    description="Number of similar cases to return",
                    required=False,
                    default=3
                )
            ],
            version="1.0.0"
        )
        
        # Tool 3: Check consistency
        self.register_tool(
            name="check_consistency",
            handler=self._check_consistency,
            description="Check if decision is consistent with past similar cases",
            parameters=[
                ToolParameter(
                    name="candidate_id",
                    param_type=ToolParameterType.STRING,
                    description="Candidate ID"
                ),
                ToolParameter(
                    name="job_title",
                    param_type=ToolParameterType.STRING,
                    description="Job title"
                ),
                ToolParameter(
                    name="score",
                    param_type=ToolParameterType.FLOAT,
                    description="Current evaluation score"
                ),
                ToolParameter(
                    name="decision",
                    param_type=ToolParameterType.STRING,
                    description="Current decision (hire/reject/conditional)"
                )
            ],
            version="1.0.0"
        )
        
        # Tool 4: Get statistics
        self.register_tool(
            name="get_statistics",
            handler=self._get_statistics,
            description="Get memory system statistics",
            parameters=[],
            version="1.0.0"
        )
    
    def _find_similar_hires(self, candidate_id, job_title, top_k=3):
        """Find similar past hires."""
        # Create minimal candidate/job objects for querying
        # In production, would fetch full profiles
        from data.evaluation_store import get_evaluation_store
        eval_store = get_evaluation_store()
        all_evals = eval_store.get_all_evaluations(limit=50)
        
        # Filter for hires with similar job
        hires = [
            {
                "candidate_name": e.candidate_name,
                "job_title": e.job_title,
                "score": e.overall_score,
                "timestamp": e.timestamp[:10]
            }
            for e in all_evals
            if 'hire' in e.final_decision.lower() and job_title.lower() in e.job_title.lower()
        ]
        
        return hires[:top_k]
    
    def _find_similar_rejections(self, candidate_id, job_title, top_k=3):
        """Find similar past rejections."""
        from data.evaluation_store import get_evaluation_store
        eval_store = get_evaluation_store()
        all_evals = eval_store.get_all_evaluations(limit=50)
        
        rejections = [
            {
                "candidate_name": e.candidate_name,
                "job_title": e.job_title,
                "score": e.overall_score,
                "timestamp": e.timestamp[:10]
            }
            for e in all_evals
            if 'reject' in e.final_decision.lower() and 'conditional' not in e.final_decision.lower()
            and job_title.lower() in e.job_title.lower()
        ]
        
        return rejections[:top_k]
    
    def _check_consistency(self, candidate_id, job_title, score, decision):
        """Check decision consistency."""
        # Simplified consistency check
        from data.evaluation_store import get_evaluation_store
        eval_store = get_evaluation_store()
        all_evals = eval_store.get_all_evaluations(limit=50)
        
        similar_cases = []
        for e in all_evals:
            if job_title.lower() in e.job_title.lower():
                score_diff = abs(score - e.overall_score)
                if score_diff < 10:  # Similar score
                    similar_cases.append({
                        "name": e.candidate_name,
                        "score": e.overall_score,
                        "decision": e.final_decision
                    })
        
        flags = []
        for case in similar_cases:
            if case['decision'] != decision:
                flags.append(f"Similar score but different decision: {case['name']} ({case['score']:.1f})")
        
        return {
            "is_consistent": len(flags) == 0,
            "similar_cases": len(similar_cases),
            "flags": flags
        }
    
    def _get_statistics(self):
        """Get memory statistics."""
        return self.memory.get_statistics()


def get_memory_server() -> MemoryServer:
    """Get or create memory server instance."""
    return MemoryServer()


__all__ = ["MemoryServer", "get_memory_server"]

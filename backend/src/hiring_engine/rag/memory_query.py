"""Memory query helper — provides past decision context to agents."""

import logging
from typing import Dict, List, Any, Optional

from hiring_engine.schemas.candidate import CandidateProfile
from hiring_engine.schemas.job import JobRequirements

logger = logging.getLogger(__name__)

_memory_helper: Optional["MemoryQueryHelper"] = None


class MemoryQueryHelper:
    """Provides RAG-powered memory queries for agents."""

    def __init__(self):
        self._evaluations: List[Dict] = []

    def find_similar_hires(
        self, candidate: CandidateProfile, job: JobRequirements, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar past hires for comparison."""
        # Simplified: returns stored evaluations that were hires
        hires = [
            e for e in self._evaluations
            if "hire" in e.get("final_decision", "").lower()
            and job.title.lower() in e.get("job_title", "").lower()
        ]
        return hires[:top_k]

    def find_similar_rejections(
        self, candidate: CandidateProfile, job: JobRequirements, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar past rejections for comparison."""
        rejections = [
            e for e in self._evaluations
            if "reject" in e.get("final_decision", "").lower()
            and "conditional" not in e.get("final_decision", "").lower()
            and job.title.lower() in e.get("job_title", "").lower()
        ]
        return rejections[:top_k]

    def check_consistency(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        current_score: float,
        current_decision: str,
    ) -> Dict[str, Any]:
        """Check if a decision is consistent with past similar cases."""
        similar_cases = []
        for e in self._evaluations:
            if job.title.lower() in e.get("job_title", "").lower():
                score_diff = abs(current_score - e.get("overall_score", 0))
                if score_diff < 10:
                    similar_cases.append({
                        "name": e.get("candidate_name", ""),
                        "score": e.get("overall_score", 0),
                        "decision": e.get("final_decision", ""),
                    })

        flags = [
            f"Similar score but different decision: {c['name']} ({c['score']:.1f})"
            for c in similar_cases
            if c["decision"] != current_decision
        ]

        return {
            "is_consistent": len(flags) == 0,
            "similar_cases": len(similar_cases),
            "flags": flags,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            "total_evaluations": len(self._evaluations),
            "hires": len([e for e in self._evaluations if "hire" in e.get("final_decision", "").lower()]),
            "rejections": len([e for e in self._evaluations if "reject" in e.get("final_decision", "").lower()]),
        }


def get_memory_helper() -> MemoryQueryHelper:
    """Get or create singleton memory helper."""
    global _memory_helper
    if _memory_helper is None:
        _memory_helper = MemoryQueryHelper()
    return _memory_helper

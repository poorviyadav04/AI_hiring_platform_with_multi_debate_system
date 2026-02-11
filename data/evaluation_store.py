"""
Evaluation storage system for tracking past hiring decisions.
Saves evaluations to JSON files and provides query interface.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class EvaluationRecord:
    """Record of a single candidate evaluation."""
    evaluation_id: str
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str
    overall_score: float
    component_scores: Dict[str, float]
    final_decision: str
    timestamp: str
    debate_transcript: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationRecord':
        """Create from dictionary."""
        return cls(**data)


class EvaluationStore:
    """
    Persistent storage for evaluation history.
    Uses JSON file structure organized by date.
    """
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize evaluation store.
        
        Args:
            storage_dir: Directory for storing evaluations (default: data/evaluations)
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent / "evaluations"
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Index file for quick lookups
        self.index_file = self.storage_dir / "index.json"
        self._load_index()
    
    def _load_index(self):
        """Load or create the index file."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {
                "total_evaluations": 0,
                "evaluations_by_candidate": {},
                "evaluations_by_job": {},
                "evaluations_by_date": {}
            }
            self._save_index()
    
    def _save_index(self):
        """Save the index file."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def save_evaluation(
        self,
        candidate_id: str,
        candidate_name: str,
        job_id: str,
        job_title: str,
        overall_score: float,
        component_scores: Dict[str, float],
        final_decision: str,
        debate_transcript: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save an evaluation to storage.
        
        Args:
            candidate_id: Candidate identifier
            candidate_name: Candidate name
            job_id: Job identifier
            job_title: Job title
            overall_score: Overall evaluation score
            component_scores: Component score breakdown
            final_decision: Final hiring decision
            debate_transcript: Full agent debate transcript
            metadata: Optional additional metadata
            
        Returns:
            Evaluation ID
        """
        # Generate evaluation ID
        timestamp = datetime.now()
        evaluation_id = f"EVAL-{timestamp.strftime('%Y%m%d-%H%M%S')}-{candidate_id}"
        
        # Create evaluation record
        record = EvaluationRecord(
            evaluation_id=evaluation_id,
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            job_id=job_id,
            job_title=job_title,
            overall_score=overall_score,
            component_scores=component_scores,
            final_decision=final_decision,
            timestamp=timestamp.isoformat(),
            debate_transcript=debate_transcript,
            metadata=metadata or {}
        )
        
        # Save to date-based directory
        date_dir = self.storage_dir / timestamp.strftime('%Y-%m-%d')
        date_dir.mkdir(exist_ok=True)
        
        eval_file = date_dir / f"{evaluation_id}.json"
        with open(eval_file, 'w') as f:
            json.dump(record.to_dict(), f, indent=2)
        
        # Update index
        self._update_index(record, timestamp)
        
        return evaluation_id
    
    def _update_index(self, record: EvaluationRecord, timestamp: datetime):
        """Update the index with new evaluation."""
        self.index["total_evaluations"] += 1
        
        # Index by candidate
        if record.candidate_id not in self.index["evaluations_by_candidate"]:
            self.index["evaluations_by_candidate"][record.candidate_id] = []
        self.index["evaluations_by_candidate"][record.candidate_id].append(record.evaluation_id)
        
        # Index by job
        if record.job_id not in self.index["evaluations_by_job"]:
            self.index["evaluations_by_job"][record.job_id] = []
        self.index["evaluations_by_job"][record.job_id].append(record.evaluation_id)
        
        # Index by date
        date_key = timestamp.strftime('%Y-%m-%d')
        if date_key not in self.index["evaluations_by_date"]:
            self.index["evaluations_by_date"][date_key] = []
        self.index["evaluations_by_date"][date_key].append(record.evaluation_id)
        
        self._save_index()
    
    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationRecord]:
        """
        Retrieve a specific evaluation by ID.
        
        Args:
            evaluation_id: Evaluation identifier
            
        Returns:
            EvaluationRecord or None if not found
        """
        # Extract date from evaluation ID
        try:
            date_part = evaluation_id.split('-')[1]  # YYYYMMDD
            date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
            eval_file = self.storage_dir / date_str / f"{evaluation_id}.json"
            
            if eval_file.exists():
                with open(eval_file, 'r') as f:
                    data = json.load(f)
                return EvaluationRecord.from_dict(data)
        except Exception as e:
            print(f"Error retrieving evaluation {evaluation_id}: {e}")
        
        return None
    
    def get_candidate_history(self, candidate_id: str) -> List[EvaluationRecord]:
        """
        Get all evaluations for a specific candidate.
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            List of EvaluationRecords, sorted by timestamp (newest first)
        """
        eval_ids = self.index["evaluations_by_candidate"].get(candidate_id, [])
        
        evaluations = []
        for eval_id in eval_ids:
            record = self.get_evaluation(eval_id)
            if record:
                evaluations.append(record)
        
        # Sort by timestamp (newest first)
        evaluations.sort(key=lambda x: x.timestamp, reverse=True)
        return evaluations
    
    def get_job_history(self, job_id: str) -> List[EvaluationRecord]:
        """
        Get all evaluations for a specific job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            List of EvaluationRecords, sorted by timestamp (newest first)
        """
        eval_ids = self.index["evaluations_by_job"].get(job_id, [])
        
        evaluations = []
        for eval_id in eval_ids:
            record = self.get_evaluation(eval_id)
            if record:
                evaluations.append(record)
        
        evaluations.sort(key=lambda x: x.timestamp, reverse=True)
        return evaluations
    
    def get_all_evaluations(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[EvaluationRecord]:
        """
        Get all evaluations, optionally filtered by date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD) or None for all
            end_date: End date (YYYY-MM-DD) or None for all
            limit: Maximum number of results
            
        Returns:
            List of EvaluationRecords, sorted by timestamp (newest first)
        """
        evaluations = []
        
        # Get all evaluation IDs
        all_eval_ids = []
        for date_key, eval_ids in self.index["evaluations_by_date"].items():
            # Filter by date range if specified
            if start_date and date_key < start_date:
                continue
            if end_date and date_key > end_date:
                continue
            all_eval_ids.extend(eval_ids)
        
        # Load evaluations
        for eval_id in all_eval_ids:
            record = self.get_evaluation(eval_id)
            if record:
                evaluations.append(record)
        
        # Sort by timestamp (newest first)
        evaluations.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit if specified
        if limit:
            evaluations = evaluations[:limit]
        
        return evaluations
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about evaluations.
        
        Returns:
            Dictionary with statistics
        """
        all_evals = self.get_all_evaluations()
        
        if not all_evals:
            return {
                "total_evaluations": 0,
                "unique_candidates": 0,
                "unique_jobs": 0,
                "decisions": {},
                "average_score": 0
            }
        
        decisions = {}
        total_score = 0
        
        for eval in all_evals:
            decision = eval.final_decision
            decisions[decision] = decisions.get(decision, 0) + 1
            total_score += eval.overall_score
        
        return {
            "total_evaluations": len(all_evals),
            "unique_candidates": len(self.index["evaluations_by_candidate"]),
            "unique_jobs": len(self.index["evaluations_by_job"]),
            "decisions": decisions,
            "average_score": total_score / len(all_evals) if all_evals else 0
        }


# Global instance
_evaluation_store: Optional[EvaluationStore] = None


def get_evaluation_store() -> EvaluationStore:
    """Get or create global evaluation store instance."""
    global _evaluation_store
    if _evaluation_store is None:
        _evaluation_store = EvaluationStore()
    return _evaluation_store

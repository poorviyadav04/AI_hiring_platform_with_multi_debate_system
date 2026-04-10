"""
Memory Query Utilities - Now with Hybrid Retrieval Support

Provides utilities for querying evaluation memory with:
- FAISS vector search (Phase 1 ✅)
- Hybrid retrieval: vector + graph traversal (Phase 5 ✅)
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))

from data.evaluation_store import EvaluationStore, EvaluationRecord
from data.schemas import CandidateProfile, JobRequirements


class MemoryQueryHelper:
    """
    Helper for querying evaluation memory.
    Now supports hybrid retrieval combining vector search + graph.
    """
    
    def __init__(self, use_hybrid: bool = False):
        """
        Initialize memory query helper.

        Args:
            use_hybrid: If True, use hybrid retrieval (vector + graph)
        """
        self.eval_store = EvaluationStore()
        self.use_hybrid = use_hybrid
        self.hybrid_retriever = None  # always defined

        if use_hybrid:
            try:
                from rag.hybrid_retrieval import HybridRetriever
                from rag.vector_store import VectorStore
                from rag.decision_graph import DecisionGraph

                vector_store = VectorStore()
                vector_store.load()

                decision_graph = DecisionGraph()
                decision_graph.load()

                self.hybrid_retriever = HybridRetriever(
                    vector_store=vector_store,
                    decision_graph=decision_graph
                )

                print("✅ Hybrid retrieval activated (vector + graph)")

            except Exception as e:
                print(f"⚠️ Hybrid retrieval unavailable: {e}")
                self.use_hybrid = False

    def find_similar_hires(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find similar past hires using RAG or hybrid retrieval.
        
        Uses hybrid retrieval (vector + graph) if enabled, otherwise FAISS only.
        """
        # NEW: Try hybrid retrieval first if enabled
        if self.use_hybrid and hasattr(self, 'hybrid_retriever'):
            try:
                results = self.hybrid_retriever.search_candidates(
                    query=f"{candidate.name} {' '.join(candidate.skills)}",
                    top_k=top_k,
                    decision_filter="hire"
                )
                
                # Convert to expected format
                similar_hires = []
                for result in results:
                    similar_hires.append({
                        'candidate_name': result.get('name', 'Unknown'),
                        'job_title': result.get('job_title', 'N/A'),
                        'score': result.get('score', 0),
                        'decision': 'hire',
                        'similarity': result.get('similarity', 0),
                        'timestamp': result.get('timestamp', ''),
                        'graph_boost': result.get('graph_boost', 0)  # From graph traversal
                    })
                
                return similar_hires[:top_k]
            except Exception as e:
                print(f"⚠️ Hybrid retrieval failed, falling back to vector: {e}")
        
        # Use RAG vector search for semantic similarity
        try:
            from rag import VectorStore
            from tools.execution_tracer import get_current_tracer
            
            tracer = get_current_tracer()
            
            # Load vector store
            vector_store = VectorStore()
            vector_store.load()
            
            # Build query from candidate profile
            query = f"{candidate.name} {' '.join(candidate.skills)} {candidate.experience_years} years experience"
            
            # Log tool call
            if tracer:
                tracer.log_event(
                    event_type="tool_start",
                    action="vector_search_hires",
                    input_data={"query": query[:50], "top_k": top_k}
                )
            
            # Search for similar candidates
            results = vector_store.search_similar_candidates(query, top_k=top_k * 2)
            
            # Filter for hires only
            all_evals = self.eval_store.get_all_evaluations()
            eval_map = {e.candidate_id: e for e in all_evals if 'hire' in e.final_decision.lower()}
            
            similar_hires = []
            for result in results:
                if result['candidate_id'] in eval_map:
                    eval = eval_map[result['candidate_id']]
                    similar_hires.append({
                        'candidate_name': eval.candidate_name,
                        'job_title': eval.job_title,
                        'score': eval.overall_score,
                        'decision': eval.final_decision,
                        'similarity': result['similarity'],
                        'timestamp': eval.timestamp[:10]
                    })
                    
                    if len(similar_hires) >= top_k:
                        break
            
            if tracer:
                tracer.log_event(
                    event_type="tool_end",
                    action="vector_search_hires",
                    output_data={"results": len(similar_hires)}
                )
            
            return similar_hires
            
        except Exception as e:
            # Fallback to simple filtering if RAG not available
            print(f"⚠️ Vector search unavailable, using fallback: {e}")
            return self._fallback_find_similar_hires(candidate, job, top_k)
    
    def _fallback_find_similar_hires(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 3
    ) -> List[Dict]:
        """Fallback method using simple filtering (original implementation)."""
        all_evals = self.eval_store.get_all_evaluations()
        
        # Filter for hires only
        hires = [e for e in all_evals if 'hire' in e.final_decision.lower()]
        
        if not hires:
            return []
        
        # Score similarity
        similar = []
        for eval in hires:
            similarity_score = self._calculate_similarity(candidate, job, eval)
            if similarity_score > 0.3:  # Threshold for relevance
                similar.append({
                    'candidate_name': eval.candidate_name,
                    'job_title': eval.job_title,
                    'score': eval.overall_score,
                    'decision': eval.final_decision,
                    'similarity': similarity_score,
                    'timestamp': eval.timestamp[:10]
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar[:top_k]
    
    def find_similar_rejections(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find similar candidates who were rejected using FAISS vector search.
        
        Args:
            candidate: Current candidate profile
            job: Current job requirements
            top_k: Number of similar cases to return
            
        Returns:
            List of similar rejection cases
        """
        # Use RAG vector search for semantic similarity
        try:
            from rag import VectorStore
            from tools.execution_tracer import get_current_tracer
            
            tracer = get_current_tracer()
            
            # Load vector store
            vector_store = VectorStore()
            vector_store.load()
            
            # Build query from candidate profile
            query = f"{candidate.name} {' '.join(candidate.skills)} {candidate.experience_years} years experience"
            
            # Log tool call
            if tracer:
                tracer.log_event(
                    event_type="tool_start",
                    action="vector_search_rejections",
                    input_data={"query": query[:50], "top_k": top_k}
                )
            
            # Search for similar candidates
            results = vector_store.search_similar_candidates(query, top_k=top_k * 2)
            
            # Filter for rejections only
            all_evals = self.eval_store.get_all_evaluations()
            eval_map = {e.candidate_id: e for e in all_evals 
                       if 'reject' in e.final_decision.lower() and 'conditional' not in e.final_decision.lower()}
            
            similar_rejects = []
            for result in results:
                if result['candidate_id'] in eval_map:
                    eval = eval_map[result['candidate_id']]
                    similar_rejects.append({
                        'candidate_name': eval.candidate_name,
                        'job_title': eval.job_title,
                        'score': eval.overall_score,
                        'decision': eval.final_decision,
                        'similarity': result['similarity'],
                        'timestamp': eval.timestamp[:10],
                        'component_scores': eval.component_scores
                    })
                    
                    if len(similar_rejects) >= top_k:
                        break
            
            if tracer:
                tracer.log_event(
                    event_type="tool_end",
                    action="vector_search_rejections",
                    output_data={"results": len(similar_rejects)}
                )
            
            return similar_rejects
            
        except Exception as e:
            # Fallback to simple filtering if RAG not available
            print(f"⚠️ Vector search unavailable, using fallback: {e}")
            return self._fallback_find_similar_rejections(candidate, job, top_k)
    
    def _fallback_find_similar_rejections(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 3
    ) -> List[Dict]:
        """Fallback method using simple filtering (original implementation)."""
        all_evals = self.eval_store.get_all_evaluations()
        
        # Filter for rejections only
        rejections = [e for e in all_evals if 'reject' in e.final_decision.lower() and 'conditional' not in e.final_decision.lower()]
        
        if not rejections:
            return []
        
        # Score similarity
        similar = []
        for eval in rejections:
            similarity_score = self._calculate_similarity(candidate, job, eval)
            if similarity_score > 0.3:
                similar.append({
                    'candidate_name': eval.candidate_name,
                    'job_title': eval.job_title,
                    'score': eval.overall_score,
                    'decision': eval.final_decision,
                    'similarity': similarity_score,
                    'timestamp': eval.timestamp[:10],
                    'component_scores': eval.component_scores
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar[:top_k]
    
    def check_consistency(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        current_score: float,
        current_decision: str
    ) -> Dict:
        """
        Check if current decision is consistent with past similar cases.
        
        Args:
            candidate: Current candidate
            job: Current job
            current_score: Current evaluation score
            current_decision: Current decision
            
        Returns:
            Consistency report
        """
        all_evals = self.eval_store.get_all_evaluations()
        
        if not all_evals:
            return {
                'is_consistent': True,
                'similar_cases': 0,
                'flags': []
            }
        
        # Find similar cases
        similar_cases = []
        for eval in all_evals:
            similarity = self._calculate_similarity(candidate, job, eval)
            if similarity > 0.4:  # Higher threshold for consistency check
                similar_cases.append({
                    'name': eval.candidate_name,
                    'score': eval.overall_score,
                    'decision': eval.final_decision,
                    'similarity': similarity
                })
        
        if not similar_cases:
            return {
                'is_consistent': True,
                'similar_cases': 0,
                'flags': []
            }
        
        # Check for inconsistencies
        flags = []
        
        for case in similar_cases:
            score_diff = abs(current_score - case['score'])
            
            # Flag 1: Similar score but different decision
            if score_diff < 10 and current_decision != case['decision']:
                flags.append(
                    f"Similar candidate '{case['name']}' (score: {case['score']:.1f}) was {case['decision']}, "
                    f"but current candidate (score: {current_score:.1f}) is {current_decision}"
                )
            
            # Flag 2: Higher score but worse decision
            if current_score > case['score'] + 5 and 'reject' in current_decision and 'hire' in case['decision']:
                flags.append(
                    f"Current candidate scores higher ({current_score:.1f}) than '{case['name']}' ({case['score']:.1f}) "
                    f"who was hired, but is being rejected"
                )
        
        return {
            'is_consistent': len(flags) == 0,
            'similar_cases': len(similar_cases),
            'flags': flags,
            'similar_decisions': similar_cases
        }
    
    def get_candidate_history(self, candidate_id: str) -> List[EvaluationRecord]:
        """
        Get past evaluation history for a specific candidate.
        
        Args:
            candidate_id: Candidate identifier
            
        Returns:
            List of past evaluations
        """
        return self.eval_store.get_candidate_history(candidate_id)
    
    def _calculate_similarity(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        eval_record: EvaluationRecord
    ) -> float:
        """
        Calculate similarity between current candidate/job and a past evaluation.
        
        Uses simple heuristics:
        - Job title match
        - Score proximity
        - Experience level
        
        Returns:
            Similarity score 0-1
        """
        similarity = 0.0
        
        # Job similarity (40% weight)
        if eval_record.job_title.lower() == job.title.lower():
            similarity += 0.4
        elif any(word in eval_record.job_title.lower() for word in job.title.lower().split()):
            similarity += 0.2
        
        # Score proximity (30% weight)
        # Compare component scores if available
        if eval_record.component_scores:
            score_similarity = 0
            components = ['skills', 'experience', 'education', 'interviews']
            
            for comp in components:
                eval_score = eval_record.component_scores.get(comp, 0)
                # We don't have current candidate's scores yet, so we use a rough estimate
                # based on experience years for experience component
                if comp == 'experience':
                    # Rough estimate: normalize experience years to 0-100 scale
                    estimated_score = min(candidate.experience_years * 5, 100)
                    score_diff = abs(eval_score - estimated_score)
                    if score_diff < 20:
                        score_similarity += 0.25
            
            similarity += score_similarity * 0.3
        
        # Experience level similarity (30% weight)
        # Rough estimate based on years
        if hasattr(candidate, 'experience_years'):
            exp_diff = abs(candidate.experience_years - eval_record.component_scores.get('experience', 0) / 5)
            if exp_diff < 2:
                similarity += 0.3
            elif exp_diff < 5:
                similarity += 0.15
        
        return min(similarity, 1.0)
    
    def get_statistics(self) -> Dict:
        """Get memory statistics."""
        return self.eval_store.get_statistics()


# Global instance
_memory_helper: Optional[MemoryQueryHelper] = None


def get_memory_helper() -> MemoryQueryHelper:
    """Get or create global memory helper instance."""
    global _memory_helper
    if _memory_helper is None:
        _memory_helper = MemoryQueryHelper()
    return _memory_helper

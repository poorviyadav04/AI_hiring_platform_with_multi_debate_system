"""
Hybrid retrieval combining vector similarity and graph relationships.
"""

from typing import List, Dict, Optional
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent))

from rag.vector_store import VectorStore
from rag.decision_graph import DecisionGraph
from data.schemas import CandidateProfile, JobRequirements


class HybridRetriever:
    """
    Combines vector similarity search with graph-based relationship traversal.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        decision_graph: DecisionGraph
    ):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: FAISS vector store
            decision_graph: NetworkX decision graph
        """
        self.vector_store = vector_store
        self.decision_graph = decision_graph
    
    def retrieve_similar_candidates(
        self,
        query: str,
        top_k: int = 10,
        include_graph_context: bool = True
    ) -> List[Dict]:
        """
        Retrieve similar candidates using hybrid approach.
        
        Args:
            query: Search query
            top_k: Number of results
            include_graph_context: Whether to enrich with graph data
            
        Returns:
            Ranked list of candidates with context
        """
        # Step 1: Vector similarity search
        vector_results = self.vector_store.search_similar_candidates(query, top_k)
        
        if not include_graph_context:
            return vector_results
        
        # Step 2: Enrich with graph context
        enriched_results = []
        for result in vector_results:
            candidate_id = result['candidate_id']
            
            # Get history from graph
            history = self.decision_graph.get_candidate_history(candidate_id)
            
            # Get similar candidates from graph
            similar = self.decision_graph.find_similar_candidates(candidate_id, min_similarity=0.7)
            
            result['graph_context'] = {
                'application_history': history,
                'similar_candidates': similar[:3],  # Top 3 similar
                'num_applications': len(history),
                'num_hires': len([h for h in history if h.get('relationship') == 'hired_for']),
            }
            
            enriched_results.append(result)
        
        return enriched_results
    
    def retrieve_candidates_for_job(
        self,
        job: JobRequirements,
        top_k: int = 10,
        min_score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Find best candidates for a job using hybrid retrieval.
        
        Args:
            job: Job requirements
            top_k: Number of candidates to return
            min_score_threshold: Optional minimum similarity threshold
            
        Returns:
            Ranked candidates with scores
        """
        # Step 1: Vector search for semantically similar candidates
        candidates = self.vector_store.find_candidates_for_job(job, top_k * 2)
        
        # Step 2: Filter by threshold if provided
        if min_score_threshold:
            candidates = [c for c in candidates if c['similarity_score'] >= min_score_threshold]
        
        # Step 3: Re-rank using graph data
        for candidate in candidates:
            candidate_id = candidate['candidate_id']
            
            # Check if candidate has successful hires for similar roles
            history = self.decision_graph.get_candidate_history(candidate_id)
            similar_role_hires = [
                h for h in history
                if h.get('relationship') == 'hired_for' and
                h.get('level') == job.level
            ]
            
            # Boost score for proven track record
            if similar_role_hires:
                boost = 0.1 * len(similar_role_hires)
                candidate['similarity_score'] = min(1.0, candidate['similarity_score'] + boost)
                candidate['boost_reason'] = f"Hired {len(similar_role_hires)} times for {job.level} roles"
        
        # Step 4: Re-sort and limit
        candidates = sorted(candidates, key=lambda x: x['similarity_score'], reverse=True)
        return candidates[:top_k]
    
    def retrieve_past_decisions(
        self,
        job_title: str,
        department: Optional[str] = None,
        decision_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve past hiring decisions for similar roles.
        
        Args:
            job_title: Job title to match
            department: Optional department filter
            decision_type: Optional filter (hire, reject, etc.)
            
        Returns:
            List of past decisions
        """
        # Get successful hires from graph
        hires = self.decision_graph.find_successful_hires_for_role(job_title, department)
        
        if decision_type == "hire":
            return hires
        
        # For other decision types, we'd need to extend the graph query
        # For now, return hires as the primary use case
        return hires
    
    def explain_retrieval(
        self,
        query: str,
        results: List[Dict]
    ) -> str:
        """
        Generate explanation of why results were retrieved.
        
        Args:
            query: Original query
            results: Retrieved results
            
        Returns:
            Human-readable explanation
        """
        explanation = f"Retrieved {len(results)} results for query: '{query}'\n\n"
        
        if results:
            explanation += "Top Results:\n"
            for i, result in enumerate(results[:3], 1):
                score = result.get('similarity_score', 0)
                name = result.get('name', result.get('title', 'Unknown'))
                explanation += f"{i}. {name} (similarity: {score:.2%})\n"
                
                # Add context
                if 'graph_context' in result:
                    ctx = result['graph_context']
                    if ctx['num_hires'] > 0:
                        explanation += f"   Previously hired {ctx['num_hires']} time(s)\n"
        
        return explanation


__all__ = ["HybridRetriever"]

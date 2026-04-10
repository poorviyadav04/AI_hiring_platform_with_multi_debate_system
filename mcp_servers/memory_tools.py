"""
LangChain memory tools for RAG system.
Enables agents to retrieve similar candidates and past decisions.
"""

from typing import List, Optional
from langchain.tools import tool
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rag import VectorStore, DecisionGraph
from rag.hybrid_retrieval import HybridRetriever


# Global instances (will be initialized when building indices)
_vector_store: Optional[VectorStore] = None
_decision_graph: Optional[DecisionGraph] = None
_hybrid_retriever: Optional[HybridRetriever] = None


def initialize_memory_tools(
    vector_store: VectorStore,
    decision_graph: DecisionGraph
):
    """
    Initialize memory tools with vector store and decision graph.
    
    Args:
        vector_store: Initialized vector store
        decision_graph: Initialized decision graph
    """
    global _vector_store, _decision_graph, _hybrid_retriever
    
    _vector_store = vector_store
    _decision_graph = decision_graph
    _hybrid_retriever = HybridRetriever(vector_store, decision_graph)


@tool
def find_similar_candidates_tool(
    query: str,
    top_k: int = 5
) -> str:
    """
    Find candidates similar to a natural language query.
    
    Use this when you need to find candidates with specific skills, experience, or background.
    
    Args:
        query: Natural language description of desired candidate
               (e.g., "Python engineer with 5 years experience in cloud")
        top_k: Number of similar candidates to return (default: 5)
        
    Returns:
        Formatted list of similar candidates with:
        - Name and ID
        - Skills
        - Experience
        - Similarity score
        - Past hiring history (if available)
    """
    
    if not _hybrid_retriever:
        return "❌ Memory system not initialized. Please build indices first."
    
    try:
        results = _hybrid_retriever.retrieve_similar_candidates(query, top_k)
        
        if not results:
            return f"No candidates found matching query: '{query}'"
        
        output = f"Found {len(results)} similar candidates for: '{query}'\n"
        output += "=" * 70 + "\n\n"
        
        for i, candidate in enumerate(results, 1):
            output += f"{i}. {candidate['name']} (ID: {candidate['candidate_id']})\n"
            output += f"   Similarity: {candidate['similarity_score']:.1%}\n"
            output += f"   Skills: {', '.join(candidate['skills'][:5])}\n"
            output += f"   Experience: {candidate['experience_years']} years\n"
            output += f"   Education: {candidate['education']}\n"
            output += f"   Salary: ${candidate['salary_expectation']:,}\n"
            
            if 'graph_context' in candidate:
                ctx = candidate['graph_context']
                if ctx['num_applications'] > 0:
                    output += f"   History: {ctx['num_applications']} applications, {ctx['num_hires']} hired\n"
            
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error retrieving candidates: {str(e)}"


@tool
def find_past_decisions_tool(
    job_title: str,
    department: Optional[str] = None
) -> str:
    """
    Find past hiring decisions for similar roles.
    
    Use this to learn from historical hiring patterns and avoid repeating mistakes.
    
    Args:
        job_title: Job title to search for (e.g., "Software Engineer", "Data Scientist")
        department: Optional department filter (e.g., "Engineering", "Data")
        
    Returns:
        Formatted list of past hiring decisions with:
        - Hired candidate details
        - Job details
        - Hiring score
        - Key qualifications
    """
    
    if not _hybrid_retriever:
        return "❌ Memory system not initialized. Please build indices first."
    
    try:
        results = _hybrid_retriever.retrieve_past_decisions(job_title, department)
        
        if not results:
            dept_str = f" in {department}" if department else ""
            return f"No past decisions found for '{job_title}'{dept_str}"
        
        output = f"Found {len(results)} past hiring decisions for '{job_title}'\n"
        if department:
            output += f"Department: {department}\n"
        output += "=" * 70 + "\n\n"
        
        for i, decision in enumerate(results, 1):
            output += f"{i}. {decision.get('name', 'Unknown')} → {decision.get('job_title', 'Unknown Role')}\n"
            output += f"   Score: {decision.get('hire_score', 'N/A')}/100\n"
            output += f"   Experience: {decision.get('experience_years', 'N/A')} years\n"
            output += f"   Skills: {decision.get('skills', 'N/A')}\n"
            output += f"   Education: {decision.get('education', 'N/A')}\n"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error retrieving past decisions: {str(e)}"


@tool
def get_candidate_history_tool(candidate_id: str) -> str:
    """
    Get the application and hiring history for a specific candidate.
    
    Use this to see if a candidate has applied before, was hired, or rejected.
    
    Args:
        candidate_id: Candidate ID (e.g., "CAND-001")
        
    Returns:
        Formatted history of candidate's interactions including:
        - Jobs applied to
        - Hired/rejected status
        - Scores received
        - Timeline
    """
    
    if not _decision_graph:
        return "❌ Decision graph not initialized."
    
    try:
        history = _decision_graph.get_candidate_history(candidate_id)
        
        if not history:
            return f"No history found for candidate: {candidate_id}"
        
        output = f"History for Candidate {candidate_id}\n"
        output += "=" * 70 + "\n\n"
        
        for i, interaction in enumerate(history, 1):
            relationship = interaction.get('relationship', 'unknown')
            emoji = {"hired_for": "✅", "rejected_for": "❌", "applied_to": "📝"}.get(relationship, "•")
            
            output += f"{i}. {emoji} {relationship.upper().replace('_', ' ')}\n"
            output += f"   Job: {interaction.get('title', 'Unknown')}\n"
            output += f"   Level: {interaction.get('level', 'Unknown')}\n"
            output += f"   Score: {interaction.get('score', 'N/A')}/100\n"
            output += "\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error retrieving candidate history: {str(e)}"


# Tool list for easy registration
MEMORY_TOOLS = [
    find_similar_candidates_tool,
    find_past_decisions_tool,
    get_candidate_history_tool,
]


__all__ = [
    "initialize_memory_tools",
    "find_similar_candidates_tool",
    "find_past_decisions_tool",
    "get_candidate_history_tool",
    "MEMORY_TOOLS",
]

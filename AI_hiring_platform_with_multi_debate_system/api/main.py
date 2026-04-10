"""
FastAPI REST API for LLM Decision Intelligence System.

Endpoints:
- POST /evaluate - Evaluate a candidate for a job
- GET /candidates/search - Search for similar candidates
- GET /decisions/{decision_id} - Get decision details
- GET /stats - Get system statistics
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from agents.workflow import MultiAgentWorkflow
from rag import VectorStore, DecisionGraph
from rag.hybrid_retrieval import HybridRetriever
from mcp_servers.memory_tools import initialize_memory_tools
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints


# Initialize FastAPI app
app = FastAPI(
    title="LLM Decision Intelligence API",
    description="AI-powered hiring decision system with multi-agent debate",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global system components
SYSTEM = {}


# Request/Response Models
class EvaluateRequest(BaseModel):
    """Request to evaluate a candidate."""
    candidate: Dict[str, Any]
    job: Dict[str, Any]


class EvaluateResponse(BaseModel):
    """Response from candidate evaluation."""
    decision_id: str
    final_decision: str
    overall_score: float
    component_scores: Dict[str, float]
    debate_summary: List[Dict[str, str]]


class SearchRequest(BaseModel):
    """Request to search candidates."""
    query: str
    top_k: int = 5


class SearchResponse(BaseModel):
    """Response from candidate search."""
    results: List[Dict[str, Any]]
    count: int


class StatsResponse(BaseModel):
    """System statistics."""
    total_candidates: int
    total_jobs: int
    total_decisions: int
    graph_nodes: int
    graph_edges: int


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("Initializing LLM Decision Intelligence System...")
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Load constraints
    with open(data_dir / "policies.json") as f:
        policies_data = json.load(f)
    constraints = HiringConstraints(**policies_data)
    
    # Initialize RAG
    vector_store = VectorStore()
    try:
        vector_store.load()
        print("✓ Loaded vector store")
    except:
        print("⚠️  Vector store not found. Build indices first.")
    
    decision_graph = DecisionGraph()
    try:
        decision_graph.load()
        print("✓ Loaded decision graph")
    except:
        print("⚠️  Decision graph not found. Build indices first.")
    
    # Initialize components
    hybrid_retriever = HybridRetriever(vector_store, decision_graph)
    initialize_memory_tools(vector_store, decision_graph)
    workflow = MultiAgentWorkflow(constraints=constraints)
    
    # Store in global
    SYSTEM['vector_store'] = vector_store
    SYSTEM['decision_graph'] = decision_graph
    SYSTEM['hybrid_retriever'] = hybrid_retriever
    SYSTEM['workflow'] = workflow
    SYSTEM['constraints'] = constraints
    
    print("✓ System ready!")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "LLM Decision Intelligence API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/evaluate - Evaluate candidate for job",
            "/candidates/search - Search candidates",
            "/decisions/{id} - Get decision details",
            "/stats - System statistics"
        ]
    }


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_candidate(request: EvaluateRequest):
    """
    Evaluate a candidate for a job using multi-agent debate.
    
    Args:
        request: Candidate and job data
        
    Returns:
        Evaluation result with decision and scores
    """
    try:
        # Parse candidate and job
        candidate = CandidateProfile(**request.candidate)
        job = JobRequirements(**request.job)
        
        # Run evaluation
        result = SYSTEM['workflow'].run(candidate, job)
        
        # Store decision in graph
        decision_obj = SYSTEM['workflow'].create_decision_object(result)
        SYSTEM['decision_graph'].add_decision(
            decision_obj,
            candidate.candidate_id,
            job.job_id
        )
        SYSTEM['decision_graph'].save()
        
        # Build response
        debate_summary = [
            {
                'agent': msg['agent'],
                'role': msg['role'],
                'summary': msg['content'][:200] + '...'  # Truncate
            }
            for msg in result['debate_transcript']
        ]
        
        return EvaluateResponse(
            decision_id=decision_obj.decision_id,
            final_decision=result['final_decision'],
            overall_score=result['overall_score'],
            component_scores=result['component_scores'],
            debate_summary=debate_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/candidates/search", response_model=SearchResponse)
async def search_candidates(request: SearchRequest):
    """
    Search for candidates using semantic similarity.
    
    Args:
        request: Search query and parameters
        
    Returns:
        Matching candidates with scores
    """
    try:
        results = SYSTEM['hybrid_retriever'].retrieve_similar_candidates(
            request.query,
            top_k=request.top_k
        )
        
        return SearchResponse(
            results=results,
            count=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/decisions/{decision_id}")
async def get_decision(decision_id: str):
    """
    Get details of a specific decision.
    
    Args:
        decision_id: Decision ID
        
    Returns:
        Decision details
    """
    try:
        # In a real system, this would query from database
        # For now, return placeholder
        return {
            "decision_id": decision_id,
            "status": "completed",
            "message": "Decision details would be returned here"
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail="Decision not found")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get system statistics.
    
    Returns:
        System stats
    """
    try:
        graph_stats = SYSTEM['decision_graph'].get_statistics()
        
        return StatsResponse(
            total_candidates=len(SYSTEM['vector_store'].candidate_metadata),
            total_jobs=len(SYSTEM['vector_store'].job_metadata),
            total_decisions=graph_stats['decisions'],
            graph_nodes=graph_stats['total_nodes'],
            graph_edges=graph_stats['total_edges']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 70)
    print("  STARTING LLM DECISION INTELLIGENCE API")
    print("=" * 70)
    print("\nAPI will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

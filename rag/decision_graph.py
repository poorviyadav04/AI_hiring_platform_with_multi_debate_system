"""
Decision graph implementation using NetworkX.
Models relationships between candidates, jobs, and hiring decisions.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import networkx as nx

import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements, Decision


class DecisionGraph:
    """
    Graph-based storage for hiring decisions and relationships.
    
    Node types:
    - candidate: Candidate profiles
    - job: Job requirements
    - decision: Hiring decisions
    
    Edge types:
    - applied_to: Candidate → Job
    - hired_for: Candidate → Job (successful hire)
    - rejected_for: Candidate → Job (rejection)
    - similar_to: Candidate ↔ Candidate, Job ↔ Job
    - reports_to: Job → Job (organizational hierarchy)
    """
    
    def __init__(self, graph_path: Optional[Path] = None):
        """
        Initialize decision graph.
        
        Args:
            graph_path: Path to save/load graph
        """
        self.graph = nx.MultiDiGraph()  # Directed multigraph
        self.graph_path = graph_path or Path("./data/decision_graph.gml")
    
    def add_candidate(self, candidate: CandidateProfile) -> None:
        """
        Add candidate node to graph.
        
        Args:
            candidate: Candidate profile
        """
        self.graph.add_node(
            candidate.candidate_id,
            node_type="candidate",
            name=candidate.name,
            skills=",".join(candidate.skills),
            experience_years=candidate.experience_years,
            education=candidate.education,
            salary_expectation=candidate.salary_expectation,
            work_preference=candidate.work_preference,
        )
    
    def add_job(self, job: JobRequirements) -> None:
        """
        Add job node to graph.
        
        Args:
            job: Job requirements
        """
        self.graph.add_node(
            job.job_id,
            node_type="job",
            title=job.title,
            department=job.department,
            level=job.level,
            required_skills=",".join(job.required_skills),
            min_experience_years=job.min_experience_years,
            budget_min=job.budget_min,
            budget_max=job.budget_max,
        )
    
    def add_decision(
        self,
        decision: Decision,
        candidate_id: str,
        job_id: str
    ) -> None:
        """
        Add decision node and connect to candidate/job.
        
        Args:
            decision: Hiring decision
            candidate_id: Candidate ID
            job_id: Job ID
        """
        decision_id = f"decision_{candidate_id}_{job_id}"
        
        self.graph.add_node(
            decision_id,
            node_type="decision",
            final_decision=decision.final_decision,
            overall_score=decision.overall_score,
            timestamp=decision.timestamp.isoformat(),
            reasoning_summary=decision.reasoning_summary[:200],  # Truncate
        )
        
        # Connect decision to candidate and job
        self.graph.add_edge(decision_id, candidate_id, edge_type="for_candidate")
        self.graph.add_edge(decision_id, job_id, edge_type="for_job")
        
        # Connect candidate to job based on decision
        if decision.final_decision == "hire":
            self.graph.add_edge(
                candidate_id,
                job_id,
                edge_type="hired_for",
                score=decision.overall_score,
                timestamp=decision.timestamp.isoformat()
            )
        elif decision.final_decision in ["reject", "strong_reject"]:
            self.graph.add_edge(
                candidate_id,
                job_id,
                edge_type="rejected_for",
                score=decision.overall_score,
                timestamp=decision.timestamp.isoformat()
            )
        else:
            self.graph.add_edge(
                candidate_id,
                job_id,
                edge_type="applied_to",
                score=decision.overall_score,
                timestamp=decision.timestamp.isoformat()
            )
    
    def add_similarity_edge(
        self,
        node1_id: str,
        node2_id: str,
        similarity_score: float
    ) -> None:
        """
        Add similarity edge between two nodes.
        
        Args:
            node1_id: First node ID
            node2_id: Second node ID
            similarity_score: Similarity score (0-1)
        """
        self.graph.add_edge(
            node1_id,
            node2_id,
            edge_type="similar_to",
            similarity=similarity_score
        )
        self.graph.add_edge(
            node2_id,
            node1_id,
            edge_type="similar_to",
            similarity=similarity_score
        )
    
    def get_candidate_history(self, candidate_id: str) -> List[Dict]:
        """
        Get all jobs a candidate applied to/was hired for.
        
        Args:
            candidate_id: Candidate ID
            
        Returns:
            List of job interactions
        """
        if candidate_id not in self.graph:
            return []
        
        history = []
        for successor in self.graph.successors(candidate_id):
            # Get all edges between candidate and this job
            edges = self.graph.get_edge_data(candidate_id, successor)
            if edges:
                for edge_key, edge_data in edges.items():
                    if edge_data.get("edge_type") in ["hired_for", "rejected_for", "applied_to"]:
                        job_data = dict(self.graph.nodes[successor])
                        job_data["relationship"] = edge_data["edge_type"]
                        job_data["score"] = edge_data.get("score")
                        job_data["job_id"] = successor
                        history.append(job_data)
        
        return history
    
    def get_job_candidates(self, job_id: str) -> List[Dict]:
        """
        Get all candidates who applied to a job.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of candidate interactions
        """
        if job_id not in self.graph:
            return []
        
        candidates = []
        for predecessor in self.graph.predecessors(job_id):
            # Get all edges from this candidate to job
            edges = self.graph.get_edge_data(predecessor, job_id)
            if edges:
                for edge_key, edge_data in edges.items():
                    if edge_data.get("edge_type") in ["hired_for", "rejected_for", "applied_to"]:
                        candidate_data = dict(self.graph.nodes[predecessor])
                        candidate_data["relationship"] = edge_data["edge_type"]
                        candidate_data["score"] = edge_data.get("score")
                        candidate_data["candidate_id"] = predecessor
                        candidates.append(candidate_data)
        
        return candidates
    
    def find_similar_candidates(
        self,
        candidate_id: str,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Find candidates similar to given candidate.
        
        Args:
            candidate_id: Candidate ID
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar candidates
        """
        if candidate_id not in self.graph:
            return []
        
        similar = []
        for successor in self.graph.successors(candidate_id):
            edges = self.graph.get_edge_data(candidate_id, successor)
            if edges:
                for edge_key, edge_data in edges.items():
                    if edge_data.get("edge_type") == "similar_to":
                        similarity = edge_data.get("similarity", 0)
                        if similarity >= min_similarity:
                            candidate_data = dict(self.graph.nodes[successor])
                            candidate_data["similarity"] = similarity
                            candidate_data["candidate_id"] = successor
                            similar.append(candidate_data)
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)
    
    def find_successful_hires_for_role(
        self,
        job_title: str,
        department: Optional[str] = None
    ) -> List[Dict]:
        """
        Find candidates successfully hired for similar roles.
        
        Args:
            job_title: Job title to match
            department: Optional department filter
            
        Returns:
            List of successful hires
        """
        hires = []
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get("node_type") == "job":
                # Check if job matches criteria
                if job_title.lower() in node_data.get("title", "").lower():
                    if department and department.lower() not in node_data.get("department", "").lower():
                        continue
                    
                    # Get hired candidates for this job
                    for predecessor in self.graph.predecessors(node_id):
                        edges = self.graph.get_edge_data(predecessor, node_id)
                        if edges:
                            for edge_key, edge_data in edges.items():
                                if edge_data.get("edge_type") == "hired_for":
                                    candidate_data = dict(self.graph.nodes[predecessor])
                                    candidate_data["candidate_id"] = predecessor
                                    candidate_data["job_id"] = node_id
                                    candidate_data["job_title"] = node_data.get("title")
                                    candidate_data["hire_score"] = edge_data.get("score")
                                    hires.append(candidate_data)
        
        return hires
    
    def get_statistics(self) -> Dict:
        """
        Get graph statistics.
        
        Returns:
            Dictionary with stats
        """
        candidate_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "candidate"]
        job_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "job"]
        decision_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "decision"]
        
        hired_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True)
            if d.get("edge_type") == "hired_for"
        ]
        rejected_edges = [
            (u, v) for u, v, d in self.graph.edges(data=True)
            if d.get("edge_type") == "rejected_for"
        ]
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "candidates": len(candidate_nodes),
            "jobs": len(job_nodes),
            "decisions": len(decision_nodes),
            "hires": len(hired_edges),
            "rejections": len(rejected_edges),
            "hire_rate": len(hired_edges) / max(len(hired_edges) + len(rejected_edges), 1),
        }
    
    def save(self) -> None:
        """Save graph to disk."""
        print(f"Saving decision graph to {self.graph_path}...")
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        nx.write_gml(self.graph, str(self.graph_path))
        print(f"✓ Saved graph with {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
    
    def load(self) -> None:
        """Load graph from disk."""
        if self.graph_path.exists():
            print(f"Loading decision graph from {self.graph_path}...")
            self.graph = nx.read_gml(str(self.graph_path))
            print(f"✓ Loaded graph with {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        else:
            print(f"⚠️  No graph file found at {self.graph_path}")


__all__ = ["DecisionGraph"]

"""
Vector store implementation using FAISS for semantic search.
Enables finding similar candidates and job requirements.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Warning: FAISS or sentence-transformers not installed")
    print("Install with: pip install faiss-cpu sentence-transformers")

import sys
sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements


class VectorStore:
    """
    Vector store for semantic similarity search using FAISS.
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[Path] = None
    ):
        """
        Initialize vector store.
        
        Args:
            model_name: SentenceTransformer model name
            index_path: Path to save/load FAISS index
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # FAISS indices
        self.candidate_index = None
        self.job_index = None
        self.counterfactual_index = None  # NEW: For counterfactual scenarios
        
        # Metadata storage
        self.candidate_metadata = []
        self.job_metadata = []
        self.counterfactual_metadata = []  # NEW: For counterfactual metadata
        
        self.index_path = index_path or Path("./data")
        
    def _create_candidate_text(self, candidate: CandidateProfile) -> str:
        """
        Create searchable text representation of candidate.
        
        Args:
            candidate: Candidate profile
            
        Returns:
            Text for embedding
        """
        skills_text = ", ".join(candidate.skills)
        
        text = f"""Candidate: {candidate.name}
Education: {candidate.education}
Experience: {candidate.experience_years} years
Skills: {skills_text}
Work Preference: {candidate.work_preference}
Salary Expectation: ${candidate.salary_expectation:,}
Technical Score: {candidate.technical_interview_score or 'N/A'}
Behavioral Score: {candidate.behavioral_interview_score or 'N/A'}
"""
        return text
    
    def _create_job_text(self, job: JobRequirements) -> str:
        """
        Create searchable text representation of job.
        
        Args:
            job: Job requirements
            
        Returns:
            Text for embedding
        """
        required_skills_text = ", ".join(job.required_skills)
        preferred_skills_text = ", ".join(job.preferred_skills or [])
        
        text = f"""Job: {job.title}
Department: {job.department}
Level: {job.level}
Required Skills: {required_skills_text}
Preferred Skills: {preferred_skills_text}
Experience Required: {job.min_experience_years} years
Education Required: {job.required_education}
Budget: ${job.budget_min:,} - ${job.budget_max:,}
Work Mode: {job.work_mode}
"""
        return text
    
    def index_candidates(self, candidates: List[CandidateProfile]) -> None:
        """
        Index candidate profiles for similarity search.
        
        Args:
            candidates: List of candidate profiles
        """
        print(f"Indexing {len(candidates)} candidates...")
        
        # Create text representations
        texts = [self._create_candidate_text(c) for c in candidates]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        self.candidate_index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product = cosine similarity
        self.candidate_index.add(embeddings)
        
        # Store metadata
        self.candidate_metadata = [
            {
                "candidate_id": c.candidate_id,
                "name": c.name,
                "skills": c.skills,
                "experience_years": c.experience_years,
                "education": c.education,
                "salary_expectation": c.salary_expectation,
            }
            for c in candidates
        ]
        
        print(f"✓ Indexed {len(candidates)} candidates")
    
    def index_jobs(self, jobs: List[JobRequirements]) -> None:
        """
        Index job requirements for similarity search.
        
        Args:
            jobs: List of job requirements
        """
        print(f"Indexing {len(jobs)} jobs...")
        
        # Create text representations
        texts = [self._create_job_text(j) for j in jobs]
        
        # Generate embeddings
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create FAISS index
        self.job_index = faiss.IndexFlatIP(self.embedding_dim)
        self.job_index.add(embeddings)
        
        # Store metadata
        self.job_metadata = [
            {
                "job_id": j.job_id,
                "title": j.title,
                "level": j.level,
                "department": j.department,
                "required_skills": j.required_skills,
                "min_experience_years": j.min_experience_years,
            }
            for j in jobs
        ]
        
        print(f"✓ Indexed {len(jobs)} jobs")
    
    def search_similar_candidates(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar candidates using semantic search.
        
        Args:
            query: Search query (natural language or structured)
            top_k: Number of results to return
            
        Returns:
            List of similar candidates with scores
        """
        if self.candidate_index is None:
            raise ValueError("Candidate index not built. Call index_candidates() first.")
        
        # Embed query
        query_embedding = self.model.encode([query])[0].astype('float32')
        query_embedding = np.array([query_embedding])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.candidate_index.search(query_embedding, top_k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.candidate_metadata):
                result = self.candidate_metadata[idx].copy()
                result["similarity"] = float(score)  # Changed from similarity_score to similarity
                results.append(result)
        
        return results
    
    def search_similar_jobs(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar jobs using semantic search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of similar jobs with scores
        """
        if self.job_index is None:
            raise ValueError("Job index not built. Call index_jobs() first.")
        
        # Embed query
        query_embedding = self.model.encode([query])[0].astype('float32')
        query_embedding = np.array([query_embedding])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.job_index.search(query_embedding, top_k)
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.job_metadata):
                result = self.job_metadata[idx].copy()
                result["similarity"] = float(score)  # Changed from similarity_score to similarity
                results.append(result)
        
        return results
    
    def find_candidates_for_job(
        self,
        job: JobRequirements,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find candidates most similar to a job's requirements.
        
        Args:
            job: Job requirements
            top_k: Number of candidates to return
            
        Returns:
            Ranked list of candidates
        """
        job_text = self._create_job_text(job)
        return self.search_similar_candidates(job_text, top_k)
    
    def find_jobs_for_candidate(
        self,
        candidate: CandidateProfile,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find jobs most similar to a candidate's profile.
        
        Args:
            candidate: Candidate profile
            top_k: Number of jobs to return
            
        Returns:
            Ranked list of jobs
        """
        candidate_text = self._create_candidate_text(candidate)
        return self.search_similar_jobs(candidate_text, top_k)
    
    def save(self) -> None:
        """Save indices and metadata to disk."""
        print(f"Saving vector store to {self.index_path}...")
        
        # Save candidate index
        if self.candidate_index:
            faiss.write_index(
                self.candidate_index,
                str(self.index_path / "candidate_index.faiss")
            )
            with open(self.index_path / "candidate_metadata.pkl", "wb") as f:
                pickle.dump(self.candidate_metadata, f)
        
        # Save job index
        if self.job_index:
            faiss.write_index(
                self.job_index,
                str(self.index_path / "job_index.faiss")
            )
            with open(self.index_path / "job_metadata.pkl", "wb") as f:
                pickle.dump(self.job_metadata, f)
        
        # NEW: Save counterfactual index  
        if self.counterfactual_index:
            faiss.write_index(
                self.counterfactual_index,
                str(self.index_path / "counterfactual_index.faiss")
            )
            with open(self.index_path / "counterfactual_metadata.pkl", "wb") as f:
                pickle.dump(self.counterfactual_metadata, f)
        
        print("✓ Vector store saved")
    
    def load(self) -> None:
        """Load indices and metadata from disk."""
        print(f"Loading vector store from {self.index_path}...")
        
        # Load candidate index
        candidate_index_path = self.index_path / "candidate_index.faiss"
        if candidate_index_path.exists():
            self.candidate_index = faiss.read_index(str(candidate_index_path))
            with open(self.index_path / "candidate_metadata.pkl", "rb") as f:
                self.candidate_metadata = pickle.load(f)
            print(f"✓ Loaded {len(self.candidate_metadata)} candidates")
        
        # Load job index
        job_index_path = self.index_path / "job_index.faiss"
        if job_index_path.exists():
            self.job_index = faiss.read_index(str(job_index_path))
            with open(self.index_path / "job_metadata.pkl", "rb") as f:
                self.job_metadata = pickle.load(f)
            print(f"✓ Loaded {len(self.job_metadata)} jobs")
        
        # NEW: Load counterfactual index
        counterfactual_index_path = self.index_path / "counterfactual_index.faiss"
        if counterfactual_index_path.exists():
            self.counterfactual_index = faiss.read_index(str(counterfactual_index_path))
            with open(self.index_path / "counterfactual_metadata.pkl", "rb") as f:
                self.counterfactual_metadata = pickle.load(f)
            print(f"✓ Loaded {len(self.counterfactual_metadata)} counterfactuals")
    
    def index_counterfactuals(self, counterfactuals: List[Dict]) -> None:
        """
        Index counterfactual scenarios for semantic search.
        
        Args:
            counterfactuals: List of counterfactual dicts with keys:
                - candidate_id, candidate_name, job_title
                - type, change, explanation
                - impact, overall_impact
        """
        if not counterfactuals:
            return
        
        # Build text representations for embedding
        texts = []
        for cf in counterfactuals:
            # Create rich text for semantic search
            text = f"{cf['candidate_name']} for {cf['job_title']}: {cf['explanation']}"
            texts.append(text)
        
        # Generate embeddings
        embeddings = self.model.encode(texts)
        embeddings = embeddings.astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Create or extend index
        if self.counterfactual_index is None:
            self.counterfactual_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Add to index
        self.counterfactual_index.add(embeddings)
        
        # Store metadata
        for cf in counterfactuals:
            self.counterfactual_metadata.append(cf)
        
        print(f"✅ Indexed {len(counterfactuals)} counterfactuals (total: {len(self.counterfactual_metadata)})")
    
    def search_counterfactuals(
        self, 
        query: str, 
        top_k: int = 5,
        min_impact: float = None
    ) -> List[Dict]:
        """
        Search for relevant counterfactual scenarios.
        
        Args:
            query: Search query (e.g., "how to improve Python skills")
            top_k: Number of results
            min_impact: Optional minimum impact filter
            
        Returns:
            List of matching counterfactuals with similarity scores
        """
        if self.counterfactual_index is None or self.counterfactual_index.ntotal == 0:
            print("⚠️ No counterfactuals indexed yet")
            return []
        
        # Embed query
        query_embedding = self.model.encode([query])[0].astype('float32')
        query_embedding = np.array([query_embedding])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.counterfactual_index.search(
            query_embedding, 
            min(top_k * 2, self.counterfactual_index.ntotal)
        )
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.counterfactual_metadata):
                cf = self.counterfactual_metadata[idx].copy()
                cf["similarity"] = float(score)
                
                # Apply impact filter
                if min_impact is None or cf.get('overall_impact', 0) >= min_impact:
                    results.append(cf)
                
                if len(results) >= top_k:
                    break
        
        return results


__all__ = ["VectorStore"]

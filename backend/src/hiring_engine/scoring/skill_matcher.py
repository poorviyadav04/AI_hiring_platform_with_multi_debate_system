"""Semantic skill matching using sentence-transformer embeddings."""

import logging
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# --- Thresholds (single knob to tune) --------------------------------
FULL_MATCH_THRESHOLD = 0.70   # >= this → count as 1.0
PARTIAL_MATCH_THRESHOLD = 0.58  # >= this → count at actual similarity
# below PARTIAL_MATCH_THRESHOLD → no match (0.0)

MODEL_NAME = "all-MiniLM-L6-v2"

# --- Normalization map (acronyms / common aliases) --------------------
# Keep this small (~50-100). Embeddings handle the rest.
SKILL_ALIASES: Dict[str, str] = {
    # Languages
    "js": "JavaScript",
    "ts": "TypeScript",
    "py": "Python",
    "rb": "Ruby",
    "c#": "C Sharp",
    "c++": "C Plus Plus",
    "golang": "Go",
    # Frontend
    "reactjs": "React",
    "react.js": "React",
    "vuejs": "Vue",
    "vue.js": "Vue",
    "nextjs": "Next.js",
    "angularjs": "Angular",
    # Backend / Infra
    "k8s": "Kubernetes",
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "dynamo": "DynamoDB",
    "rabbitmq": "RabbitMQ",
    # AI / ML
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "llm": "Large Language Model",
    "genai": "Generative AI",
    "cv": "Computer Vision",
    "sklearn": "scikit-learn",
    "tf": "TensorFlow",
    # Cloud
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "ec2": "Amazon EC2",
    "s3": "Amazon S3",
    "lambda": "AWS Lambda",
    # DevOps
    "ci/cd": "Continuous Integration and Continuous Deployment",
    "cicd": "Continuous Integration and Continuous Deployment",
    "gh actions": "GitHub Actions",
    "iac": "Infrastructure as Code",
    # Data
    "etl": "Extract Transform Load",
    "eda": "Exploratory Data Analysis",
    "bi": "Business Intelligence",
    "sql": "Structured Query Language",
    "nosql": "NoSQL Database",
    # General
    "oop": "Object Oriented Programming",
    "fp": "Functional Programming",
    "tdd": "Test Driven Development",
    "dsa": "Data Structures and Algorithms",
    "api": "Application Programming Interface",
    "rest": "REST API",
    "graphql": "GraphQL API",
    "ui": "User Interface",
    "ux": "User Experience",
    "qa": "Quality Assurance",
    "pm": "Project Management",
    "agile": "Agile Methodology",
    "scrum": "Scrum Methodology",
    "sre": "Site Reliability Engineering",
}


class SkillMatcher:
    """Semantic skill matcher using sentence-transformer embeddings."""

    def __init__(self, model_name: str = MODEL_NAME):
        start = time.time()
        self._model = SentenceTransformer(model_name)
        elapsed = time.time() - start
        logger.info("SkillMatcher loaded model '%s' in %.1fs", model_name, elapsed)

    def normalize(self, skill: str) -> str:
        """Normalize a skill string via alias lookup."""
        key = skill.strip().lower()
        return SKILL_ALIASES.get(key, skill.strip())

    def _embed(self, skills: List[str]) -> np.ndarray:
        """Embed skill strings with context prefix for better similarity."""
        # Short keywords embed poorly in sentence-transformers.
        # A domain-neutral prefix boosts similarity for related skills
        # without inflating scores across unrelated domains.
        normalized = [
            f"Professional skill: {self.normalize(s)}"
            for s in skills
        ]
        return self._model.encode(normalized, convert_to_numpy=True)

    def similarity_matrix(
        self, jd_skills: List[str], resume_skills: List[str]
    ) -> np.ndarray:
        """Return a (len(jd_skills), len(resume_skills)) cosine similarity matrix."""
        jd_emb = self._embed(jd_skills)
        resume_emb = self._embed(resume_skills)
        return cosine_similarity(jd_emb, resume_emb)

    def match_skills(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: Optional[List[str]] = None,
    ) -> Dict:
        """
        Match candidate skills against required/preferred using embeddings.

        Returns a dict with:
          - required_matches: list of {skill, best_match, similarity, match_type}
          - preferred_matches: same shape
          - missing_required: skills below PARTIAL_MATCH_THRESHOLD
          - partially_matched: skills between PARTIAL and FULL thresholds
          - fully_matched: skills above FULL threshold
          - required_score: 0-100
          - preferred_score: 0-100
        """
        if not required_skills:
            raise ValueError("required_skills cannot be empty")
        if not candidate_skills:
            return self._empty_result(required_skills, preferred_skills)

        required_matches = self._match_list(candidate_skills, required_skills)
        required_score = self._compute_score(required_matches)

        preferred_matches = []
        preferred_score = 0.0
        if preferred_skills:
            preferred_matches = self._match_list(candidate_skills, preferred_skills)
            preferred_score = self._compute_score(preferred_matches)

        missing = [m for m in required_matches if m["match_type"] == "none"]
        partial = [m for m in required_matches if m["match_type"] == "partial"]
        full = [m for m in required_matches if m["match_type"] == "full"]

        return {
            "required_matches": required_matches,
            "preferred_matches": preferred_matches,
            "missing_required": [m["skill"] for m in missing],
            "partially_matched": [
                {"skill": m["skill"], "matched_to": m["best_match"], "similarity": m["similarity"]}
                for m in partial
            ],
            "fully_matched": [
                {"skill": m["skill"], "matched_to": m["best_match"], "similarity": m["similarity"]}
                for m in full
            ],
            "required_score": round(required_score, 2),
            "preferred_score": round(preferred_score, 2),
        }

    def _match_list(
        self, candidate_skills: List[str], target_skills: List[str]
    ) -> List[Dict]:
        """For each target skill, find best matching candidate skill.

        Uses greedy one-to-one assignment: once a candidate skill is claimed
        by a higher-similarity pair, it cannot be reused by another target.
        """
        matrix = self.similarity_matrix(target_skills, candidate_skills)
        used_candidate_indices: set = set()
        results: List[Dict] = []

        # Build all (similarity, target_idx, candidate_idx) pairs, sort desc
        pairs = []
        for i in range(len(target_skills)):
            for j in range(len(candidate_skills)):
                pairs.append((float(matrix[i][j]), i, j))
        pairs.sort(reverse=True)

        # Greedy assignment: highest similarity first
        assigned_targets: Dict[int, Tuple[int, float]] = {}
        for sim, t_idx, c_idx in pairs:
            if t_idx in assigned_targets or c_idx in used_candidate_indices:
                continue
            assigned_targets[t_idx] = (c_idx, sim)
            used_candidate_indices.add(c_idx)

        for i, skill in enumerate(target_skills):
            if i in assigned_targets:
                c_idx, best_sim = assigned_targets[i]
                best_match = candidate_skills[c_idx]
            else:
                best_sim = 0.0
                best_match = ""

            if best_sim >= FULL_MATCH_THRESHOLD:
                match_type = "full"
                effective_score = 1.0
            elif best_sim >= PARTIAL_MATCH_THRESHOLD:
                match_type = "partial"
                effective_score = best_sim
            else:
                match_type = "none"
                effective_score = 0.0

            results.append({
                "skill": skill,
                "best_match": best_match,
                "similarity": round(best_sim, 3),
                "match_type": match_type,
                "effective_score": round(effective_score, 3),
            })

        return results

    def _compute_score(self, matches: List[Dict]) -> float:
        """Average of effective scores → 0-100."""
        if not matches:
            return 0.0
        total = sum(m["effective_score"] for m in matches)
        return (total / len(matches)) * 100

    def _empty_result(
        self, required_skills: List[str], preferred_skills: Optional[List[str]]
    ) -> Dict:
        """Return zero-score result when candidate has no skills."""
        missing = [
            {"skill": s, "best_match": "", "similarity": 0.0,
             "match_type": "none", "effective_score": 0.0}
            for s in required_skills
        ]
        return {
            "required_matches": missing,
            "preferred_matches": [],
            "missing_required": required_skills,
            "partially_matched": [],
            "fully_matched": [],
            "required_score": 0.0,
            "preferred_score": 0.0,
        }


__all__ = ["SkillMatcher", "FULL_MATCH_THRESHOLD", "PARTIAL_MATCH_THRESHOLD"]

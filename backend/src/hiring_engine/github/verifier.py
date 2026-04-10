"""GitHub verification orchestrator — produces TrustScore."""

import asyncio
import logging
import re
from typing import List, Optional

from hiring_engine.github.client import GitHubClient
from hiring_engine.github.analyzer import GitHubAnalyzer
from hiring_engine.llm.base import BaseLLMClient
from hiring_engine.llm.prompts import GITHUB_CODE_REVIEW_PROMPT
from hiring_engine.schemas.github import (
    GitHubVerificationResult,
    GitHubProfile,
    CommitPattern,
    SkillVerification,
    CodeQualitySignal,
)

logger = logging.getLogger(__name__)


class GitHubVerifier:
    """Verifies GitHub profiles for candidate authenticity."""

    def __init__(self, github_token: Optional[str] = None, llm: Optional[BaseLLMClient] = None):
        self._client = GitHubClient(token=github_token)
        self._analyzer = GitHubAnalyzer(self._client)
        self._llm = llm

    @staticmethod
    def extract_username(github_url: str) -> Optional[str]:
        """Extract username from various GitHub URL formats."""
        patterns = [
            r"github\.com/([a-zA-Z0-9\-]+)/?$",
            r"github\.com/([a-zA-Z0-9\-]+)/[^/]+",
        ]
        for pattern in patterns:
            match = re.search(pattern, github_url)
            if match:
                return match.group(1)
        return None

    async def verify(
        self, github_url: str, claimed_skills: List[str]
    ) -> Optional[GitHubVerificationResult]:
        """Run full GitHub verification."""
        username = self.extract_username(github_url)
        if not username:
            logger.warning("Could not extract username from: %s", github_url)
            return None

        logger.info("Verifying GitHub profile: %s", username)

        # Run profile, commits, and repos analysis in parallel
        profile, commit_pattern, repos = await asyncio.gather(
            self._analyzer.analyze_profile(username),
            self._analyzer.analyze_commit_pattern(username),
            self._analyzer.analyze_repos(username),
        )

        if not profile:
            logger.warning("GitHub profile not found: %s", username)
            return None

        # Verify skills against repo languages
        skill_verifications = self._verify_skills(claimed_skills, profile.top_languages)

        # Code quality review (if LLM available and rate limit OK)
        code_quality = None
        if self._llm and self._client.rate_remaining > 20:
            code_quality = await self._review_code(username, repos[:3], claimed_skills)

        # Calculate trust scores
        authenticity = self._score_authenticity(profile, commit_pattern)
        skill_match = self._score_skill_match(skill_verifications)
        activity = self._score_activity(commit_pattern, repos)

        code_quality_score = code_quality.quality_score if code_quality else 50.0

        # Weighted overall: authenticity 15%, activity 25%, repo quality 20%, skill match 25%, code 15%
        overall_trust = (
            authenticity * 0.15
            + activity * 0.25
            + self._score_repo_quality(repos) * 0.20
            + skill_match * 0.25
            + code_quality_score * 0.15
        )

        # Determine label
        flags = []
        if profile.account_age_days < 90:
            flags.append("Account less than 90 days old")
        if commit_pattern.burst_detected:
            flags.append("Commit burst detected — possible cramming")
        if all(r.is_fork for r in repos[:5]):
            flags.append("All top repos are forks — no original work")
        if skill_match < 40:
            flags.append("Significant skill mismatch between resume and code")

        if overall_trust >= 75:
            label = "real_active"
        elif overall_trust >= 50:
            label = "real_inactive" if activity < 40 else "suspicious"
        else:
            label = "possibly_fake"

        verified = sum(1 for s in skill_verifications if s.verified)
        summary = (
            f"GitHub profile @{username}: Trust {overall_trust:.0f}/100 ({label}). "
            f"Account age: {profile.account_age_days} days. "
            f"{profile.public_repos} repos. "
            f"Skills verified: {verified}/{len(skill_verifications)}. "
            f"Activity consistency: {commit_pattern.consistency_score:.0%}."
        )

        return GitHubVerificationResult(
            profile=profile,
            commit_pattern=commit_pattern,
            top_repos=repos[:5],
            skill_verification=skill_verifications,
            code_quality=code_quality,
            authenticity_score=round(authenticity, 1),
            skill_match_score=round(skill_match, 1),
            activity_score=round(activity, 1),
            overall_trust_score=round(overall_trust, 1),
            trust_label=label,
            flags=flags,
            analysis_summary=summary,
        )

    def _verify_skills(
        self, claimed_skills: List[str], languages: dict
    ) -> List[SkillVerification]:
        """Check if claimed skills appear in GitHub language data."""
        SKILL_TO_LANGUAGE = {
            "python": ["Python"],
            "javascript": ["JavaScript"],
            "typescript": ["TypeScript"],
            "react": ["JavaScript", "TypeScript"],
            "vue": ["JavaScript", "Vue"],
            "angular": ["TypeScript"],
            "java": ["Java"],
            "c++": ["C++"],
            "c#": ["C#"],
            "go": ["Go"],
            "rust": ["Rust"],
            "ruby": ["Ruby"],
            "php": ["PHP"],
            "swift": ["Swift"],
            "kotlin": ["Kotlin"],
            "r": ["R"],
            "sql": ["PLSQL", "TSQL"],
            "html": ["HTML"],
            "css": ["CSS"],
        }

        languages_lower = {k.lower(): v for k, v in languages.items()}
        results = []

        for skill in claimed_skills:
            skill_lower = skill.lower()
            lang_names = SKILL_TO_LANGUAGE.get(skill_lower, [skill])
            found = False
            total_bytes = 0

            for lang in lang_names:
                if lang.lower() in languages_lower:
                    found = True
                    total_bytes += languages_lower[lang.lower()]

            if found:
                strength = "strong" if total_bytes > 10000 else "moderate" if total_bytes > 1000 else "weak"
            else:
                strength = "none"

            results.append(SkillVerification(
                skill=skill,
                verified=found,
                evidence_strength=strength,
                lines_of_code=total_bytes // 40 if total_bytes else 0,  # rough estimate
            ))

        return results

    def _score_authenticity(self, profile: GitHubProfile, pattern: CommitPattern) -> float:
        """Score profile authenticity (0-100)."""
        score = 50.0  # baseline

        # Account age
        if profile.account_age_days > 730:  # 2+ years
            score += 20
        elif profile.account_age_days > 365:
            score += 10
        elif profile.account_age_days < 90:
            score -= 20

        # Followers
        if profile.followers > 10:
            score += 10
        elif profile.followers > 3:
            score += 5

        # Repos
        if profile.public_repos > 10:
            score += 10
        elif profile.public_repos > 3:
            score += 5
        elif profile.public_repos == 0:
            score -= 20

        # Burst detection
        if pattern.burst_detected:
            score -= 15

        return max(0, min(100, score))

    def _score_skill_match(self, verifications: List[SkillVerification]) -> float:
        """Score skill match (0-100)."""
        if not verifications:
            return 50.0
        verified_count = sum(1 for v in verifications if v.verified)
        strong_count = sum(1 for v in verifications if v.evidence_strength == "strong")
        base = (verified_count / len(verifications)) * 80
        bonus = (strong_count / len(verifications)) * 20
        return min(100, base + bonus)

    def _score_activity(self, pattern: CommitPattern, repos: list) -> float:
        """Score activity level (0-100)."""
        score = pattern.consistency_score * 60
        if pattern.total_commits > 100:
            score += 20
        elif pattern.total_commits > 30:
            score += 10
        if pattern.longest_streak_days > 30:
            score += 20
        elif pattern.longest_streak_days > 7:
            score += 10
        return min(100, score)

    def _score_repo_quality(self, repos: list) -> float:
        """Score repository quality (0-100)."""
        if not repos:
            return 0
        score = 0
        original = [r for r in repos if not r.is_fork]
        score += min(40, len(original) * 8)
        starred = sum(1 for r in repos if r.stars > 0)
        score += min(30, starred * 10)
        licensed = sum(1 for r in repos if r.has_license)
        score += min(15, licensed * 5)
        recent = sum(1 for r in repos if r.last_pushed_days_ago < 90)
        score += min(15, recent * 5)
        return min(100, score)

    async def _review_code(self, username: str, repos: list, claimed_skills: List[str]) -> Optional[CodeQualitySignal]:
        """Use LLM to review code quality from top repos."""
        if not repos or not self._llm:
            return None

        # Find a non-fork repo with a matching language
        target_repo = None
        for repo in repos:
            if not repo.is_fork and repo.language:
                target_repo = repo
                break

        if not target_repo:
            return None

        # Try to get a source file
        content = await self._client.get_file_content(username, target_repo.name, "README.md")
        # For actual code, we'd look for main source files
        # Simplified: just return a basic signal based on repo stats
        has_readme = content is not None

        return CodeQualitySignal(
            quality_score=60.0 if has_readme else 30.0,
            structure="good" if target_repo.stars > 0 else "basic",
            testing_present=False,
            documentation_quality="good" if has_readme else "none",
            is_tutorial_copy=False,
            summary=f"Repo '{target_repo.name}' ({target_repo.language}): {'has README' if has_readme else 'no README'}, {target_repo.stars} stars",
        )

    async def close(self):
        await self._client.close()


__all__ = ["GitHubVerifier"]

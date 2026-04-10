"""GitHub profile analyzer."""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from hiring_engine.github.client import GitHubClient
from hiring_engine.schemas.github import (
    GitHubProfile,
    CommitPattern,
    RepoAnalysis,
)

logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    """Analyzes GitHub profiles for authenticity and activity patterns."""

    def __init__(self, client: GitHubClient):
        self._client = client

    async def analyze_profile(self, username: str) -> Optional[GitHubProfile]:
        """Get basic profile information."""
        user = await self._client.get_user(username)
        if not user:
            return None

        created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
        age_days = (datetime.now(timezone.utc) - created).days

        repos = await self._client.get_repos(username) or []

        # Aggregate languages across repos
        all_languages = {}
        for repo in repos[:10]:  # Top 10 repos
            langs = await self._client.get_repo_languages(username, repo["name"])
            if langs:
                for lang, bytes_count in langs.items():
                    all_languages[lang] = all_languages.get(lang, 0) + bytes_count

        return GitHubProfile(
            username=username,
            account_age_days=age_days,
            public_repos=user.get("public_repos", 0),
            followers=user.get("followers", 0),
            following=user.get("following", 0),
            top_languages=dict(sorted(all_languages.items(), key=lambda x: x[1], reverse=True)[:10]),
            bio=user.get("bio"),
            company=user.get("company"),
            hireable=user.get("hireable"),
        )

    async def analyze_commit_pattern(self, username: str) -> CommitPattern:
        """Analyze commit patterns across repositories."""
        repos = await self._client.get_repos(username) or []

        total_commits = 0
        commit_dates = []

        for repo in repos[:5]:  # Analyze top 5 repos
            if repo.get("fork"):
                continue
            commits = await self._client.get_repo_commits(username, repo["name"], per_page=50)
            if not commits:
                continue
            total_commits += len(commits)

            for commit in commits:
                date_str = commit.get("commit", {}).get("author", {}).get("date", "")
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_dates.append(dt)
                    except ValueError:
                        pass

        if not commit_dates:
            return CommitPattern(total_commits=0)

        commit_dates.sort()

        # Calculate weekly distribution (last 52 weeks)
        now = datetime.now(timezone.utc)
        weekly_counts = {}
        for dt in commit_dates:
            week_num = (now - dt).days // 7
            if week_num < 52:
                weekly_counts[week_num] = weekly_counts.get(week_num, 0) + 1

        active_weeks = len(weekly_counts)
        consistency_score = min(1.0, active_weeks / 26)  # 26+ weeks = perfect

        # Detect burst: if >50% of commits in a single week
        max_week_commits = max(weekly_counts.values()) if weekly_counts else 0
        total_recent = sum(weekly_counts.values())
        burst_detected = total_recent > 0 and (max_week_commits / total_recent) > 0.5

        # Longest streak
        streak_days = 0
        if len(commit_dates) > 1:
            current_streak = 1
            for i in range(1, len(commit_dates)):
                diff = (commit_dates[i] - commit_dates[i - 1]).days
                if diff <= 7:
                    current_streak += 1
                else:
                    streak_days = max(streak_days, current_streak * 7)
                    current_streak = 1
            streak_days = max(streak_days, current_streak * 7)

        return CommitPattern(
            total_commits=total_commits,
            active_weeks=active_weeks,
            consistency_score=round(consistency_score, 2),
            burst_detected=burst_detected,
            longest_streak_days=streak_days,
            avg_commits_per_active_week=round(total_recent / max(active_weeks, 1), 1),
        )

    async def analyze_repos(self, username: str, limit: int = 10) -> List[RepoAnalysis]:
        """Analyze top repositories."""
        repos = await self._client.get_repos(username) or []
        results = []

        for repo in repos[:limit]:
            now = datetime.now(timezone.utc)
            pushed_at = repo.get("pushed_at", "")
            days_ago = 0
            if pushed_at:
                try:
                    pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                    days_ago = (now - pushed).days
                except ValueError:
                    pass

            results.append(RepoAnalysis(
                name=repo["name"],
                language=repo.get("language"),
                stars=repo.get("stargazers_count", 0),
                forks=repo.get("forks_count", 0),
                has_readme=True,  # Assume if repo exists
                has_license=repo.get("license") is not None,
                is_fork=repo.get("fork", False),
                last_pushed_days_ago=days_ago,
                description=repo.get("description"),
            ))

        return results


__all__ = ["GitHubAnalyzer"]

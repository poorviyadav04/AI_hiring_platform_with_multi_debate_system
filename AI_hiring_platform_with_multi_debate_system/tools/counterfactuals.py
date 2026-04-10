"""
Counterfactual Explanation Engine.

Generates "what-if" scenarios to explain how changes to candidate
attributes would affect hiring scores and decisions.
"""

from typing import List, Dict, Any, Optional
from copy import deepcopy
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data.schemas import CandidateProfile, JobRequirements
from tools.scoring import (
    calculate_skill_match,
    calculate_experience_score,
    calculate_education_score,
    calculate_overall_score
)


class CounterfactualGenerator:
    """
    Generates counterfactual explanations for hiring decisions.
    """
    
    def __init__(self):
        """Initialize counterfactual generator."""
        pass
    
    def generate_skill_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactuals for missing skills.
        
        Shows: "If candidate had skill X, score would increase by Y points"
        
        Args:
            candidate: Current candidate
            job: Job requirements
            top_k: Number of counterfactuals to generate
            
        Returns:
            List of counterfactual scenarios
        """
        # Get current score
        current_result = calculate_skill_match(
            candidate.skills,
            job.required_skills,
            job.preferred_skills
        )
        current_score = current_result['overall_score']
        
        # Find missing skills
        missing_skills = [s for s in job.required_skills if s not in candidate.skills]
        
        counterfactuals = []
        
        for skill in missing_skills[:top_k]:
            # Create hypothetical candidate with this skill
            hypothetical_skills = candidate.skills + [skill]
            
            # Calculate new score
            new_result = calculate_skill_match(
                hypothetical_skills,
                job.required_skills,
                job.preferred_skills
            )
            new_score = new_result['overall_score']
            
            # Calculate impact
            impact = new_score - current_score
            
            counterfactuals.append({
                'type': 'skill',
                'change': f"Add skill: {skill}",
                'current_score': current_score,
                'new_score': new_score,
                'impact': impact,
                'impact_percentage': (impact / 100) * 100,
                'explanation': f"If candidate had {skill} skill, skill score would increase from {current_score:.1f} to {new_score:.1f} (+{impact:.1f} points)"
            })
        
        # Sort by impact (highest first)
        counterfactuals.sort(key=lambda x: x['impact'], reverse=True)
        
        return counterfactuals
    
    def generate_experience_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        scenarios: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactuals for experience levels.
        
        Shows: "If candidate had N years experience, score would be X"
        
        Args:
            candidate: Current candidate
            job: Job requirements
            scenarios: Years to test (default: [+1, +2, +3, +5, min_required])
            
        Returns:
            List of counterfactual scenarios
        """
        # Get current score
        current_result = calculate_experience_score(
            candidate.experience_years,
            job.min_experience_years,
            job.level
        )
        current_score = current_result['score']
        
        if scenarios is None:
            # Default scenarios
            scenarios = [
                candidate.experience_years + 1,
                candidate.experience_years + 2,
                candidate.experience_years + 3,
                candidate.experience_years + 5,
                job.min_experience_years  # What if met minimum?
            ]
            # Remove duplicates and sort
            scenarios = sorted(list(set(scenarios)))
        
        counterfactuals = []
        
        for years in scenarios:
            if years <= candidate.experience_years:
                continue  # Skip if not an increase
            
            # Calculate new score with hypothetical experience
            new_result = calculate_experience_score(
                years,
                job.min_experience_years,
                job.level
            )
            new_score = new_result['score']
            
            # Calculate impact
            impact = new_score - current_score
            years_diff = years - candidate.experience_years
            
            counterfactuals.append({
                'type': 'experience',
                'change': f"Add {years_diff:.0f} years experience (total: {years:.0f} years)",
                'years': years,  # Add this for easy access
                'current_score': current_score,
                'new_score': new_score,
                'impact': impact,
                'impact_percentage': (impact / 100) * 100,
                'meets_minimum': years >= job.min_experience_years,
                'explanation': f"If candidate had {years:.0f} years experience (+{years_diff:.0f} years), experience score would increase from {current_score:.1f} to {new_score:.1f} (+{impact:.1f} points)"
            })
        
        return counterfactuals
    
    def generate_education_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactuals for education levels.
        
        Shows: "If candidate had higher degree, score would be X"
        
        Args:
            candidate: Current candidate
            job: Job requirements
            
        Returns:
            List of counterfactual scenarios
        """
        # Education hierarchy
        education_levels = [
            "High School",
            "Bachelor",
            "Master",
            "PhD"
        ]
        
        # Get current score
        current_result = calculate_education_score(
            candidate.education,
            job.required_education
        )
        current_score = current_result['score']
        
        # Find current level
        try:
            current_idx = education_levels.index(candidate.education)
        except ValueError:
            current_idx = 0
        
        counterfactuals = []
        
        # Try higher education levels
        for i in range(current_idx + 1, len(education_levels)):
            higher_ed = education_levels[i]
            
            # Calculate new score with hypothetical education
            new_result = calculate_education_score(
                higher_ed,
                job.required_education
            )
            new_score = new_result['score']
            
            # Calculate impact
            impact = new_score - current_score
            
            counterfactuals.append({
                'type': 'education',
                'change': f"Upgrade to {higher_ed}",
                'current_score': current_score,
                'new_score': new_score,
                'impact': impact,
                'impact_percentage': (impact / 100) * 100,
                'explanation': f"If candidate had {higher_ed} degree (vs {candidate.education}), education score would increase from {current_score:.1f} to {new_score:.1f} (+{impact:.1f} points)"
            })
        
        return counterfactuals
    
    def generate_salary_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        scenarios: List[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactuals for salary expectations.
        
        Shows: "If candidate's salary expectation was $X, budget fit would be Y"
        
        Args:
            candidate: Current candidate
            job: Job requirements
            scenarios: Salaries to test
            
        Returns:
            List of counterfactual scenarios
        """
        current_salary = candidate.salary_expectation
        
        if scenarios is None:
            # Default scenarios around budget
            scenarios = [
                int(job.budget_max * 0.7),  # 30% under budget
                int(job.budget_max * 0.8),  # 20% under
                int(job.budget_max * 0.9),  # 10% under
                job.budget_max,              # At budget
                current_salary              # Current
            ]
            scenarios = sorted(list(set(scenarios)))
        
        counterfactuals = []
        
        for salary in scenarios:
            if salary == current_salary:
                continue
            
            # Determine fit
            within_budget = salary <= job.budget_max
            margin = job.budget_max - salary
            margin_pct = (margin / job.budget_max) * 100
            
            counterfactuals.append({
                'type': 'salary',
                'change': f"Salary expectation: ${salary:,}",
                'current_salary': current_salary,
                'new_salary': salary,
                'difference': salary - current_salary,
                'within_budget': within_budget,
                'budget_margin': margin,
                'budget_margin_percentage': margin_pct,
                'explanation': f"If candidate's salary expectation was ${salary:,} (vs ${current_salary:,}), budget margin would be ${margin:,} ({margin_pct:.1f}% of budget)"
            })
        
        return counterfactuals
    
    def generate_overall_counterfactuals(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Generate comprehensive counterfactual analysis.
        
        Shows impact on overall score from all types of changes.
        
        Args:
            candidate: Current candidate
            job: Job requirements
            top_k: Number of top counterfactuals to return
            
        Returns:
            Comprehensive counterfactual analysis
        """
        # Get current overall score
        current_overall = calculate_overall_score(candidate, job)
        current_score = current_overall['overall_score']
        
        all_counterfactuals = []
        
        # Skills
        skill_cfs = self.generate_skill_counterfactuals(candidate, job, top_k=5)
        for cf in skill_cfs:
            # Calculate new overall score
            hypothetical = deepcopy(candidate)
            # Extract skill name from change description
            skill = cf['change'].replace("Add skill: ", "")
            hypothetical.skills.append(skill)
            new_overall = calculate_overall_score(hypothetical, job)
            
            all_counterfactuals.append({
                **cf,
                'overall_current': current_score,
                'overall_new': new_overall['overall_score'],
                'overall_impact': new_overall['overall_score'] - current_score
            })
        
        # Experience
        exp_cfs = self.generate_experience_counterfactuals(candidate, job, scenarios=[
            candidate.experience_years + 1,
            candidate.experience_years + 2,
            job.min_experience_years
        ])
        for cf in exp_cfs:
            # Use the years from metadata instead of parsing
            total_years = cf.get('years', candidate.experience_years)
            
            hypothetical = deepcopy(candidate)
            hypothetical.experience_years = total_years
            new_overall = calculate_overall_score(hypothetical, job)
            
            all_counterfactuals.append({
                **cf,
                'overall_current': current_score,
                'overall_new': new_overall['overall_score'],
                'overall_impact': new_overall['overall_score'] - current_score
            })
        
        # Education
        edu_cfs = self.generate_education_counterfactuals(candidate, job)
        for cf in edu_cfs:
            # Extract education level
            new_ed = cf['change'].replace("Upgrade to ", "")
            
            new_overall = calculate_overall_score(candidate, job)
            # Just adjust the education component
            edu_impact = cf['impact']
            overall_impact = edu_impact * 0.15  # Education is 15% of overall
            
            all_counterfactuals.append({
                **cf,
                'overall_current': current_score,
                'overall_new': current_score + overall_impact,
                'overall_impact': overall_impact
            })
        
        # Sort by overall impact
        all_counterfactuals.sort(key=lambda x: x['overall_impact'], reverse=True)
        
        return {
            'current_overall_score': current_score,
            'counterfactuals': all_counterfactuals[:top_k],
            'summary': {
                'total_scenarios': len(all_counterfactuals),
                'highest_impact': all_counterfactuals[0] if all_counterfactuals else None,
                'actionable_count': len([cf for cf in all_counterfactuals if cf['overall_impact'] > 5])
            }
        }
    
    def get_actionable_feedback(
        self,
        candidate: CandidateProfile,
        job: JobRequirements,
        score_threshold: float = 75.0
    ) -> List[str]:
        """
        Generate actionable feedback for candidate improvement.
        
        Args:
            candidate: Current candidate
            job: Job requirements
            score_threshold: Target score to reach
            
        Returns:
            List of actionable recommendations
        """
        current_overall = calculate_overall_score(candidate, job)
        current_score = current_overall['overall_score']
        
        if current_score >= score_threshold:
            return [f"✅ Already meets threshold ({current_score:.1f}/{score_threshold})"]
        
        gap = score_threshold - current_score
        
        recommendations = []
        recommendations.append(f"Current score: {current_score:.1f}/100 (need {gap:.1f} more points to reach {score_threshold})")
        
        # Get counterfactuals
        analysis = self.generate_overall_counterfactuals(candidate, job, top_k=5)
        
        recommendations.append("\n📈 Top ways to improve score:\n")
        
        for i, cf in enumerate(analysis['counterfactuals'][:5], 1):
            if cf['overall_impact'] > 0:
                recommendations.append(
                    f"{i}. {cf['change']} → +{cf['overall_impact']:.1f} points overall"
                )
        
        return recommendations


__all__ = ["CounterfactualGenerator"]

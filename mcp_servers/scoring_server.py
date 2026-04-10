"""
Scoring Server - MCP Server for candidate scoring tools.

Exposes scoring functionality via MCP protocol for tool discovery.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_servers.mcp_base import (
    MCPServer, ToolParameter, ToolParameterType
)
from tools.scoring import (
    calculate_skill_match,
    calculate_experience_score,
    calculate_overall_score
)
from data.schemas import CandidateProfile, JobRequirements


class ScoringServer(MCPServer):
    """
    MCP Server for candidate scoring tools.
    
    Provides:
    - Skills matching
    - Experience evaluation
    - Education assessment
    - Interview scoring
    - Overall score calculation
    """
    
    def __init__(self):
        """Initialize scoring server."""
        super().__init__(
            name="scoring",
            description="Candidate evaluation and scoring tools"
        )
        self.register_tools()
    
    def register_tools(self):
        """Register all scoring tools."""
        
        # Tool 1: Calculate skills score
        self.register_tool(
            name="calculate_skills_score",
            handler=self._calculate_skills_score,
            description="Calculate candidate's skills match score",
            parameters=[
                ToolParameter(
                    name="candidate_skills",
                    param_type=ToolParameterType.ARRAY,
                    description="List of candidate skills"
                ),
                ToolParameter(
                    name="required_skills",
                    param_type=ToolParameterType.ARRAY,
                    description="List of required job skills"
                ),
                ToolParameter(
                    name="preferred_skills",
                    param_type=ToolParameterType.ARRAY,
                    description="List of preferred skills",
                    required=False,
                    default=[]
                )
            ],
            version="1.0.0"
        )
        
        # Tool 2: Calculate experience score
        self.register_tool(
            name="calculate_experience_score",
            handler=self._calculate_experience_score,
            description="Calculate candidate's experience relevance score",
            parameters=[
                ToolParameter(
                    name="experience_years",
                    param_type=ToolParameterType.FLOAT,
                    description="Years of experience"
                ),
                ToolParameter(
                    name="min_experience_required",
                    param_type=ToolParameterType.FLOAT,
                    description="Minimum years required"
                )
            ],
            version="1.0.0"
        )
        
        # Tool 3: Calculate interview score
        self.register_tool(
            name="calculate_interview_score",
            handler=self._calculate_interview_score,
            description="Calculate combined interview performance score",
            parameters=[
                ToolParameter(
                    name="technical_score",
                    param_type=ToolParameterType.FLOAT,
                    description="Technical interview score (0-100)"
                ),
                ToolParameter(
                    name="behavioral_score",
                    param_type=ToolParameterType.FLOAT,
                    description="Behavioral interview score (0-100)"
                )
            ],
            version="1.0.0"
        )
        
        # Tool 4: Calculate overall score
        self.register_tool(
            name="calculate_overall_score",
            handler=self._calculate_overall_score,
            description="Calculate weighted overall candidate score",
            parameters=[
                ToolParameter(
                    name="component_scores",
                    param_type=ToolParameterType.OBJECT,
                    description="Dictionary of component scores (skills, experience, etc.)"
                )
            ],
            version="1.0.0"
        )
    
    def _calculate_skills_score(self, candidate_skills, required_skills, preferred_skills=None):
        """Wrapper for skills score calculation."""
        return calculate_skills_score(
            candidate_skills,
            required_skills,
            preferred_skills or []
        )
    
    def _calculate_experience_score(self, experience_years, min_experience_required):
        """Wrapper for experience score calculation."""
        return calculate_experience_score(experience_years, min_experience_required)
    
    def _calculate_interview_score(self, technical_score, behavioral_score):
        """Wrapper for interview score calculation."""
        return calculate_interview_score(technical_score, behavioral_score)
    
    def _calculate_overall_score(self, component_scores):
        
        # NEW: Full scoring with detailed breakdown
        self.register_tool(
            name="calculate_overall_score_full",
            handler=self._calculate_overall_score_full,
            description="Calculate overall score with full component breakdown",
            parameters=[
                ToolParameter(
                    name="candidate",
                    param_type=ToolParameterType.OBJECT, # Changed type to param_type
                    description="Candidate profile",
                    required=True
                ),
                ToolParameter(
                    name="job",
                    param_type=ToolParameterType.OBJECT, # Changed type to param_type
                    description="Job requirements",
                    required=True
                )
            ],
            version="1.0.0" # Added version
        )
    
    def _calculate_skills_score(self, **kwargs) -> float:
        """Calculate skills match score."""
        candidate_skills = kwargs.get('candidate_skills', [])
        required_skills = kwargs.get('required_skills', [])
        preferred_skills = kwargs.get('preferred_skills', [])
        
        from tools import scoring as scoring_module
        return scoring_module.calculate_skills_score(
            candidate_skills, required_skills, preferred_skills
        )
    
    def _calculate_experience_score(self, **kwargs) -> float:
        """Calculate experience match score."""
        experience_years = kwargs.get('experience_years', 0) # Changed from candidate_experience
        min_experience_required = kwargs.get('min_experience_required', 0) # Changed from required_experience
        
        from tools import scoring as scoring_module
        return scoring_module.calculate_experience_score(
            experience_years, min_experience_required
        )
    
    def _calculate_education_score(self, **kwargs) -> float:
        """Calculate education level score."""
        candidate_education = kwargs.get('candidate_education', '')
        required_education = kwargs.get('required_education', '')
        
        from tools import scoring as scoring_module
        return scoring_module.calculate_education_score(
            candidate_education, required_education
        )
    
    def _calculate_interview_score(self, **kwargs) -> float:
        """Calculate interview performance score."""
        technical_score = kwargs.get('technical_score')
        behavioral_score = kwargs.get('behavioral_score')
        
        from tools import scoring as scoring_module
        return scoring_module.calculate_interview_score(
            technical_score, behavioral_score
        )
    
    def _calculate_overall_score(self, **kwargs) -> float:
        """Calculate weighted overall score."""
        component_scores = kwargs.get('component_scores', {})
        
        from tools import scoring as scoring_module
        # Assuming calculate_overall_score is the weighted version
        return scoring_module.calculate_overall_score(component_scores)
    
    def _calculate_overall_score_full(self, **kwargs) -> dict:
        """Calculate full score with detailed breakdown."""
        from data.schemas import CandidateProfile, JobRequirements
        
        candidate_data = kwargs.get('candidate')
        job_data = kwargs.get('job')
        
        # Convert to proper objects if needed
        if isinstance(candidate_data, dict):
            candidate = CandidateProfile(**candidate_data)
        else:
            candidate = candidate_data
            
        if isinstance(job_data, dict):
            job = JobRequirements(**job_data)
        else:
            job = job_data
        
        # Import the original implementation
        from tools import scoring as scoring_module
        
        # Call original calculate_overall_score_detailed
        # Assuming a new function calculate_overall_score_detailed exists in scoring_module
        return scoring_module.calculate_overall_score_detailed(candidate, job)


def get_scoring_server() -> ScoringServer:
    """Get or create scoring server instance."""
    return ScoringServer()


__all__ = ["ScoringServer", "get_scoring_server"]

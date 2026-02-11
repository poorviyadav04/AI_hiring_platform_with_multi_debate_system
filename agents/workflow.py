"""
Multi-agent orchestration workflow.
Coordinates debate between Evaluator, Advocate, Skeptic, and Moderator.
"""

from typing import Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from agents import (
    AgentState,
    EvaluatorAgent,
    AdvocateAgent,
    SkepticAgent,
    ModeratorAgent
)
from data.schemas import CandidateProfile, JobRequirements, HiringConstraints, Decision
from data.evaluation_store import get_evaluation_store
from datetime import datetime


class MultiAgentWorkflow:
    """
    Orchestrates the multi-agent hiring decision workflow.
    
    Workflow:
    1. Evaluator: Objective scoring
    2. Advocate: Pro-hiring argument
    3. Skeptic: Risk analysis
    4. Moderator: Final decision
    5. Save to memory: Store evaluation for future reference
    """
    
    def __init__(self, constraints: HiringConstraints = None, llm=None, save_to_memory: bool = True):
        """
        Initialize workflow.
        
        Args:
            constraints: Hiring constraints/policies
            llm: Optional LLM client for agents
            save_to_memory: Whether to save evaluations to memory (default: True)
        """
        self.constraints = constraints
        self.llm = llm
        self.save_to_memory = save_to_memory
        
        # Initialize agents
        self.evaluator = EvaluatorAgent(constraints=constraints, llm=llm)
        self.advocate = AdvocateAgent(llm=llm)
        self.skeptic = SkepticAgent(llm=llm)
        self.moderator = ModeratorAgent(llm=llm)
        
        self.constraints = constraints or HiringConstraints(
            policy_id="POL-DEFAULT",
            policy_name="Standard Hiring Policy"
        )
    
    def run(self, candidate: CandidateProfile, job: JobRequirements) -> Dict[str, Any]:
        """
        Run the multi-agent hiring evaluation workflow with execution tracing.
        
        Args:
            candidate: Candidate to evaluate
            job: Job requirements
            
        Returns:
            Evaluation result with decision, scores, and debate transcript
        """
        # Generate evaluation ID
        timestamp = datetime.now()
        candidate_id = candidate.candidate_id if hasattr(candidate, 'candidate_id') else f"CAND-{hash(candidate.name) % 10000:04d}"
        evaluation_id = f"EVAL-{timestamp.strftime('%Y%m%d-%H%M%S')}-{candidate_id}"
        
        # Initialize execution tracer
        from tools.execution_tracer import ExecutionTracer, set_current_tracer
        tracer = ExecutionTracer(evaluation_id)
        set_current_tracer(tracer)
        
        print(f"\n{'='*70}")
        print(f"MULTI-AGENT HIRING EVALUATION")
        print(f"Candidate: {candidate.name}")
        print(f"Position: {job.title}")
        print(f"Evaluation ID: {evaluation_id}")
        print(f"{'='*70}\n")
        
        # Initialize shared state
        state = AgentState(candidate=candidate, job=job)
        
        # STEP 1: Evaluator - Objective scoring with tracing
        print("STEP 1: Evaluator Assessment...")
        with tracer.trace_agent("Evaluator", "calculate_scores"):
            state = self.evaluator.run(state)
            tracer.log_event(
                event_type="scoring_complete",
                action="calculate_overall_score",
                output_data={"scores": state.scores}
            )
        print(f"✓ Complete - Overall Score: {state.scores.get('overall', 0):.1f}/100\n")
        
        # STEP 2: Advocate - Pro-hire argument with tracing
        print("STEP 2: Advocate Building Case...")
        with tracer.trace_agent("Advocate", "build_pro_case"):
            state = self.advocate.run(state)
        print("✓ Complete\n")
        
        # STEP 3: Skeptic - Critical analysis with tracing
        print("STEP 3: Skeptic Analyzing Risks...")
        with tracer.trace_agent("Skeptic", "analyze_risks"):
            state = self.skeptic.run(state)
        print("✓ Complete\n")
        
        # STEP 4: Moderator - Final decision with tracing
        print("STEP 4: Moderator Making Final Decision...")
        with tracer.trace_agent("Moderator", "make_final_decision"):
            state = self.moderator.run(state)
            tracer.log_decision(
                decision=state.final_decision,
                score=state.scores.get('overall', 0),
                metadata={"component_scores": state.scores}
            )
        print(f"✓ Complete - Decision: {state.final_decision.upper()}\n")
        
        # Build result dictionary
        result = {
            'evaluation_id': evaluation_id,
            'candidate_id': candidate_id,
            'candidate_name': candidate.name,
            'job_id': job.job_id if hasattr(job, 'job_id') else 'JOB-001',
            'job_title': job.title,
            'final_decision': state.final_decision,
            'overall_score': state.scores.get('overall', 0),
            'component_scores': {
                'skills': state.scores.get('skills', 0),
                'experience': state.scores.get('experience', 0),
                'education': state.scores.get('education', 0),
                'interviews': state.scores.get('interviews', 0),
            },
            'debate_transcript': [
                {
                    'agent': msg.agent_name,
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in state.messages
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to memory if enabled
        if self.save_to_memory:
            try:
                tracer.log_event(
                    event_type="memory_save_start",
                    action="save_evaluation"
                )
                
                eval_store = get_evaluation_store()
                eval_id = eval_store.save_evaluation(
                    candidate_id=candidate_id,
                    candidate_name=candidate.name,
                    job_id=result['job_id'],
                    job_title=job.title,
                    overall_score=state.scores.get('overall', 0),
                    component_scores=state.scores,
                    final_decision=state.final_decision,
                    debate_transcript=result['debate_transcript'],
                    metadata={'constraints': self.constraints.dict() if self.constraints else {}}
                )
                result['evaluation_id'] = eval_id
                
                tracer.log_event(
                    event_type="memory_save_complete",
                    action="save_evaluation",
                    output_data={"evaluation_id": eval_id}
                )
                
                print(f"✓ Evaluation saved to memory: {eval_id}\n")
            except Exception as e:
                print(f"⚠️  Warning: Could not save to memory: {e}\n")
        
        # Save execution trace
        trace_file = tracer.save()
        tracer.print_summary()
        print(f"✓ Execution trace saved: {trace_file}\n")
        
        # Clear tracer
        from tools.execution_tracer import set_current_tracer
        set_current_tracer(None)
        
        return result
    
    def create_decision_object(self, result: Dict) -> Decision:
        """
        Convert workflow result to Decision schema.
        
        Args:
            result: Workflow result
            
        Returns:
            Decision object
        """
        
        # Extract key points from debate
        moderator_msg = next(
            (msg for msg in result['debate_transcript'] if msg['role'] == 'moderator'),
            None
        )
        
        reasoning = moderator_msg['content'] if moderator_msg else "Decision pending"
        
        return Decision(
            decision_id=f"DEC-{result['candidate_id']}-{result['job_id']}",
            candidate_id=result['candidate_id'],
            job_id=result['job_id'],
            final_decision=result['final_decision'],
            overall_score=result['overall_score'],
            component_scores=result['component_scores'],
            reasoning_summary=reasoning[:500],  # Truncate for summary
            debate_transcript={
                'messages': result['debate_transcript']
            },
            timestamp=datetime.fromisoformat(result['timestamp'])
        )


__all__ = ["MultiAgentWorkflow"]

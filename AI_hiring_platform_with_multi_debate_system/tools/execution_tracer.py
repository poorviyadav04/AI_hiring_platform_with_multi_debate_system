"""
Execution Tracer for Multi-Agent Workflow
Provides observability and audit trails for hiring decisions.

Features:
- Agent action logging
- Tool call tracking
- Performance metrics
- Decision traces
- OpenTelemetry-style tracing
"""

import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager


@dataclass
class TraceEvent:
    """Single trace event in the execution."""
    timestamp: str
    event_type: str  # 'agent_start', 'agent_end', 'tool_call', 'decision'
    agent: str
    action: str
    input_data: Optional[Dict] = None
    output_data: Optional[Dict] = None
    duration_ms: Optional[float] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class ExecutionTracer:
    """
    Tracer for multi-agent workflow execution.
    
    Tracks:
    - Agent lifecycle (start/end)
    - Tool calls
    - Performance metrics
    - Decision flow
    
    Example:
        tracer = ExecutionTracer(evaluation_id="EVAL-001")
        
        with tracer.trace_agent("Evaluator", "calculate_score"):
            score = calculate_score()
            tracer.log_event("score_calculated", output_data={"score": score})
        
        tracer.save()
    """
    
    def __init__(self, evaluation_id: str, trace_dir: str = "data/traces"):
        """
        Initialize execution tracer.
        
        Args:
            evaluation_id: Unique evaluation identifier
            trace_dir: Directory to save trace files
        """
        self.evaluation_id = evaluation_id
        self.trace_dir = Path(trace_dir)
        self.events: List[TraceEvent] = []
        self.start_time = time.time()
        self.current_agent: Optional[str] = None
        
        # Create trace directory
        today = datetime.now().strftime('%Y-%m-%d')
        self.output_dir = self.trace_dir / today
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def log_event(
        self,
        event_type: str,
        action: str,
        agent: Optional[str] = None,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Log a trace event.
        
        Args:
            event_type: Type of event (agent_start, agent_end, tool_call, etc.)
            action: Action being performed
            agent: Agent name (defaults to current_agent)
            input_data: Input parameters
            output_data: Output/result
            duration_ms: Duration in milliseconds
            metadata: Additional metadata
        """
        agent = agent or self.current_agent or "system"
        
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent=agent,
            action=action,
            input_data=input_data,
            output_data=output_data,
            duration_ms=duration_ms,
            metadata=metadata
        )
        
        self.events.append(event)
    
    @contextmanager
    def trace_agent(self, agent_name: str, action: str):
        """
        Context manager to trace agent execution.
        
        Args:
            agent_name: Name of the agent
            action: Action being performed
            
        Example:
            with tracer.trace_agent("Evaluator", "calculate_score"):
                result = evaluator.run()
        """
        # Store previous agent
        prev_agent = self.current_agent
        self.current_agent = agent_name
        
        # Log start
        start_time = time.time()
        self.log_event(
            event_type="agent_start",
            action=action,
            agent=agent_name
        )
        
        try:
            yield self
        finally:
            # Log end with duration
            duration_ms = (time.time() - start_time) * 1000
            self.log_event(
                event_type="agent_end",
                action=action,
                agent=agent_name,
                duration_ms=duration_ms
            )
            
            # Restore previous agent
            self.current_agent = prev_agent
    
    @contextmanager
    def trace_tool(self, tool_name: str, **kwargs):
        """
        Context manager to trace tool execution.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
            
        Example:
            with tracer.trace_tool("find_similar_candidates", query="AWS"):
                results = tool.execute()
        """
        start_time = time.time()
        
        self.log_event(
            event_type="tool_start",
            action=tool_name,
            input_data=kwargs
        )
        
        try:
            yield self
        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000
            self.log_event(
                event_type="tool_error",
                action=tool_name,
                duration_ms=duration_ms,
                metadata={"error": str(e)}
            )
            raise
        else:
            # Log success
            duration_ms = (time.time() - start_time) * 1000
            self.log_event(
                event_type="tool_end",
                action=tool_name,
                duration_ms=duration_ms
            )
    
    def log_decision(self, decision: str, score: float, metadata: Optional[Dict] = None):
        """
        Log final decision.
        
        Args:
            decision: Final decision (hire/reject/conditional)
            score: Overall score
            metadata: Additional decision metadata
        """
        self.log_event(
            event_type="final_decision",
            action="decide",
            output_data={"decision": decision, "score": score},
            metadata=metadata
        )
    
    def get_summary(self) -> Dict:
        """
        Get execution summary statistics.
        
        Returns:
            Summary dictionary with metrics
        """
        total_duration = (time.time() - self.start_time) * 1000
        
        # Count events by type
        event_counts = {}
        for event in self.events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        # Calculate agent durations
        agent_durations = {}
        for event in self.events:
            if event.event_type == "agent_end" and event.duration_ms:
                agent_durations[event.agent] = event.duration_ms
        
        # Calculate tool durations
        tool_durations = {}
        for event in self.events:
            if event.event_type == "tool_end" and event.duration_ms:
                tool_durations[event.action] = event.duration_ms
        
        return {
            "evaluation_id": self.evaluation_id,
            "total_events": len(self.events),
            "total_duration_ms": total_duration,
            "event_counts": event_counts,
            "agent_durations_ms": agent_durations,
            "tool_durations_ms": tool_durations
        }
    
    def save(self) -> str:
        """
        Save trace to JSON file.
        
        Returns:
            Path to saved trace file
        """
        # Build trace document
        trace = {
            "evaluation_id": self.evaluation_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "events": [event.to_dict() for event in self.events]
        }
        
        # Save to file
        output_file = self.output_dir / f"{self.evaluation_id}-trace.json"
        with open(output_file, 'w') as f:
            json.dump(trace, f, indent=2)
        
        return str(output_file)
    
    def print_summary(self):
        """Print execution summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("EXECUTION TRACE SUMMARY")
        print("="*70)
        print(f"Evaluation ID: {summary['evaluation_id']}")
        print(f"Total Duration: {summary['total_duration_ms']:.2f}ms")
        print(f"Total Events: {summary['total_events']}")
        
        print("\nAgent Durations:")
        for agent, duration in summary['agent_durations_ms'].items():
            print(f"  {agent}: {duration:.2f}ms")
        
        if summary['tool_durations_ms']:
            print("\nTool Durations:")
            for tool, duration in summary['tool_durations_ms'].items():
                print(f"  {tool}: {duration:.2f}ms")
        
        print("="*70 + "\n")


# Global tracer instance
_current_tracer: Optional[ExecutionTracer] = None


def get_current_tracer() -> Optional[ExecutionTracer]:
    """Get the current execution tracer."""
    return _current_tracer


def set_current_tracer(tracer: Optional[ExecutionTracer]):
    """Set the current execution tracer."""
    global _current_tracer
    _current_tracer = tracer


@contextmanager
def trace_evaluation(evaluation_id: str):
    """
    Context manager to trace entire evaluation.
    
    Args:
        evaluation_id: Unique evaluation identifier
        
    Example:
        with trace_evaluation("EVAL-001"):
            result = workflow.run(candidate, job)
    """
    tracer = ExecutionTracer(evaluation_id)
    set_current_tracer(tracer)
    
    try:
        yield tracer
    finally:
        # Save and print summary
        trace_file = tracer.save()
        tracer.print_summary()
        print(f"✓ Execution trace saved: {trace_file}\n")
        
        # Clear tracer
        set_current_tracer(None)


__all__ = [
    "ExecutionTracer",
    "TraceEvent",
    "get_current_tracer",
    "set_current_tracer",
    "trace_evaluation"
]

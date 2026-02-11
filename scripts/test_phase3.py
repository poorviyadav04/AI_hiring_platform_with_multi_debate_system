"""
Demo script to test LangChain tools with a local LLM.
This demonstrates how agents can call scoring tools via Ollama.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_servers.tools_langchain import SCORING_TOOLS


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_tools_direct():
    """Test tools by calling them directly."""
    print_section("TESTING LANGCHAIN TOOLS - DIRECT CALLS")
    
    # Test 1: Skill Match Tool
    print("\n1. Skill Match Tool:")
    print("-" * 70)
    result = SCORING_TOOLS[0].invoke({
        "candidate_skills": ["Python", "React", "AWS", "Docker"],
        "required_skills": ["Python", "React", "AWS"],
        "preferred_skills": ["Docker", "Kubernetes"]
    })
    print(result)
    
    # Test 2: Experience Match Tool
    print("\n2. Experience Match Tool:")
    print("-" * 70)
    result = SCORING_TOOLS[1].invoke({
        "candidate_years": 5.0,
        "required_years": 5.0,
        "role_level": "mid",
        "allow_gap": True,
        "max_gap_years": 1.0
    })
    print(result)
    
    # Test 3: Budget Check Tool
    print("\n3. Budget Check Tool:")
    print("-" * 70)
    result = SCORING_TOOLS[2].invoke({
        "candidate_salary": 115000,
        "budget_min": 100000,
        "budget_max": 130000,
        "max_overage_percent": 5.0
    })
    print(result)
    
    # Test 4: Score Threshold Check Tool
    print("\n4. Score Threshold Check Tool:")
    print("-" * 70)
    result = SCORING_TOOLS[3].invoke({
        "technical_score": 85.0,
        "behavioral_score": 80.0,
        "overall_score": 78.0,
        "min_technical": 60.0,
        "min_behavioral": 60.0,
        "min_overall": 65.0
    })
    print(result)


def test_tools_with_agent():
    """Test tools with LangChain agent (requires Ollama)."""
    print_section("TESTING LANGCHAIN TOOLS - WITH AGENT")
    
    try:
        from langchain_community.llms import Ollama
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain.prompts import PromptTemplate
        
        print("\n✓ Ollama packages available")
        
        # Initialize Ollama
        try:
            llm = Ollama(model="llama3", temperature=0)
            print("✓ Ollama LLM initialized (llama3)")
        except Exception as e:
            print(f"⚠️  Ollama not running: {e}")
            print("   Please start Ollama and ensure llama3 model is downloaded")
            print("   Run: ollama serve")
            return
        
        # Create agent prompt
        template = """You are a hiring decision assistant with access to scoring tools.

You have access to the following tools:

{tools}

Use this format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
{agent_scratchpad}"""
        
        prompt = PromptTemplate.from_template(template)
        
        # Create agent
        agent = create_react_agent(llm, SCORING_TOOLS, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=SCORING_TOOLS,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
        
        print("\n✓ Agent created with scoring tools")
        
        # Test query
        print("\n" + "-" * 70)
        print("Query: Evaluate a candidate with Python and React skills,")
        print("       5 years experience for a mid-level role requiring")
        print("       Python, React, and AWS with $110K salary vs $100-120K budget")
        print("-" * 70)
        
        response = agent_executor.invoke({
            "input": """Evaluate this candidate:
            - Skills: Python, React
            - Experience: 5 years
            - Role level: mid
            - Salary: 110000
            - Budget: 100000-120000
            
            Required skills: Python, React, AWS
            Required experience: 5 years
            
            Use the tools to:
            1. Check skill match
            2. Check experience match
            3. Check budget constraint
            
            Provide a summary of whether this candidate should proceed."""
        })
        
        print("\n" + "=" * 70)
        print("AGENT RESPONSE:")
        print("=" * 70)
        print(response['output'])
        
    except ImportError as e:
        print(f"\n⚠️  LangChain Community not installed: {e}")
        print("   Install with: pip install langchain-community")
    except Exception as e:
        print(f"\n❌ Error testing with agent: {e}")
        import traceback
        traceback.print_exc()


def test_tool_descriptions():
    """Show tool descriptions for agent discovery."""
    print_section("TOOL CATALOG - FOR AGENT DISCOVERY")
    
    for i, tool in enumerate(SCORING_TOOLS, 1):
        print(f"\n{i}. {tool.name}")
        print("-" * 70)
        print(f"Description: {tool.description}")
        print(f"Args Schema: {tool.args}")


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  PHASE 3: MCP/LANGCHAIN TOOLS - DEMO")
    print("=" * 70)
    
    try:
        # Test 1: Direct tool calls
        test_tools_direct()
        
        # Test 2: Tool descriptions
        test_tool_descriptions()
        
        # Test 3: Agent (requires Ollama)
        test_tools_with_agent()
        
        print("\n" + "=" * 70)
        print("  ✅ TOOL TESTING COMPLETE")
        print("=" * 70)
        print("\nPhase 3 Tools:")
        print("  ✓ 4 LangChain tools created")
        print("  ✓ Direct tool invocation working")
        print("  ✓ Agent integration ready (requires Ollama)")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

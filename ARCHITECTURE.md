# Architecture Documentation

## System Overview

The LLM Decision Intelligence System is built on a **modular, layered architecture** that separates concerns and enables independent component testing and evolution.

## Architecture Layers

### **Layer 1: Data Foundation**
```
data/schemas.py - Pydantic models for type safety
```

**Purpose:** Define all data structures with validation

**Key Components:**
- `CandidateProfile` - Candidate information
- `JobRequirements` - Job specifications
- `HiringConstraints` - Policy rules
- `Decision` - Hiring decision records
- `AgentState` - Multi-agent shared state
- `AgentMessage` - Inter-agent communication

**Design Decisions:**
- Pydantic for automatic validation
- Immutable by default (data integrity)
- JSON-serializable for API compatibility

---

### **Layer 2: Deterministic Core**
```
tools/scoring.py      - Scoring algorithms
tools/constraints.py  - Policy validation
```

**Purpose:** Provide zero-hallucination, transparent calculations

**Key Functions:**

**Scoring (`scoring.py`):**
- `calculate_skill_match()` - Weighted skill scoring with depth bonus
- `calculate_experience_score()` - Gap-aware experience evaluation
- `calculate_education_score()` - Hierarchical education levels
- `calculate_overall_score()` - Composite score with component weights

**Constraints (`constraints.py`):**
- `check_budget_constraint()` - Budget compliance with tolerance
- `validate_experience_requirement()` - Experience gap validation
- `check_score_thresholds()` - Technical/behavioral/overall thresholds
- `validate_all_constraints()` - Comprehensive policy check

**Design Decisions:**
- Pure functions (no side effects)
- Detailed breakdown in return values
- Configurable thresholds via HiringConstraints

---

### **Layer 3: RAG System**
```
rag/vector_store.py       - FAISS semantic search
rag/decision_graph.py     - NetworkX relationships
rag/hybrid_retrieval.py   - Combined retrieval
```

**Purpose:** Intelligent retrieval with context from past decisions

#### **3A: Vector Store (FAISS)**

**Capabilities:**
- Index candidates and jobs as embeddings
- Semantic similarity search
- Cosine similarity via normalized vectors
- Fast retrieval (<10ms per query)

**Embedding Model:**
- `all-MiniLM-L6-v2` (384 dimensions)
- Optimized for semantic textual similarity
- Compact yet accurate

**Storage:**
- FAISS index files (`.faiss`)
- Metadata in pickle files (`.pkl`)
- Disk-persistent, fast loading

#### **3B: Decision Graph (NetworkX)**

**Graph Schema:**

**Nodes:**
- `candidate` - Candidate profiles
- `job` - Job postings
- `decision` - Hiring decisions (future)

**Edges:**
- `hired_for` - Successful hire relationship
- `rejected_for` - Rejection relationship
- `applied_to` - Application relationship
- `similar_to` - Similarity edges (bidirectional)

**Capabilities:**
- Traverse hiring history
- Find similar candidates via graph
- Identify successful patterns
- Track candidate journey

**Storage:**
- GML format (human-readable)
- Full graph topology preserved

#### **3C: Hybrid Retrieval**

**Algorithm:**
```
1. Vector Search → Get top-K semantically similar
2. Graph Enrichment → Add relationship context
3. Re-Ranking → Boost based on track record
   - Boost if past hires for similar roles
   - Penalize if previous rejections
4. Context Injection → Include:
   - Application history
   - Similar candidate references
   - Success patterns
```

**Benefits:**
- More relevant than pure vector search
- Contextual awareness from graph
- Learns from past hiring decisions

---

### **Layer 4: Agent System**
```
agents/base_agent.py      - Base class & state
agents/evaluator_agent.py - Objective scorer
agents/advocate_agent.py  - Pro-hiring advocate
agents/skeptic_agent.py   - Risk analyzer
agents/moderator_agent.py - Decision synthesizer
agents/workflow.py        - Orchestration
```

**Purpose:** Multi-perspective decision making via specialized agents

#### **Agent Roles**

**1. Evaluator Agent**
- **Input:** Candidate + Job
- **Process:** Calls Layer 2 deterministic functions
- **Output:** Objective scores & constraint validation
- **Bias:** None (purely data-driven)

**2. Advocate Agent**
- **Input:** Candidate + Job + Evaluator scores
- **Process:** Highlights strengths, frames gaps as opportunities
- **Output:** Pro-hiring argument
- **Bias:** Optimistic (intentional)

**3. Skeptic Agent**
- **Input:** Candidate + Job + Evaluator scores
- **Process:** Identifies risks, challenges assumptions
- **Output:** Critical analysis with concerns
- **Bias:** Pessimistic (intentional)

**4. Moderator Agent**
- **Input:** All agent messages + scores
- **Process:** Synthesizes perspectives via decision logic
- **Output:** Final decision (hire/conditional/reject)
- **Bias:** Balanced (weighs both sides)

#### **State Management**

**AgentState:**
```python
class AgentState(BaseModel):
    candidate: CandidateProfile
    job: JobRequirements
    messages: List[AgentMessage]  # Debate transcript
    scores: Dict[str, float]       # Component scores
    final_decision: Optional[str]
    reasoning: Optional[str]
```

**Message Passing:**
- Agents append messages to shared state
- Each message has: agent, role, content, timestamp, metadata
- Full audit trail of decision process

**Workflow:**
```
Initialize State
    ↓
Evaluator.run(state) → Update state with scores
    ↓
Advocate.run(state) → Add pro-hiring message
    ↓
Skeptic.run(state) → Add critical message
    ↓
Moderator.run(state) → Add final decision
    ↓
Return Result (with full transcript)
```

---

### **Layer 5: Integration Tools**
```
mcp_servers/tools_langchain.py - LangChain tool wrappers
mcp_servers/memory_tools.py    - RAG query tools
```

**Purpose:** Expose core functionality as callable tools for agents

**LangChain Tools (Phase 3):**
- `skill_match_tool` - Wraps `calculate_skill_match`
- `experience_match_tool` - Wraps `calculate_experience_score`
- `budget_check_tool` - Wraps `check_budget_constraint`
- `score_threshold_check_tool` - Wraps `check_score_thresholds`

**Memory Tools (Phase 4):**
- `find_similar_candidates_tool` - Queries vector + graph
- `find_past_decisions_tool` - Retrieves hiring history
- `get_candidate_history_tool` - Shows candidate journey

**Design:**
- `@tool` decorator for LangChain compatibility
- Human-readable output formatting
- Error handling with clear messages

---

### **Layer 6: API Interface**
```
api/main.py - FastAPI REST endpoints
```

**Purpose:** External integration via HTTP

**Endpoints:**

**POST /evaluate**
- Input: Candidate + Job JSON
- Process: Run multi-agent workflow
- Output: Decision + scores + debate summary
- Stores decision in graph

**POST /candidates/search**
- Input: Natural language query
- Process: Hybrid RAG retrieval
- Output: Ranked candidates with similarity scores

**GET /decisions/{id}**
- Input: Decision ID
- Output: Decision details

**GET /stats**
- Output: System statistics (candidates, jobs, decisions)

**Design:**
- Pydantic request/response models
- CORS enabled for frontend integration
- Auto-generated OpenAPI docs at `/docs`

---

## Data Flow Example

**Scenario:** Evaluate Jane Doe for Senior Engineer role

```
User → API: POST /evaluate
         ↓
    FastAPI validates request
         ↓
    MultiAgentWorkflow.run()
         ↓
    ┌─────────────────────┐
    │ 1. Evaluator Agent  │
    │ ├─ calculate_overall_score() ← Layer 2
    │ ├─ validate_all_constraints() ← Layer 2
    │ └─ Adds scores to state
    └─────────────────────┘
         ↓
    ┌─────────────────────┐
    │ 2. Advocate Agent   │
    │ ├─ Reads scores from state
    │ ├─ Builds pro-hiring argument
    │ └─ Adds message to state
    └─────────────────────┘
         ↓
    ┌─────────────────────┐
    │ 3. Skeptic Agent    │
    │ ├─ Reads scores & validation
    │ ├─ Identifies concerns
    │ └─ Adds message to state
    └─────────────────────┘
         ↓
    ┌─────────────────────┐
    │ 4. Moderator Agent  │
    │ ├─ Reviews all messages
    │ ├─ Applies decision logic
    │ ├─ Sets final_decision
    │ └─ Adds reasoning
    └─────────────────────┘
         ↓
    Create Decision object
         ↓
    DecisionGraph.add_decision() ← Layer 3
         ↓
    Return result
         ↓
User ← API: JSON response
```

---

## Design Principles

### **1. Separation of Concerns**
- Each layer has a clear, distinct responsibility
- Layers depend only on lower layers (no circular deps)
- Easy to test layers independently

### **2. Deterministic Core**
- Scoring and constraints are pure functions
- Same input always produces same output
- Zero hallucination risk

### **3. Pluggable Components**
- Easy to swap FAISS with another vector DB
- Can add new agents without changing existing ones
- Tools can be used independently

### **4. Type Safety**
- Pydantic models enforce schemas
- FastAPI validates requests/responses automatically
- Reduces runtime errors

### **5. Explainability**
- Full debate transcript preserved
- Score calculations include detailed breakdowns
- Constraint violations explicitly listed

---

## Scalability Considerations

### **Current Limitations (Prototype)**
- In-memory graph (NetworkX)
- File-based storage (JSON, pickle)
- Single-threaded workflow

### **Production Enhancements**
- **Database:** PostgreSQL for persistent storage
- **Caching:** Redis for hot data
- **Async:** Async agents with parallel evaluation
- **Queue:** Celery for background processing
- **Distributed:** Ray for multi-node scaling

---

## Technology Choices Rationale

| Choice | Why? |
|--------|------|
| **Pydantic** | Type safety, validation, FastAPI compatibility |
| **FAISS** | Fastest vector search, Facebook-proven |
| **NetworkX** | Python-native graph library, easy to learn |
| **FastAPI** | Modern, fast, auto-docs, async-ready |
| **Sentence Transformers** | SOTA embeddings, pre-trained models |
| **pytest** | Standard Python testing, fixtures, parametrize |

---

## Security Considerations

**Current (Prototype):**
- No authentication (local use)
- No rate limiting
- No input sanitization beyond Pydantic

**Production Recommendations:**
- JWT authentication for API
- Rate limiting (per IP/user)
- Input validation & sanitization
- HTTPS only
- Secret management (not in .env)
- Audit logging

---

## Extension Points

**Easy to Add:**
1. **New Agents** - Inherit from `BaseAgent`, implement `run()`
2. **New Tools** - Use `@tool` decorator, add to tool list
3. **New Scoring Functions** - Add to `tools/scoring.py`
4. **New API Endpoints** - Add route to `api/main.py`

**Example: Adding "Recruiter Agent"**
```python
class RecruiterAgent(BaseAgent):
    def run(self, state):
        # Access candidate via state.candidate
        # Add sourcing perspective
        message = self.create_message(content="...")
        state.messages.append(message)
        return state

# Add to workflow.py
self.recruiter = RecruiterAgent()
# Call in workflow
state = self.recruiter.run(state)
```

---

**Last Updated:** 2026-02-07  
**Version:** 1.0.0

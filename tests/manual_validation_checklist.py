"""
Manual testing checklist and validation guide.
Run this to get a step-by-step validation process.
"""

def print_manual_checklist():
    """Print manual testing checklist."""
    
    checklist = """
╔═══════════════════════════════════════════════════════════════════════╗
║           MANUAL VALIDATION CHECKLIST FOR AI HIRING SYSTEM            ║
╚═══════════════════════════════════════════════════════════════════════╝

📋 PHASE 1: BASIC FUNCTIONALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Dashboard loads without errors
□ All 4 pages accessible (Home, Evaluate, Counterfactual, Red Team)
□ Sidebar shows Ollama connection status
□ Candidate dropdown populated with all candidates
□ Job dropdown populated with all positions

📋 PHASE 2: EVALUATION TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test Case 1: High-Scoring Candidate
□ Select: Candidate with strong skills matching job
□ Expected: Overall score > 80, Decision = "Hire" or "Strong Hire"
□ Verify: Component scores all > 70
□ Verify: Advocate message is positive
□ Verify: Moderator decision matches score

Test Case 2: Low-Scoring Candidate
□ Select: Candidate with weak skill match
□ Expected: Overall score < 65, Decision = "Reject"
□ Verify: Skeptic raises valid concerns
□ Verify: Decision is justified

Test Case 3: Borderline Candidate
□ Select: Candidate with score 65-75
□ Expected: Decision = "Conditional Hire"
□ Verify: Both strengths and weaknesses mentioned
□ Verify: Conditions for hiring stated

📋 PHASE 3: SCORE VALIDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Skills Score (0-100):
  - Candidate has ALL required skills → Should be ~90-100
  - Candidate missing 50% of skills → Should be ~40-50
  - Check: Score decreases with missing skills

□ Experience Score (0-100):
  - Meets minimum years → Should be ~80+
  - Below minimum → Should be <80
  - 2x minimum → Should be ~100

□ Education Score (0-100):
  - MS/PhD for senior role → Should be ~100
  - BS for senior role → Should be ~75-90
  - Bootcamp → Should be ~50-70

□ Interview Score (0-100):
  - Average of technical, behavioral, coding scores
  - Verify: Matches candidate's interview scores

□ Overall Score:
  - Verify: Is weighted average of components
  - Check: Falls between 0-100
  - Test: Same candidate + job → Same score (deterministic)

📋 PHASE 4: AGENT BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Evaluator:
  - Shows objective scores
  - Lists skill matches/gaps
  - No subjective opinions

□ Advocate (If LLM enabled):
  - Argues FOR hiring
  - Highlights strengths
  - Positive tone
  - Suggests how to address gaps

□ Skeptic (If LLM enabled):
  - Argues AGAINST hiring
  - Points out risks
  - Critical tone
  - Questions candidate fit

□ Moderator (If LLM enabled):
  - Balanced perspective
  - References all agents
  - Clear final decision
  - Justified reasoning

📋 PHASE 5: RED TEAM ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Shows correct Overall Score (NOT 0.0)
□ Shows correct Decision (NOT "UNKNOWN")
□ Identifies at least one challenge or confirms "No challenges"
□ Verdict is one of: APPROVED / CONDITIONAL / CHALLENGED
□ Sensitivity analysis shows top counterfactual

Common Red Team Checks:
□ Bias Detection: Flags education/experience bias
□ Boundary Testing: Notes scores near thresholds (65, 75, 85)
□ Consistency: Checks score-decision alignment
□ Edge Cases: Identifies unusual candidates
□ Fairness: Ensures no single component dominates

📋 PHASE 6: COUNTERFACTUAL EXPLORER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Skill Counterfactuals:
  - Shows missing required skills
  - Impact points make sense (core skills = higher impact)
  - Explanations are clear

□ Experience Counterfactuals:
  - Shows how +1, +2 years affects score
  - Indicates if meets/doesn't meet minimum

□ Education Counterfactuals:
  - Shows upgrade paths (BS→MS→PhD)
  - Impact values reasonable

□ Salary Counterfactuals:
  - Shows budget fit
  - Percentage margin calculated correctly

📋 PHASE 7: EDGE CASE TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test these scenarios:
□ Candidate with 0 matching skills → Very low score
□ Candidate with ALL skills but 0 experience → Mixed score
□ Overqualified candidate (2x experience) → High score
□ Salary 2x budget → Should be flagged
□ Remote job + candidate unwilling to relocate → Check constraints

📋 PHASE 8: BUG CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Common Bugs to Watch:
□ Red Team shows 0.0 score ❌ (FIXED)
□ Decisions don't match scores
□ Component scores > 100 or < 0
□ Same candidate gives different scores (non-deterministic)
□ Agent debates are empty
□ Counterfactuals show negative impacts
□ Dashboard crashes on evaluation
□ Ollama status contradictory ❌ (FIXED)

📋 PHASE 9: OLLAMA/LLM TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

With Ollama Running:
□ Sidebar shows "✅ Ollama Connected"
□ Advocate/Skeptic/Moderator generate natural language
□ Red Team uses LLM for analysis (if enabled)
□ Responses are coherent and relevant

Without Ollama:
□ Sidebar shows "⚠️ Ollama Offline"
□ Fallback mode messages appear
□ Deterministic responses still work
□ Red Team shows proper fallback analysis ✅ (FIXED)

📋 VALIDATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If all items checked: ✅ System is production-ready
If 1-2 items failed: ⚠️  Minor issues, can be addressed
If 3+ items failed: ❌ Requires debugging before deployment

═══════════════════════════════════════════════════════════════════════

💡 PRO TIPS:
• Test with at least 5 different candidate-job combinations
• Test both with Ollama ON and OFF
• Compare multiple evaluations of same candidate (should be identical)
• Check Red Team identifies genuine edge cases
• Verify counterfactuals actually improve scores when applied
"""
    
    print(checklist)


if __name__ == "__main__":
    print_manual_checklist()

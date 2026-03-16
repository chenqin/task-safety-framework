#!/usr/bin/env python3
"""
LLM Coding Agent Example - Complete E2E with Context/Output Tracking

This example demonstrates how a coding agent (OpenClaw, Codex, Claude Code)
can use LLMTask to safely run long-running coding tasks with:
1. Full context tracking (last prompt to LLM)
2. Output tracking (last response from LLM)
3. Auto-resume from exact LLM conversation point

Scenario: Coding agent refactors a Python codebase with LLM assistance.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from llm_task import LLMTask, resume_llm_task


class MockLLMAPI:
    """
    Mock LLM API for demonstration.
    
    In real usage, replace with:
    - OpenAI API
    - Claude API  
    - llama.cpp API
    - Any LLM provider
    """
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self.conversation_turns = 0
    
    def call(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> Dict:
        """
        Mock LLM call.
        
        In real usage:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt},
                          {"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message
        """
        self.conversation_turns += 1
        
        # Mock response based on prompt content
        if "analyze" in prompt.lower():
            response = """
Analysis complete. Found 3 files to refactor:
1. utils.py - Add type hints
2. main.py - Extract functions
3. config.py - Validate inputs

Next step: Refactor utils.py
"""
        elif "refactor" in prompt.lower() and "utils.py" in prompt:
            response = """
Refactored utils.py:
- Added type hints to all functions
- Improved docstrings
- Reduced complexity from 25 to 12

Ready for next file: main.py
"""
        elif "refactor" in prompt.lower() and "main.py" in prompt:
            response = """
Refactored main.py:
- Extracted 5 helper functions
- Added error handling
- Improved structure

Ready for next file: config.py
"""
        else:
            response = """
Task complete! All files refactored successfully.

Summary:
- 3 files processed
- 150 lines added
- 50 lines removed
- Net improvement: +100 LOC with better structure
"""
        
        return {
            "content": response,
            "token_count": len(response) // 4,  # Rough estimate
            "tool_calls": []
        }


class CodingAgent:
    """
    Example coding agent using LLMTask for safe long-running tasks.
    """
    
    def __init__(self, task_name: str):
        self.task = LLMTask(task_name)
        self.llm = MockLLMAPI(model="gpt-4")
        self.system_prompt = """
You are a coding assistant helping to refactor Python code.
Your goal is to improve code quality while maintaining functionality.

Guidelines:
1. Add type hints
2. Improve function names
3. Extract helper functions
4. Add docstrings
5. Reduce complexity

Always provide clear, actionable output.
"""
    
    def run(self):
        """Run the coding agent task."""
        print("="*60)
        print("🤖 LLM Coding Agent: Python Codebase Refactoring")
        print("="*60)
        print()
        
        # Define task steps
        steps = [
            "analyze_codebase",
            "refactor_utils",
            "refactor_main",
            "refactor_config",
            "generate_summary"
        ]
        
        # Resume if interrupted
        if self.task.should_resume():
            last_step = self.task.state["last_step"]
            start_index = steps.index(last_step) + 1
            print(f"🔄 Resuming from step: {last_step}")
            print(f"   Starting from: {steps[start_index]}")
        else:
            start_index = 0
            print(f"🆕 Starting fresh task")
        
        print()
        
        # Execute steps
        for i, step in enumerate(steps[start_index:], start=start_index):
            try:
                print(f"[{i+1:2d}/{len(steps)}] Step: {step}")
                
                # Build context for this step
                context = self._build_step_context(step)
                
                # Save context (what we send to LLM)
                self.task.set_context(context)
                
                # Call LLM
                print(f"   📤 Sending to LLM...")
                response = self.llm.call(
                    prompt=context,
                    system_prompt=self.system_prompt
                )
                
                # Save output (what LLM returned)
                self.task.save_response(
                    response=response["content"],
                    tool_calls=response.get("tool_calls", []),
                    token_count=response["token_count"]
                )
                
                # Create checkpoint
                self.task.checkpoint(step, metadata={
                    "response_tokens": response["token_count"],
                    "llm_turn": self.llm.conversation_turns
                })
                
                print(f"   ✅ Complete")
                print(f"   Response: {response['content'][:100]}...")
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.task.mark_failed(f"Step {step} failed: {e}")
                raise
        
        # Mark complete
        self.task.mark_complete()
        
        print()
        print("="*60)
        print("✅ Task Complete!")
        print("="*60)
        print()
        print("📁 Context files saved:")
        print(f"   Context: {self.task.context_file}")
        print(f"   Output: {self.task.output_file}")
        print(f"   History: {self.task.history_file}")
        print()
        print("🔄 To resume (if interrupted), just run this script again!")
        print()
    
    def _build_step_context(self, step: str) -> str:
        """Build context for a specific step."""
        
        # Get previous response if exists
        last_response = self.task.get_last_response()
        
        if step == "analyze_codebase":
            return f"""
Analyze the Python codebase in /home/chen/my-project/

Files to analyze:
- utils.py (150 lines)
- main.py (200 lines)  
- config.py (80 lines)

Provide a refactoring plan.
"""
        
        elif step == "refactor_utils":
            return f"""
Refactor utils.py based on analysis.

Previous response:
{last_response}

Focus on:
1. Adding type hints
2. Improving function names
3. Adding docstrings
"""
        
        elif step == "refactor_main":
            return f"""
Refactor main.py.

Previous response:
{last_response}

Focus on:
1. Extracting helper functions
2. Adding error handling
3. Improving structure
"""
        
        elif step == "refactor_config":
            return f"""
Refactor config.py.

Previous response:
{last_response}

Focus on:
1. Input validation
2. Type checking
3. Environment variables
"""
        
        else:  # generate_summary
            return f"""
Generate a summary of all refactoring work.

Previous response:
{last_response}

Include:
- Files changed
- Lines added/removed
- Key improvements
- Testing recommendations
"""


def main():
    """Main entry point."""
    agent = CodingAgent("python_refactor_demo")
    agent.run()


if __name__ == "__main__":
    main()

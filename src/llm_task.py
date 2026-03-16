"""
LLM Task Manager - Checkpointing for LLM-based Agents

This module provides LLM-friendly checkpointing that tracks:
1. Full context (last prompt sent to LLM)
2. Last output (last response from LLM)
3. Conversation history (for context window management)

Designed for coding agents, research agents, and any LLM-powered automation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from safe_task import SafeTask


class LLMTask:
    """
    LLM-friendly task manager with context/output tracking.
    
    Usage:
        task = LLMTask("my_llm_task", context_dir="/path/to/context")
        
        # Send prompt to LLM
        response = llm_api.call(prompt=task.get_current_prompt())
        
        # Save response
        task.save_response(response, tool_calls=[])
        
        # Checkpoint
        task.checkpoint(step="analyze_requirements")
        
        # Resume later
        if task.should_resume():
            start_from = task.last_step
    """
    
    def __init__(self, task_name: str, context_dir: Optional[str] = None):
        """
        Initialize LLM task manager.
        
        Args:
            task_name: Unique task identifier
            context_dir: Directory for context files (default: ~/.openclaw/llm-tasks/{task_name})
        """
        self.task_name = task_name
        self.context_dir = Path(context_dir) if context_dir else Path.home() / ".openclaw" / "llm-tasks" / task_name
        self.context_dir.mkdir(parents=True, exist_ok=True)
        
        # Underlying safe task
        self.safe_task = SafeTask(f"llm_{task_name}")
        
        # Task state files
        self.state_file = self.context_dir / "task_state.json"
        self.context_file = self.context_dir / "context.md"
        self.output_file = self.context_dir / "output.md"
        self.history_file = self.context_dir / "history.jsonl"
        
        # Load existing state or initialize
        self.state = self._load_state()
        
        print(f"✅ LLMTask '{task_name}' initialized")
        if self.state.get("last_step"):
            print(f"   🔄 Resuming from: {self.state['last_step']}")
            print(f"   📝 Context: {self.context_file}")
            print(f"   📝 Output: {self.output_file}")
    
    def _load_state(self) -> Dict:
        """Load task state from file."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            "task_name": self.task_name,
            "started_at": datetime.now().isoformat(),
            "last_step": None,
            "step_count": 0,
            "status": "in_progress",
            "total_context_tokens": 0,
            "total_output_tokens": 0,
            "conversation_turns": 0
        }
    
    def _save_state(self):
        """Save task state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)
        self.safe_task.save_checkpoint(
            step=self.state["step_count"],
            metadata={
                "last_step": self.state["last_step"],
                "status": self.state["status"],
                "context_tokens": self.state["total_context_tokens"],
                "output_tokens": self.state["total_output_tokens"]
            }
        )
    
    def set_context(self, content: str, token_count: int = 0):
        """
        Save current context (prompt sent to LLM).
        
        Args:
            content: Full prompt/context text
            token_count: Approximate token count (optional)
        """
        self.context_file.write_text(content)
        
        if token_count > 0:
            self.state["total_context_tokens"] += token_count
        else:
            # Estimate tokens (rough: 4 chars ≈ 1 token)
            self.state["total_context_tokens"] += len(content) // 4
        
        self.state["last_context_update"] = datetime.now().isoformat()
        self._save_state()
        
        print(f"   💾 Context saved: {self.context_file} ({len(content)} chars)")
    
    def set_output(self, content: str, token_count: int = 0):
        """
        Save LLM output/response.
        
        Args:
            content: LLM response text
            token_count: Actual token count from API (optional)
        """
        self.output_file.write_text(content)
        
        if token_count > 0:
            self.state["total_output_tokens"] += token_count
        else:
            # Estimate tokens
            self.state["total_output_tokens"] += len(content) // 4
        
        self.state["last_output_update"] = datetime.now().isoformat()
        self._save_state()
        
        print(f"   💾 Output saved: {self.output_file} ({len(content)} chars)")
    
    def save_response(self, response: str, tool_calls: List[Dict] = None, token_count: int = 0):
        """
        Save LLM response with optional tool calls.
        
        Args:
            response: LLM response text
            tool_calls: List of tool calls from LLM
            token_count: Output token count
        """
        self.set_output(response, token_count)
        
        # Save to history
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "turn": self.state["conversation_turns"],
            "response": response,
            "tool_calls": tool_calls or [],
            "token_count": token_count
        }
        
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(history_entry) + "\n")
        
        self.state["conversation_turns"] += 1
        self._save_state()
    
    def get_context(self) -> str:
        """Get saved context (last prompt)."""
        if not self.context_file.exists():
            return ""
        return self.context_file.read_text()
    
    def get_output(self) -> str:
        """Get saved output (last response)."""
        if not self.output_file.exists():
            return ""
        return self.output_file.read_text()
    
    def get_current_prompt(self) -> str:
        """
        Get the current prompt for LLM API.
        
        If resuming, returns the saved context.
        If new task, returns empty string (caller should set initial prompt).
        """
        if self.context_file.exists():
            return self.context_file.read_text()
        return ""
    
    def get_last_response(self) -> str:
        """Get the last LLM response (for continuation)."""
        if self.output_file.exists():
            return self.output_file.read_text()
        return ""
    
    def checkpoint(self, step_name: str, metadata: Dict = None):
        """
        Create a checkpoint with step name.
        
        Args:
            step_name: Human-readable step identifier
            metadata: Additional metadata to save
        """
        self.state["last_step"] = step_name
        self.state["step_count"] += 1
        self.state["metadata"] = metadata or {}
        self.state["last_checkpoint"] = datetime.now().isoformat()
        self._save_state()
        
        print(f"   💾 Checkpoint: {step_name} (step {self.state['step_count']})")
    
    def should_resume(self) -> bool:
        """Check if task should resume from checkpoint."""
        return self.state.get("last_step") is not None
    
    def get_conversation_history(self, max_turns: int = 10) -> List[Dict]:
        """
        Get recent conversation history.
        
        Args:
            max_turns: Maximum number of turns to return
            
        Returns:
            List of conversation turns (most recent first)
        """
        if not self.history_file.exists():
            return []
        
        history = []
        with open(self.history_file, 'r') as f:
            for line in f:
                history.append(json.loads(line))
        
        # Return most recent turns
        return history[-max_turns:]
    
    def build_context_window(self, system_prompt: str, max_tokens: int = 4000) -> str:
        """
        Build optimized context window for LLM.
        
        Includes:
        1. System prompt
        2. Recent conversation history
        3. Current task state
        
        Args:
            system_prompt: System instructions
            max_tokens: Maximum context window size
            
        Returns:
            Optimized context string
        """
        parts = [system_prompt]
        
        # Add recent history (most recent first)
        history = self.get_conversation_history(max_turns=5)
        for turn in reversed(history):
            response = turn.get("response", "")
            # Truncate if too long
            if len(response) > 500:
                response = response[:500] + "..."
            parts.append(f"\nPrevious response:\n{response}")
        
        # Add task state
        parts.append(f"\nCurrent task state:")
        parts.append(f"- Step: {self.state['last_step']}")
        parts.append(f"- Progress: {self.state['step_count']} steps completed")
        parts.append(f"- Status: {self.state['status']}")
        
        # Combine and check length
        context = "\n".join(parts)
        
        if len(context) > max_tokens * 4:  # Rough token estimate
            print(f"   ⚠️  Context truncated to {max_tokens} tokens")
            context = context[:max_tokens * 4]
        
        return context
    
    def mark_complete(self):
        """Mark task as complete."""
        self.state["status"] = "complete"
        self.state["completed_at"] = datetime.now().isoformat()
        self._save_state()
        self.safe_task.mark_complete()
        
        print(f"✅ Task '{self.task_name}' completed!")
        print(f"   Total steps: {self.state['step_count']}")
        print(f"   Context tokens: {self.state['total_context_tokens']}")
        print(f"   Output tokens: {self.state['total_output_tokens']}")
    
    def mark_failed(self, error: str):
        """Mark task as failed."""
        self.state["status"] = "failed"
        self.state["error"] = error
        self.state["failed_at"] = datetime.now().isoformat()
        self._save_state()
        self.safe_task.add_error(error)
        self.safe_task.mark_failed(error)
        
        print(f"❌ Task '{self.task_name}' failed: {error}")
    
    def get_status(self) -> Dict:
        """Get current task status."""
        return {
            "task_name": self.task_name,
            "status": self.state["status"],
            "last_step": self.state["last_step"],
            "step_count": self.state["step_count"],
            "context_file": str(self.context_file),
            "output_file": str(self.output_file),
            "context_tokens": self.state["total_context_tokens"],
            "output_tokens": self.state["total_output_tokens"],
            "conversation_turns": self.state["conversation_turns"]
        }
    
    def __str__(self) -> str:
        """String representation."""
        status = self.get_status()
        return f"LLMTask({status['task_name']}, step={status['step_count']}, status={status['status']})"


# Convenience functions
def create_llm_task(task_name: str, context_dir: str = None) -> LLMTask:
    """Create new LLM task manager."""
    return LLMTask(task_name, context_dir)


def resume_llm_task(task_name: str) -> Optional[LLMTask]:
    """
    Resume existing LLM task if it has checkpoints.
    
    Returns None if task doesn't exist or is complete.
    """
    task = LLMTask(task_name)
    
    if task.state.get("status") == "complete":
        print(f"⏭️  Task '{task_name}' already complete")
        return None
    
    if task.should_resume():
        print(f"🔄 Resuming task '{task_name}' from step: {task.state['last_step']}")
        return task
    else:
        print(f"🆕 Starting fresh task '{task_name}'")
        return task

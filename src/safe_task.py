#!/usr/bin/env python3
"""
Safe Task Framework - Prevents long-running tasks from losing progress

Usage:
    from safe_task import SafeTask
    
    task = SafeTask("my_task_name")
    task.save_checkpoint(step=5, total_steps=100)
    task.heartbeat()  # Update timestamp
    task.mark_complete()
"""

import json
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

PROGRESS_DIR = Path("~/.openclaw/workspace/memory")
PROGRESS_FILE = PROGRESS_DIR / "progress.json"


class SafeTask:
    """
    Wrapper for long-running tasks with automatic checkpointing and recovery.
    
    Features:
    - Automatic checkpoint saving
    - Heartbeat monitoring
    - Graceful shutdown on SIGTERM/SIGINT
    - Resume from last checkpoint
    - Error tracking
    """
    
    def __init__(self, task_name: str, progress_file: Optional[str] = None):
        """
        Initialize a safe task.
        
        Args:
            task_name: Unique name for this task
            progress_file: Optional custom path (default: memory/progress.json)
        """
        self.task_name = task_name
        self.progress_file = Path(progress_file) if progress_file else PROGRESS_FILE
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing progress or create new
        self.progress = self._load_progress()
        
        # Register shutdown handlers
        signal.signal(signal.SIGTERM, self._save_and_exit)
        signal.signal(signal.SIGINT, self._save_and_exit)
        
        print(f"✅ Task '{task_name}' initialized")
        if self.progress.get("current_step", 0) > 0:
            print(f"   🔄 Resuming from step {self.progress['current_step']} "
                  f"({self.progress.get('progress_percent', 0)}%)")
    
    def _load_progress(self) -> Dict[str, Any]:
        """Load progress from file or create new."""
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                # Only use if it's for this task
                if data.get("task_name") == self.task_name:
                    return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        
        # Return new progress structure
        return {
            "task_name": self.task_name,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "last_heartbeat": datetime.utcnow().isoformat() + "Z",
            "status": "in_progress",
            "current_step": 0,
            "total_steps": 0,
            "checkpoint_file": None,
            "progress_percent": 0,
            "retry_count": 0,
            "error_history": [],
            "resume_command": f"python3 <script.py> --resume",
            "metadata": {}
        }
    
    def _save_progress(self):
        """Save progress to file."""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def save_checkpoint(
        self,
        step: Optional[int] = None,
        total_steps: Optional[int] = None,
        checkpoint_file: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Save current checkpoint.
        
        Args:
            step: Current step number (updates if provided)
            total_steps: Total steps for progress calculation
            checkpoint_file: Path to checkpoint file (model weights, etc.)
            metadata: Additional task-specific data
        """
        if step is not None:
            self.progress["current_step"] = step
        if total_steps is not None:
            self.progress["total_steps"] = total_steps
        if checkpoint_file:
            self.progress["checkpoint_file"] = checkpoint_file
        if metadata:
            self.progress["metadata"].update(metadata)
        
        # Update heartbeat
        self.progress["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
        
        # Calculate progress percentage
        if self.progress["total_steps"] > 0:
            self.progress["progress_percent"] = round(
                (self.progress["current_step"] / self.progress["total_steps"]) * 100, 2
            )
        
        self._save_progress()
        
        pct = self.progress.get("progress_percent", 0)
        print(f"💾 Checkpoint saved: Step {self.progress['current_step']}/"
              f"{self.progress['total_steps']} ({pct}%)")
    
    def heartbeat(self):
        """Update heartbeat timestamp without changing other state."""
        self.progress["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
        self._save_progress()
    
    def mark_complete(self, exit_code: int = 0):
        """Mark task as complete."""
        self.progress["status"] = "complete"
        self.progress["completed_at"] = datetime.utcnow().isoformat() + "Z"
        self.progress["exit_code"] = exit_code
        self._save_progress()
        print(f"✅ Task '{self.task_name}' completed successfully!")
    
    def mark_failed(self, error: str):
        """Mark task as failed with error message."""
        self.progress["status"] = "failed"
        self.add_error(error)
        self._save_progress()
        print(f"❌ Task '{self.task_name}' failed: {error}")
    
    def add_error(self, error: str):
        """Add error to history."""
        self.progress["error_history"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(error)
        })
        self.progress["retry_count"] = self.progress.get("retry_count", 0) + 1
        self._save_progress()
    
    def _save_and_exit(self, signum, frame):
        """Handle graceful shutdown on SIGTERM/SIGINT."""
        print(f"\n⚠️  Received signal {signum}, saving checkpoint...")
        self.save_checkpoint()
        print("✅ Checkpoint saved. Task can be resumed.")
        sys.exit(0)
    
    def can_resume(self) -> bool:
        """Check if task can be resumed from checkpoint."""
        return (
            self.progress.get("status") == "in_progress" and
            self.progress.get("current_step", 0) > 0
        )
    
    def get_status(self) -> str:
        """Get human-readable status string."""
        status = self.progress.get("status", "unknown")
        step = self.progress.get("current_step", 0)
        total = self.progress.get("total_steps", 0)
        pct = self.progress.get("progress_percent", 0)
        
        return f"{status}: {step}/{total} steps ({pct}%)"
    
    def reset(self):
        """Reset task progress (start fresh)."""
        self.progress = self._load_progress()
        self.progress["status"] = "in_progress"
        self.progress["current_step"] = 0
        self.progress["progress_percent"] = 0
        self.progress["error_history"] = []
        self._save_progress()
        print(f"🔄 Task '{self.task_name}' reset - starting fresh")


def check_stuck_task() -> bool:
    """
    Check if current task is stuck (no heartbeat for >60 minutes).
    
    Returns:
        True if task is stuck, False otherwise
    """
    if not PROGRESS_FILE.exists():
        return False
    
    try:
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
    except json.JSONDecodeError:
        return False
    
    if progress.get("status") != "in_progress":
        return False
    
    try:
        last_heartbeat = datetime.fromisoformat(
            progress["last_heartbeat"].replace("Z", "+00:00")
        )
        now = datetime.utcnow().replace(tzinfo=last_heartbeat.tzinfo)
        hours_since = (now - last_heartbeat).total_seconds() / 3600
        
        if hours_since > 1:
            print(f"🚨 WARNING: Task '{progress['task_name']}' "
                  f"hasn't updated in {hours_since:.1f} hours!")
            return True
    except (KeyError, ValueError):
        pass
    
    return False


if __name__ == "__main__":
    # Demo usage
    import time
    
    task = SafeTask("demo_task")
    
    # Simulate a 10-step task
    total_steps = 10
    task.progress["total_steps"] = total_steps
    
    # Resume if we have a checkpoint
    start_step = task.progress.get("current_step", 0)
    
    print(f"\n🚀 Starting demo task from step {start_step}...\n")
    
    for step in range(start_step, total_steps):
        print(f"Processing step {step + 1}/{total_steps}")
        time.sleep(0.5)  # Simulate work
        
        # Save checkpoint every 2 steps
        task.save_checkpoint(step=step + 1)
        
        # Heartbeat (in real tasks, do this every 30-60 seconds)
        task.heartbeat()
    
    task.mark_complete()
    print(f"\n🎉 Demo complete! Check {PROGRESS_FILE} for progress data.")

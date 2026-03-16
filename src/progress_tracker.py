#!/usr/bin/env python3
"""
Progress Tracking Utility for Long-Running Tasks

Usage:
    python3 progress_tracker.py --init "task_name"
    python3 progress_tracker.py --update "task_name" --step 3 --total 10
    python3 progress_tracker.py --complete "task_name"
    python3 progress_tracker.py --resume "task_name"
    python3 progress_tracker.py --status "task_name"

All long-running tasks should use this utility for checkpointing and resume capability.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROGRESS_DIR = Path("~/.openclaw/workspace/memory")
PROGRESS_FILE = PROGRESS_DIR / "progress.json"

def ensure_progress_dir():
    """Ensure progress directory exists."""
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

def read_progress():
    """Read current progress file."""
    if not PROGRESS_FILE.exists():
        return None
    with open(PROGRESS_FILE, "r") as f:
        return json.load(f)

def write_progress(data):
    """Write progress to file."""
    ensure_progress_dir()
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def init_task(task_name, total_steps=None):
    """Initialize a new task."""
    data = {
        "task_name": task_name,
        "started_at": datetime.utcnow().isoformat() + "Z",
        "last_checkpoint": datetime.utcnow().isoformat() + "Z",
        "status": "in_progress",
        "current_step": 0,
        "total_steps": total_steps,
        "checkpoint_file": None,
        "progress_percent": 0,
        "retry_count": 0,
        "last_heartbeat": datetime.utcnow().isoformat() + "Z",
        "next_checkpoint_in_minutes": 30,
        "error_history": [],
        "resume_command": f"python3 progress_tracker.py --resume {task_name}",
        "task_metadata": {}
    }
    write_progress(data)
    print(f"✅ Task '{task_name}' initialized")
    return data

def update_progress(task_name, current_step=None, total_steps=None, progress_percent=None, checkpoint_file=None, metadata=None):
    """Update task progress."""
    data = read_progress()
    if not data or data["task_name"] != task_name:
        print(f"❌ No existing task found: {task_name}")
        return None
    
    if current_step is not None:
        data["current_step"] = current_step
    if total_steps is not None:
        data["total_steps"] = total_steps
    if progress_percent is not None:
        data["progress_percent"] = progress_percent
    if checkpoint_file is not None:
        data["checkpoint_file"] = checkpoint_file
    if metadata:
        data["task_metadata"].update(metadata)
    
    data["last_checkpoint"] = datetime.utcnow().isoformat() + "Z"
    data["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
    data["status"] = "in_progress"
    
    # Calculate progress if not provided
    if progress_percent is None and total_steps and data["current_step"]:
        data["progress_percent"] = round((data["current_step"] / total_steps) * 100, 2)
    
    write_progress(data)
    print(f"✅ Progress updated: {data['current_step']}/{data['total_steps']} ({data['progress_percent']}%)")
    return data

def complete_task(task_name, exit_code=0):
    """Mark task as complete."""
    data = read_progress()
    if not data or data["task_name"] != task_name:
        print(f"❌ No existing task found: {task_name}")
        return None
    
    data["status"] = "complete"
    data["completed_at"] = datetime.utcnow().isoformat() + "Z"
    data["exit_code"] = exit_code
    data["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
    
    write_progress(data)
    print(f"✅ Task '{task_name}' completed with exit code {exit_code}")
    return data

def pause_task(task_name, error=None):
    """Pause task (graceful shutdown)."""
    data = read_progress()
    if not data or data["task_name"] != task_name:
        print(f"❌ No existing task found: {task_name}")
        return None
    
    data["status"] = "paused"
    if error:
        data["error_history"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": error
        })
    data["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
    
    write_progress(data)
    print(f"⏸️  Task '{task_name}' paused")
    return data

def resume_task(task_name):
    """Check if task can be resumed."""
    data = read_progress()
    if not data:
        print(f"❌ No progress file found")
        return None
    
    if data["task_name"] != task_name:
        print(f"⚠️  Progress file is for task '{data['task_name']}', not '{task_name}'")
        print("   Delete progress file to start fresh, or use matching task name")
        return None
    
    if data["status"] == "in_progress":
        print(f"🔄 Task '{task_name}' can be resumed")
        print(f"   Current step: {data['current_step']}/{data['total_steps']}")
        print(f"   Progress: {data['progress_percent']}%")
        print(f"   Last heartbeat: {data['last_heartbeat']}")
        if data.get("checkpoint_file"):
            print(f"   Checkpoint: {data['checkpoint_file']}")
        return data
    elif data["status"] == "complete":
        print(f"✅ Task '{task_name}' already complete")
        return data
    elif data["status"] == "paused":
        print(f"⏸️  Task '{task_name}' was paused")
        print(f"   Errors: {len(data.get('error_history', []))}")
        return data
    
    return data

def get_status(task_name):
    """Get current task status."""
    data = read_progress()
    if not data:
        print(f"❌ No progress file found")
        return None
    
    print(f"\n📊 Task: {data['task_name']}")
    print(f"   Status: {data['status']}")
    print(f"   Progress: {data['current_step']}/{data['total_steps']} ({data['progress_percent']}%)")
    print(f"   Started: {data['started_at']}")
    print(f"   Last heartbeat: {data['last_heartbeat']}")
    if data.get("checkpoint_file"):
        print(f"   Checkpoint: {data['checkpoint_file']}")
    if data.get("error_history"):
        print(f"   Errors: {len(data['error_history'])}")
        for err in data["error_history"][-3:]:  # Show last 3 errors
            print(f"     - {err['timestamp']}: {err['error']}")
    
    return data

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "--init":
        task_name = sys.argv[2] if len(sys.argv) > 2 else "unnamed_task"
        init_task(task_name)
    
    elif action == "--update":
        task_name = sys.argv[2]
        current_step = None
        total_steps = None
        progress_percent = None
        checkpoint_file = None
        
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--step" and i + 1 < len(sys.argv):
                current_step = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--total" and i + 1 < len(sys.argv):
                total_steps = int(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--percent" and i + 1 < len(sys.argv):
                progress_percent = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--checkpoint" and i + 1 < len(sys.argv):
                checkpoint_file = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        update_progress(task_name, current_step, total_steps, progress_percent, checkpoint_file)
    
    elif action == "--complete":
        task_name = sys.argv[2]
        exit_code = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        complete_task(task_name, exit_code)
    
    elif action == "--pause":
        task_name = sys.argv[2]
        error = sys.argv[3] if len(sys.argv) > 3 else None
        pause_task(task_name, error)
    
    elif action == "--resume":
        task_name = sys.argv[2] if len(sys.argv) > 2 else None
        resume_task(task_name)
    
    elif action == "--status":
        task_name = sys.argv[2] if len(sys.argv) > 2 else None
        get_status(task_name)
    
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()

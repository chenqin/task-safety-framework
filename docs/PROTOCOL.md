# Task Safety Protocol v1.0

**Purpose:** Ensure long-running tasks never lose progress or stall silently.

---

## Core Principles

1. **Checkpoint Everything** - Save state after every meaningful step
2. **Heartbeat Monitoring** - Write timestamp every 5-10 minutes
3. **Auto-Resume** - Tasks can restart from last checkpoint
4. **Stuck Detection** - Alert if no heartbeat for >60 minutes
5. **Graceful Shutdown** - Handle SIGTERM/SIGINT cleanly

---

## Implementation

### 1. Progress File Schema

```json
{
  "task_name": "string",
  "started_at": "ISO-8601 timestamp",
  "last_heartbeat": "ISO-8601 timestamp",
  "status": "in_progress" | "complete" | "paused" | "failed",
  "current_step": "number",
  "total_steps": "number",
  "checkpoint_file": "path to checkpoint",
  "progress_percent": "0-100",
  "retry_count": "number",
  "error_history": [{"timestamp": "...", "error": "..."}],
  "resume_command": "command to restart",
  "metadata": {}
}
```

### 2. Mandatory Checkpoints

**Save after:**
- Every batch completion (training epochs, data batches)
- Every 5-10 minutes (heartbeat)
- Before expensive operations
- On SIGTERM/SIGINT (graceful shutdown)

**Format:**
```python
import signal
import json
from datetime import datetime

class SafeTask:
    def __init__(self, task_name, progress_file="memory/progress.json"):
        self.task_name = task_name
        self.progress_file = progress_file
        self.progress = self.load_progress()
        
        # Register shutdown handlers
        signal.signal(signal.SIGTERM, self.save_and_exit)
        signal.signal(signal.SIGINT, self.save_and_exit)
    
    def load_progress(self):
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                if data.get('task_name') == self.task_name:
                    return data
        except FileNotFoundError:
            pass
        return {
            "task_name": self.task_name,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "last_heartbeat": datetime.utcnow().isoformat() + "Z",
            "status": "in_progress",
            "current_step": 0,
            "total_steps": 0,
            "progress_percent": 0,
            "retry_count": 0,
            "error_history": []
        }
    
    def save_checkpoint(self, step=None, checkpoint_file=None, metadata=None):
        self.progress["current_step"] = step or self.progress["current_step"]
        self.progress["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
        
        if checkpoint_file:
            self.progress["checkpoint_file"] = checkpoint_file
        if metadata:
            self.progress["metadata"].update(metadata)
        
        # Calculate progress
        if self.progress["total_steps"] > 0:
            self.progress["progress_percent"] = round(
                (self.progress["current_step"] / self.progress["total_steps"]) * 100, 2
            )
        
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def heartbeat(self):
        """Quick heartbeat - just update timestamp"""
        self.progress["last_heartbeat"] = datetime.utcnow().isoformat() + "Z"
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def save_and_exit(self, signum, frame):
        """Graceful shutdown handler"""
        print(f"\n⚠️  Received signal {signum}, saving checkpoint...")
        self.save_checkpoint()
        print("✅ Checkpoint saved. Can resume with: " + self.progress.get("resume_command", ""))
        exit(0)
    
    def mark_complete(self):
        self.progress["status"] = "complete"
        self.progress["completed_at"] = datetime.utcnow().isoformat() + "Z"
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
        print("✅ Task complete!")
    
    def add_error(self, error_msg):
        self.progress["error_history"].append({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": str(error_msg)
        })
        self.progress["retry_count"] = self.progress.get("retry_count", 0) + 1
```

### 3. Usage Example

```python
from safe_task import SafeTask
import time

def long_running_task():
    task = SafeTask("training_model_v1")
    
    # Resume if checkpoint exists
    if task.progress["current_step"] > 0:
        print(f"🔄 Resuming from step {task.progress['current_step']}")
        start_step = task.progress["current_step"]
        # Load checkpoint data here...
    else:
        start_step = 0
    
    total_steps = 100
    task.progress["total_steps"] = total_steps
    
    try:
        for step in range(start_step, total_steps):
            # Do work
            print(f"Processing step {step+1}/{total_steps}")
            time.sleep(1)  # Simulated work
            
            # Save checkpoint every 10 steps
            if (step + 1) % 10 == 0:
                task.save_checkpoint(step=step+1, metadata={"batch": step+1})
            
            # Heartbeat every 30 seconds (in real task)
            # task.heartbeat()
        
        task.mark_complete()
    
    except Exception as e:
        task.add_error(str(e))
        task.save_checkpoint()
        raise

if __name__ == "__main__":
    long_running_task()
```

### 4. Heartbeat Monitor (Cron Job)

**Already running:** `Monitor Progress Heartbeats (Long-Running Tasks)` every 10 minutes

**What it does:**
- Reads `memory/progress.json`
- Alerts if `last_heartbeat` > 60 min old AND `status = in_progress`
- Checks if process is still alive via PID

### 5. Recovery Script

```python
#!/usr/bin/env python3
"""Check for stuck tasks and offer recovery"""
import json
from datetime import datetime, timedelta
from pathlib import Path

PROGRESS_FILE = Path("memory/progress.json")

def check_stuck_tasks():
    if not PROGRESS_FILE.exists():
        print("✅ No running tasks")
        return
    
    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)
    
    if progress.get("status") != "in_progress":
        print(f"✅ Task status: {progress.get('status')}")
        return
    
    last_heartbeat = datetime.fromisoformat(progress["last_heartbeat"].replace("Z", "+00:00"))
    now = datetime.utcnow().replace(tzinfo=last_heartbeat.tzinfo)
    hours_since_heartbeat = (now - last_heartbeat).total_seconds() / 3600
    
    if hours_since_heartbeat > 1:
        print(f"🚨 STUCK TASK DETECTED!")
        print(f"   Task: {progress['task_name']}")
        print(f"   Last heartbeat: {hours_since_heartbeat:.1f} hours ago")
        print(f"   Progress: {progress['progress_percent']}%")
        print(f"   Errors: {len(progress.get('error_history', []))}")
        print(f"\n🔧 Recovery options:")
        print(f"   1. Resume: {progress.get('resume_command', 'N/A')}")
        print(f"   2. Restart: Delete {PROGRESS_FILE} and run fresh")
        print(f"   3. Diagnose: Check logs for errors")
    else:
        print(f"✅ Task healthy - heartbeat {hours_since_heartbeat:.1f} hours ago")

if __name__ == "__main__":
    check_stuck_tasks()
```

---

## Best Practices

### For Task Authors:
1. **Wrap tasks in SafeTask class** - automatic checkpointing
2. **Save checkpoints frequently** - every batch/epoch/iteration
3. **Handle signals** - SIGTERM/SIGINT trigger graceful save
4. **Log errors** - add to error_history for debugging
5. **Set resume_command** - document how to restart

### For Operators:
1. **Check progress.json** - see current task status
2. **Monitor heartbeats** - cron job alerts on stuck tasks
3. **Review error_history** - understand failures
4. **Resume from checkpoint** - don't restart from scratch

---

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Heartbeat age | >30 min | >60 min |
| Retry count | >3 | >5 |
| Error rate | >10% | >25% |
| Progress stagnation | >1 hour | >2 hours |

---

## Pattern-Key: `task_safety.checkpoint_heartbeat`

**Cross-reference:** See `memory/progress.json` for live task state

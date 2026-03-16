# Task Safety Framework

**Purpose:** Prevent long-running tasks from losing progress or stalling silently.

---

## Quick Start

### For Task Authors

```python
from safe_task import SafeTask

# Initialize
task = SafeTask("my_training_job")

# Save checkpoints during work
task.save_checkpoint(step=10, total_steps=100, metadata={"epoch": 5})

# Heartbeat (every 5-10 minutes)
task.heartbeat()

# Mark complete when done
task.mark_complete()
```

### For Operators

```bash
# Check if any tasks are stuck
python3 task_recovery.py --status

# Detailed diagnosis
python3 task_recovery.py --diagnose

# Reset all tasks (start fresh)
python3 task_recovery.py --reset
```

---

## Files

| File | Purpose |
|------|---------|
| `safe_task.py` | Core framework - import this in your tasks |
| `task_recovery.py` | CLI tool to check/recover stuck tasks |
| `task_safety_protocol.md` | Full documentation and best practices |
| `test_safe_task.py` | Unit tests (run to verify framework) |

---

## Key Features

✅ **Automatic Checkpointing** - Save progress after every step
✅ **Heartbeat Monitoring** - Detect stuck tasks (>60 min no update)
✅ **Graceful Shutdown** - Handle SIGTERM/SIGINT by saving state
✅ **Auto-Resume** - Restart from last checkpoint on crash
✅ **Error Tracking** - Log all errors for debugging
✅ **Progress Tracking** - View % complete at any time

---

## Integration with Cron

**Already running:**
- `Monitor Progress Heartbeats (Long-Running Tasks)` - Every 10 minutes
- `Auto-Report Running Tasks` - Every 10 minutes

These cron jobs automatically alert if a task stalls.

---

## Pattern-Key: `task_safety.checkpoint_heartbeat`

**Cross-reference:** See `HEARTBEAT.md` for monitoring protocol

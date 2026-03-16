#!/usr/bin/env python3
"""
Task Recovery Tool - Diagnose and recover stuck long-running tasks

Usage:
    python3 task_recovery.py --status        # Check for stuck tasks
    python3 task_recovery.py --diagnose     # Detailed diagnosis
    python3 task_recovery.py --reset        # Reset all tasks (start fresh)
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROGRESS_FILE = Path("~/.openclaw/workspace/memory/progress.json")


def load_progress():
    """Load progress file if it exists."""
    if not PROGRESS_FILE.exists():
        return None
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def check_status():
    """Check if any tasks are stuck."""
    progress = load_progress()
    
    if not progress:
        print("✅ No running tasks")
        return 0
    
    status = progress.get("status", "unknown")
    
    if status != "in_progress":
        print(f"✅ Task '{progress['task_name']}': {status}")
        if status == "complete":
            print(f"   Progress: {progress.get('progress_percent', 0)}%")
        return 0
    
    # Check heartbeat age
    try:
        last_heartbeat = datetime.fromisoformat(
            progress["last_heartbeat"].replace("Z", "+00:00")
        )
        now = datetime.utcnow().replace(tzinfo=last_heartbeat.tzinfo)
        hours_since = (now - last_heartbeat).total_seconds() / 3600
        
        if hours_since > 1:
            print(f"🚨 STUCK TASK DETECTED!")
            print(f"   Task: {progress['task_name']}")
            print(f"   Status: {status}")
            print(f"   Last heartbeat: {hours_since:.1f} hours ago")
            print(f"   Progress: {progress.get('current_step', 0)}/{progress.get('total_steps', 'N/A')}")
            print(f"   Percent: {progress.get('progress_percent', 0)}%")
            print(f"   Errors: {len(progress.get('error_history', []))}")
            
            if progress.get("checkpoint_file"):
                print(f"   Checkpoint: {progress['checkpoint_file']}")
            
            if progress.get("resume_command"):
                print(f"\n🔧 Resume command: {progress['resume_command']}")
            
            return 1
        
        elif hours_since > 0.5:
            print(f"⚠️  Task '{progress['task_name']}' hasn't updated in {hours_since:.1f} hours")
            print(f"   Progress: {progress.get('progress_percent', 0)}%")
            return 0
        
        else:
            print(f"✅ Task '{progress['task_name']}' is healthy")
            print(f"   Last heartbeat: {hours_since:.1f} hours ago")
            print(f"   Progress: {progress.get('progress_percent', 0)}%")
            return 0
    
    except (KeyError, ValueError) as e:
        print(f"⚠️  Could not parse heartbeat: {e}")
        return 1


def diagnose():
    """Detailed diagnosis of current task."""
    progress = load_progress()
    
    if not progress:
        print("No running tasks to diagnose")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 DIAGNOSIS: {progress['task_name']}")
    print(f"{'='*60}")
    
    # Basic info
    print(f"\n📋 Basic Info:")
    print(f"   Status: {progress.get('status', 'unknown')}")
    print(f"   Started: {progress.get('started_at', 'N/A')}")
    print(f"   Current step: {progress.get('current_step', 0)}/{progress.get('total_steps', 'N/A')}")
    print(f"   Progress: {progress.get('progress_percent', 0)}%")
    
    # Heartbeat
    try:
        last_heartbeat = datetime.fromisoformat(
            progress["last_heartbeat"].replace("Z", "+00:00")
        )
        now = datetime.utcnow().replace(tzinfo=last_heartbeat.tzinfo)
        hours_since = (now - last_heartbeat).total_seconds() / 3600
        
        print(f"\n💓 Heartbeat:")
        print(f"   Last update: {progress['last_heartbeat']}")
        print(f"   Age: {hours_since:.1f} hours")
        print(f"   Status: {'🚨 STUCK' if hours_since > 1 else '✅ OK'}")
    except:
        print(f"\n💓 Heartbeat: Could not parse")
    
    # Checkpoint
    if progress.get("checkpoint_file"):
        checkpoint_path = Path(progress["checkpoint_file"])
        exists = checkpoint_path.exists()
        size = checkpoint_path.stat().st_size / (1024*1024) if exists else 0
        
        print(f"\n💾 Checkpoint:")
        print(f"   Path: {checkpoint_path}")
        print(f"   Exists: {'✅' if exists else '❌'}")
        print(f"   Size: {size:.1f} MB" if exists else "")
    
    # Error history
    errors = progress.get("error_history", [])
    if errors:
        print(f"\n❌ Error History ({len(errors)} errors):")
        for i, err in enumerate(errors[-3:], 1):  # Last 3 errors
            print(f"   {i}. {err.get('timestamp', 'N/A')}: {err.get('error', 'Unknown')[:80]}")
    
    # Metadata
    metadata = progress.get("metadata", {})
    if metadata:
        print(f"\n📦 Metadata:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
    
    # Recommendations
    print(f"\n🔧 Recommendations:")
    
    try:
        hours_since = (now - last_heartbeat).total_seconds() / 3600
    except:
        hours_since = 0
    
    if hours_since > 1:
        print(f"   1. 🚨 Task appears stuck - consider restarting")
        print(f"   2. Check logs for errors")
        if progress.get("resume_command"):
            print(f"   3. Resume with: {progress['resume_command']}")
        else:
            print(f"   3. Kill process and restart from checkpoint")
    elif hours_since > 0.5:
        print(f"   1. ⚠️  Task is slow - monitor closely")
        print(f"   2. Check system resources (CPU, GPU, disk)")
    else:
        print(f"   1. ✅ Task appears healthy - continue monitoring")
    
    print(f"\n{'='*60}\n")


def reset():
    """Reset all task progress."""
    if PROGRESS_FILE.exists():
        print(f"🗑️  Deleting {PROGRESS_FILE}")
        PROGRESS_FILE.unlink()
        print("✅ All tasks reset - ready to start fresh")
    else:
        print("✅ No tasks to reset")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "--status":
        sys.exit(check_status())
    elif action == "--diagnose":
        diagnose()
    elif action == "--reset":
        reset()
    else:
        print(f"Unknown action: {action}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

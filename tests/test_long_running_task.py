#!/usr/bin/env python3
"""
Test Long-Running Task - Simulates a realistic long-running task
with checkpointing, heartbeat, and recovery capabilities.

Usage:
    python3 test_long_running_task.py [--resume]

This task simulates processing 100 items with:
- Checkpoint every 10 items
- Heartbeat every item
- Graceful shutdown on SIGTERM/SIGINT
- Resume capability from last checkpoint
"""

import time
import random
import sys
from safe_task import SafeTask

def simulate_work(item_id):
    """Simulate processing work with random duration."""
    # Random work time between 0.1-0.3 seconds
    work_time = random.uniform(0.1, 0.3)
    time.sleep(work_time)
    return f"Processed item {item_id} in {work_time:.2f}s"

def run_task(resume=False):
    """Run the long-running task with checkpointing."""
    task = SafeTask("test_long_running_task")
    
    # Task configuration
    total_items = 100
    
    # Set total steps
    task.save_checkpoint(total_steps=total_items)
    
    # Determine starting point
    if resume:
        start_item = task.progress.get("current_step", 0)
        print(f"🔄 RESUMING from item {start_item + 1}/{total_items}")
    else:
        start_item = task.progress.get("current_step", 0)
        if start_item > 0:
            print(f"📊 Found existing checkpoint at item {start_item}")
            print(f"   Resume from checkpoint? Setting start to {start_item}")
        else:
            print(f"🚀 Starting fresh from item 0")
    
    print(f"\n📊 Task Configuration:")
    print(f"   Total items: {total_items}")
    print(f"   Starting from: {start_item + 1 if start_item > 0 else 1}")
    print(f"   Checkpoint every: 10 items")
    print(f"   Heartbeat: Every item")
    print()
    
    # Process items
    try:
        for item in range(start_item, total_items):
            # Simulate work
            result = simulate_work(item)
            
            # Update progress
            task.save_checkpoint(
                step=item + 1,
                metadata={
                    "last_processed": item,
                    "result": result
                }
            )
            
            # Heartbeat
            task.heartbeat()
            
            # Print progress
            progress = (item + 1) / total_items * 100
            status = f"{item + 1:3d}/{total_items} ({progress:5.1f}%) - {result}"
            print(f"   {status}")
            
            # Save checkpoint every 10 items
            if (item + 1) % 10 == 0:
                print(f"   💾 Checkpoint saved at item {item + 1}")
        
        # Mark complete
        task.mark_complete()
        print(f"\n🎉 SUCCESS! All {total_items} items processed!")
        return True
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user!")
        task.add_error("KeyboardInterrupt")
        print(f"💾 Checkpoint saved at item {task.progress['current_step']}")
        print(f"   Resume with: python3 test_long_running_task.py --resume")
        return False
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        task.add_error(str(e))
        task.mark_failed(str(e))
        return False

def main():
    print("="*60)
    print("🧪 Test Long-Running Task")
    print("="*60)
    print()
    
    resume = "--resume" in sys.argv
    
    success = run_task(resume=resume)
    
    print()
    print("="*60)
    print(f"Result: {'✅ PASSED' if success else '❌ FAILED/INTERRUPTED'}")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

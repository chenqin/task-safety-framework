#!/usr/bin/env python3
"""
Example: Long-Running Task with Checkpointing

This example demonstrates how to use SafeTask for a long-running task
that needs checkpointing and recovery capability.
"""

import time
from task_safety_framework import SafeTask

def process_item(item_id):
    """Simulate processing an item."""
    time.sleep(0.1)
    return f"Processed item {item_id}"

def main():
    print("🚀 Starting long-running task...")
    
    # Initialize task
    task = SafeTask("example_long_running_task")
    total_items = 50
    
    # Set total steps
    task.save_checkpoint(total_steps=total_items)
    
    # Get current progress (auto-resume if exists)
    start_item = task.progress.get("current_step", 0)
    
    print(f"📊 Starting from item {start_item + 1}/{total_items}")
    
    # Process items
    for item in range(start_item, total_items):
        result = process_item(item)
        
        # Save checkpoint
        task.save_checkpoint(
            step=item + 1,
            metadata={"last_processed": item}
        )
        
        # Heartbeat
        task.heartbeat()
        
        # Print progress
        progress = (item + 1) / total_items * 100
        print(f"   {item + 1:3d}/{total_items} ({progress:5.1f}%) - {result}")
    
    # Mark complete
    task.mark_complete()
    print(f"\n🎉 Complete! All {total_items} items processed.")

if __name__ == "__main__":
    main()

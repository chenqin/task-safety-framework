#!/usr/bin/env python3
"""
Test Interruption & Recovery - Demonstrates checkpoint/resume capability
"""

import time
import sys
from safe_task import SafeTask

def simulate_work(item_id):
    """Simulate processing work."""
    time.sleep(0.15)
    return f"Processed item {item_id}"

def main():
    print("="*60)
    print("🧪 Test Interruption & Recovery")
    print("="*60)
    print()
    
    task = SafeTask("test_interrupt_recovery")
    total_items = 50
    
    task.save_checkpoint(total_steps=total_items)
    
    start_item = task.progress.get("current_step", 0)
    print(f"📊 Starting from item {start_item + 1 if start_item > 0 else 1}/{total_items}")
    print()
    
    try:
        for item in range(start_item, total_items):
            result = simulate_work(item)
            task.save_checkpoint(step=item + 1, metadata={"last_processed": item})
            task.heartbeat()
            
            print(f"   {item + 1:3d}/{total_items} - {result}")
            
            # Checkpoint every 10 items
            if (item + 1) % 10 == 0:
                print(f"   💾 Checkpoint at {item + 1}")
            
            # SIMULATE INTERRUPT at item 25 (first run only)
            if item == 24 and start_item == 0:
                print(f"\n⚠️  SIMULATING INTERRUPT at item {item + 1}...")
                task.add_error("Simulated interruption for testing")
                print(f"💾 Checkpoint saved. Resume with: python3 test_interrupt_recovery.py")
                return 1  # Exit with error to simulate crash
        
        task.mark_complete()
        print(f"\n🎉 SUCCESS! All {total_items} items processed!")
        return 0
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted!")
        task.add_error("KeyboardInterrupt")
        return 1

if __name__ == "__main__":
    sys.exit(main())

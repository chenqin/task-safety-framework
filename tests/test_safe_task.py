#!/usr/bin/env python3
"""
Test the SafeTask framework

Run this to verify the checkpointing system works correctly.
"""

from safe_task import SafeTask
import time
import signal
import os


def test_basic_checkpoint():
    """Test basic checkpoint functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Checkpoint")
    print("="*60)
    
    task = SafeTask("test_basic")
    
    # Save initial checkpoint
    task.save_checkpoint(step=1, total_steps=5, metadata={"test": "basic"})
    
    # Verify progress
    assert task.progress["current_step"] == 1
    assert task.progress["total_steps"] == 5
    assert task.progress["progress_percent"] == 20.0
    
    # Update checkpoint
    task.save_checkpoint(step=3)
    assert task.progress["progress_percent"] == 60.0
    
    task.mark_complete()
    print("✅ Basic checkpoint test passed\n")


def test_heartbeat():
    """Test heartbeat functionality."""
    print("\n" + "="*60)
    print("TEST 2: Heartbeat")
    print("="*60)
    
    task = SafeTask("test_heartbeat")
    
    # Get initial heartbeat
    initial = task.progress["last_heartbeat"]
    
    # Wait a bit
    time.sleep(1)
    
    # Update heartbeat
    task.heartbeat()
    
    # Verify it changed
    assert task.progress["last_heartbeat"] != initial
    
    task.mark_complete()
    print("✅ Heartbeat test passed\n")


def test_error_tracking():
    """Test error tracking."""
    print("\n" + "="*60)
    print("TEST 3: Error Tracking")
    print("="*60)
    
    task = SafeTask("test_errors")
    
    # Add some errors
    task.add_error("Test error 1")
    task.add_error("Test error 2")
    
    assert len(task.progress["error_history"]) == 2
    assert task.progress["retry_count"] == 2
    
    task.mark_complete()
    print("✅ Error tracking test passed\n")


def test_resume():
    """Test resume from checkpoint."""
    print("\n" + "="*60)
    print("TEST 4: Resume from Checkpoint")
    print("="*60)
    
    # First run - create checkpoint
    task = SafeTask("test_resume")
    task.save_checkpoint(step=3, total_steps=10)
    task.mark_complete()
    
    # Second run - should detect existing checkpoint
    task2 = SafeTask("test_resume")
    assert task2.progress["current_step"] == 3
    assert task2.progress["status"] == "complete"  # Previous run completed
    
    # Reset and try again
    task2.reset()
    assert task2.progress["current_step"] == 0
    assert task2.progress["status"] == "in_progress"
    
    print("✅ Resume test passed\n")


def test_graceful_shutdown():
    """Test graceful shutdown on signal."""
    print("\n" + "="*60)
    print("TEST 5: Graceful Shutdown")
    print("="*60)
    
    task = SafeTask("test_shutdown")
    task.save_checkpoint(step=5, total_steps=10)
    
    # Send SIGTERM to self (this will trigger the handler)
    # For testing, we'll just verify the handler is registered
    import signal
    assert signal.getsignal(signal.SIGTERM) == task._save_and_exit
    assert signal.getsignal(signal.SIGINT) == task._save_and_exit
    
    task.mark_complete()
    print("✅ Graceful shutdown test passed\n")


def main():
    print("\n" + "="*60)
    print("🧪 SafeTask Framework Tests")
    print("="*60)
    
    try:
        test_basic_checkpoint()
        test_heartbeat()
        test_error_tracking()
        test_resume()
        test_graceful_shutdown()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise


if __name__ == "__main__":
    main()

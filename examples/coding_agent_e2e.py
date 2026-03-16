#!/usr/bin/env python3
"""
E2E Example: Coding Agent Using Task Safety Framework

This example demonstrates how a coding agent (like OpenClaw, Codex, etc.)
can use the Task Safety Framework to safely run long-running coding tasks
like code generation, refactoring, or testing.

Scenario: A coding agent needs to refactor 100 files in a codebase.
Without checkpointing, if the agent crashes or gets interrupted, all progress is lost.
With SafeTask, the agent can resume from where it left off.
"""

import time
import os
import sys
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from safe_task import SafeTask

# Simulated coding agent task
class CodingAgentTask:
    """Simulates a coding agent performing refactoring tasks."""
    
    def __init__(self, task_name: str):
        self.task = SafeTask(task_name)
        self.files_to_refactor = []
        
    def discover_files(self, directory: str, pattern: str = "*.py"):
        """Discover files to refactor."""
        print(f"🔍 Discovering files in {directory}...")
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if filename.endswith(pattern):
                    files.append(os.path.join(root, filename))
        return files
    
    def refactor_file(self, filepath: str) -> dict:
        """
        Simulate refactoring a single file.
        
        In a real coding agent, this would:
        1. Read the file
        2. Analyze code structure
        3. Apply refactoring rules
        4. Write back improved code
        5. Run tests to verify
        """
        print(f"   📝 Refactoring: {filepath}")
        
        # Simulate work (in real agent: actual code analysis)
        time.sleep(0.05)  # Simulate processing time
        
        # Return refactoring results
        return {
            "file": filepath,
            "lines_before": 100,
            "lines_after": 85,
            "changes": ["Added type hints", "Improved variable names", "Removed dead code"],
            "tests_passed": True
        }
    
    def run(self, directory: str, pattern: str = "*.py", max_files: int = 20):
        """
        Run the refactoring task with checkpointing.
        
        Args:
            directory: Directory to scan for files
            pattern: File pattern to match
            max_files: Maximum files to process (for demo)
        """
        print("="*60)
        print("🤖 Coding Agent: Code Refactoring Task")
        print("="*60)
        print()
        
        # Step 1: Discover files
        self.files_to_refactor = self.discover_files(directory, pattern)
        self.files_to_refactor = self.files_to_refactor[:max_files]  # Limit for demo
        
        total_files = len(self.files_to_refactor)
        print(f"📊 Found {total_files} files to refactor")
        print()
        
        # Initialize task tracking
        self.task.save_checkpoint(total_steps=total_files)
        
        # Resume if interrupted
        start_index = self.task.progress.get("current_step", 0)
        
        if start_index > 0:
            print(f"🔄 RESUMING from file {start_index + 1}/{total_files}")
            print(f"   Previous progress: {start_index} files completed")
        else:
            print(f"🚀 Starting fresh refactoring")
        
        print()
        
        # Step 2: Refactor files with checkpointing
        results = []
        for i, filepath in enumerate(self.files_to_refactor[start_index:], start=start_index):
            # Refactor the file
            result = self.refactor_file(filepath)
            results.append(result)
            
            # Save checkpoint after each file
            self.task.save_checkpoint(
                step=i + 1,
                metadata={
                    "last_file": filepath,
                    "results_count": len(results),
                    "current_result": result
                }
            )
            
            # Heartbeat
            self.task.heartbeat()
            
            # Print progress
            progress = (i + 1) / total_files * 100
            print(f"   {i + 1:3d}/{total_files} ({progress:5.1f}%) - {os.path.basename(filepath)}")
        
        # Step 3: Mark complete and generate summary
        self.task.mark_complete()
        
        print()
        print("="*60)
        print("✅ Refactoring Complete!")
        print("="*60)
        print()
        
        # Generate summary
        total_before = sum(r["lines_before"] for r in results)
        total_after = sum(r["lines_after"] for r in results)
        reduction = ((total_before - total_after) / total_before) * 100
        
        print(f"📊 Summary:")
        print(f"   Files refactored: {len(results)}")
        print(f"   Lines before: {total_before}")
        print(f"   Lines after: {total_after}")
        print(f"   Code reduction: {reduction:.1f}%")
        print(f"   Tests passed: {sum(1 for r in results if r['tests_passed'])}/{len(results)}")
        print()
        
        return results


def main():
    """
    Main entry point for the coding agent example.
    
    This simulates what a real coding agent would do:
    1. Initialize task tracking
    2. Discover work items
    3. Process with checkpointing
    4. Handle interruptions gracefully
    5. Resume from last checkpoint
    """
    
    # Example: Refactor files in the task-safety-framework itself
    task_dir = "/home/chen/.openclaw/workspace/task-safety-framework"
    
    if not os.path.exists(task_dir):
        print(f"⚠️  Directory not found: {task_dir}")
        print("Using current directory instead...")
        task_dir = "."
    
    # Run the coding agent task
    agent = CodingAgentTask("coding_agent_refactor_example")
    results = agent.run(task_dir, pattern=".py", max_files=15)
    
    print(f"\n🎉 Task completed successfully!")
    print(f"   Progress file: /home/chen/.openclaw/workspace/memory/progress.json")
    print()
    
    # Show how to resume
    print("📝 To resume if interrupted, just run this script again!")
    print("   The agent will automatically pick up from the last checkpoint.")
    print()


if __name__ == "__main__":
    main()

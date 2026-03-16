"""
Task Safety Framework - Checkpointing and Recovery for Long-Running Tasks

Usage:
    from task_safety_framework import SafeTask
    
    task = SafeTask("my_task")
    task.save_checkpoint(step=1, total_steps=100)
    task.heartbeat()
    task.mark_complete()
"""

from .safe_task import SafeTask, check_stuck_task
from .llm_task import LLMTask, create_llm_task, resume_llm_task

__version__ = "1.0.0"
__author__ = "OpenClaw Community"
__all__ = ["SafeTask", "check_stuck_task", "LLMTask", "create_llm_task", "resume_llm_task"]

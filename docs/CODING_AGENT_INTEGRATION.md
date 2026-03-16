# Coding Agent Integration Guide

**How to use Task Safety Framework as a skill for coding agents**

---

## 🎯 Use Case

Coding agents (OpenClaw, Codex, Claude Code, etc.) often run long tasks:
- Refactoring large codebases
- Generating multiple files
- Running comprehensive tests
- Analyzing dependencies

**Problem:** If interrupted, all progress is lost.

**Solution:** Use `SafeTask` to checkpoint every step and auto-resume.

---

## 📦 Installation

```bash
# Install the framework
pip install git+https://github.com/chenqin/task-safety-framework.git

# Or clone locally
git clone https://github.com/chenqin/task-safety-framework.git
cd task-safety-framework
pip install -e .
```

---

## 🤖 Basic Integration Pattern

### 1. Import SafeTask

```python
from task_safety_framework import SafeTask
```

### 2. Initialize at Task Start

```python
task = SafeTask("my_coding_task")
task.save_checkpoint(total_steps=100)  # Set total work items
```

### 3. Checkpoint Every Step

```python
for i, file in enumerate(files):
    # Do work
    result = process_file(file)
    
    # Save checkpoint
    task.save_checkpoint(
        step=i+1,
        metadata={"last_file": file, "result": result}
    )
    
    # Heartbeat
    task.heartbeat()
```

### 4. Auto-Resume on Restart

```python
# Automatically detects existing checkpoint
start_index = task.progress.get("current_step", 0)
for i, file in enumerate(files[start_index:], start=start_index):
    # Resume from where it left off
    ...
```

---

## 📝 Real Examples

### Example 1: File Refactoring Agent

```python
from task_safety_framework import SafeTask

def refactor_codebase(files):
    task = SafeTask("refactor_codebase")
    task.save_checkpoint(total_steps=len(files))
    
    start = task.progress.get("current_step", 0)
    
    for i, filepath in enumerate(files[start:], start=start):
        # 1. Read file
        code = read_file(filepath)
        
        # 2. Apply refactoring
        improved = apply_refactoring(code)
        
        # 3. Write back
        write_file(filepath, improved)
        
        # 4. Checkpoint
        task.save_checkpoint(
            step=i+1,
            metadata={"file": filepath}
        )
        task.heartbeat()
    
    task.mark_complete()
```

### Example 2: Code Generation Agent

```python
def generate_code_for_specs(specs):
    task = SafeTask("generate_code")
    task.save_checkpoint(total_steps=len(specs))
    
    start = task.progress.get("current_step", 0)
    
    for i, spec in enumerate(specs[start:], start=start):
        # Generate code from spec
        code = generate_from_spec(spec)
        
        # Save generated file
        save_code(spec.name, code)
        
        # Checkpoint
        task.save_checkpoint(
            step=i+1,
            metadata={"spec": spec.name, "lines": len(code)}
        )
        task.heartbeat()
    
    task.mark_complete()
```

### Example 3: Test Generation Agent

```python
def generate_tests(files):
    task = SafeTask("generate_tests")
    task.save_checkpoint(total_steps=len(files))
    
    start = task.progress.get("current_step", 0)
    
    for i, filepath in enumerate(files[start:], start=start):
        # Analyze code
        functions = analyze_functions(filepath)
        
        # Generate tests
        tests = generate_tests_for_functions(functions)
        
        # Save tests
        save_tests(filepath, tests)
        
        # Checkpoint
        task.save_checkpoint(
            step=i+1,
            metadata={"file": filepath, "tests_generated": len(tests)}
        )
        task.heartbeat()
    
    task.mark_complete()
```

---

## 🔧 Advanced Patterns

### Pattern 1: Nested Tasks

For complex workflows with multiple phases:

```python
def complex_workflow():
    main_task = SafeTask("complex_workflow")
    
    # Phase 1
    main_task.save_checkpoint(step=1, total_steps=3, phase="analysis")
    analyze_codebase()
    
    # Phase 2
    main_task.save_checkpoint(step=2, total_steps=3, phase="refactoring")
    refactor_codebase()
    
    # Phase 3
    main_task.save_checkpoint(step=3, total_steps=3, phase="testing")
    run_tests()
    
    main_task.mark_complete()
```

### Pattern 2: Parallel Processing

For parallelizable work:

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_process(items):
    task = SafeTask("parallel_process")
    task.save_checkpoint(total_steps=len(items))
    
    completed = set(task.progress.get("completed_items", []))
    pending = [i for i in items if i not in completed]
    
    def process_with_checkpoint(item):
        result = process_item(item)
        task.save_checkpoint(
            step=len(completed) + 1,
            metadata={"completed_items": list(completed) + [item]}
        )
        return result
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(process_with_checkpoint, pending))
    
    task.mark_complete()
```

### Pattern 3: Retry with Backoff

For flaky operations:

```python
import time

def process_with_retry(items, max_retries=3):
    task = SafeTask("process_with_retry")
    task.save_checkpoint(total_steps=len(items))
    
    for i, item in enumerate(items):
        for attempt in range(max_retries):
            try:
                result = process_item(item)
                task.save_checkpoint(step=i+1)
                task.heartbeat()
                break
            except Exception as e:
                task.add_error(f"Attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

---

## 📊 Monitoring & Diagnostics

### Check Task Status

```bash
# Quick status
python3 -m task_safety_framework.task_recovery --status

# Detailed diagnosis
python3 -m task_safety_framework.task_recovery --diagnose

# Reset all tasks
python3 -m task_safety_framework.task_recovery --reset
```

### Programmatic Monitoring

```python
from task_safety_framework import check_stuck_task

# Check if task is stuck
is_stuck, info = check_stuck_task("my_task", timeout_minutes=60)

if is_stuck:
    print(f"⚠️  Task stuck! Last update: {info['last_heartbeat']}")
    # Take recovery action
```

---

## 🧪 Testing Your Integration

```python
# test_coding_agent.py
from task_safety_framework import SafeTask
import pytest

def test_checkpoint_resume():
    task = SafeTask("test_resume")
    task.save_checkpoint(total_steps=10)
    
    # Simulate partial work
    for i in range(5):
        task.save_checkpoint(step=i+1)
    
    # Resume
    start = task.progress.get("current_step", 0)
    assert start == 5
    
    # Complete remaining
    for i in range(5, 10):
        task.save_checkpoint(step=i+1)
    
    task.mark_complete()
    assert task.progress["status"] == "complete"
```

---

## 🚀 Best Practices

### 1. Checkpoint Frequently

```python
# ✅ Good: Checkpoint every item
for item in items:
    process(item)
    task.save_checkpoint(step=...)

# ❌ Bad: Checkpoint only at end
for item in items:
    process(item)
task.save_checkpoint(step=len(items))  # Too late!
```

### 2. Include Metadata

```python
# ✅ Good: Rich metadata
task.save_checkpoint(
    step=i,
    metadata={
        "file": filepath,
        "lines": line_count,
        "errors": error_list
    }
)

# ❌ Bad: Minimal metadata
task.save_checkpoint(step=i)
```

### 3. Handle Errors Gracefully

```python
try:
    result = risky_operation()
    task.save_checkpoint(step=i)
except Exception as e:
    task.add_error(str(e))
    task.mark_failed(str(e))
    raise
```

### 4. Clean Up on Complete

```python
task.mark_complete()
# Optionally clear progress file
# task.progress_file.unlink()  # If you don't need history
```

---

## 📚 Full Examples

See these example files in the repo:

- `examples/coding_agent_e2e.py` - Complete end-to-end example
- `examples/long_running_task.py` - Simple long-running task
- `tests/test_safe_task.py` - Unit tests

---

## 🐛 Troubleshooting

### Issue: Task doesn't resume

**Solution:** Check progress file exists and has correct path.

```python
# Verify progress file
import os
print(os.path.exists("/home/chen/.openclaw/workspace/memory/progress.json"))
```

### Issue: Checkpoint not saving

**Solution:** Ensure write permissions.

```bash
chmod 777 /home/chen/.openclaw/workspace/memory/
```

### Issue: Heartbeat not updating

**Solution:** Call `task.heartbeat()` explicitly.

```python
task.heartbeat()  # Update last_heartbeat timestamp
```

---

## 📞 Support

- **Documentation:** https://github.com/chenqin/task-safety-framework
- **Issues:** https://github.com/chenqin/task-safety-framework/issues
- **Examples:** `examples/` directory

---

**Happy coding! 🐶**

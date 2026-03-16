# Task Safety Framework

**Checkpoint, Heartbeat, and Recovery for Long-Running Tasks**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)]()

---

## 🎯 Overview

A robust checkpointing and heartbeat framework for long-running Python tasks. Prevents data loss, enables auto-recovery, and provides proactive monitoring for tasks that run for hours or days.

### Key Features

✅ **Automatic Checkpointing** - Save progress after every step  
✅ **Heartbeat Monitoring** - Detect stuck tasks (>60 min no update)  
✅ **Graceful Shutdown** - Handle SIGTERM/SIGINT by saving state  
✅ **Auto-Resume** - Restart from last checkpoint on crash  
✅ **Error Tracking** - Log all errors for debugging  
✅ **Progress Tracking** - View % complete at any time  
✅ **CLI Diagnostics** - Check status and diagnose stuck tasks  

---

## 🚀 Quick Start

### Installation

```bash
pip install task-safety-framework
# Or use directly:
# cp safe_task.py your_project/
```

### Basic Usage

```python
from task_safety_framework import SafeTask

# Initialize task
task = SafeTask("my_long_running_task")

# Save checkpoints during work
for i in range(100):
    do_work(i)
    task.save_checkpoint(step=i+1, total_steps=100)
    task.heartbeat()  # Update every 5-10 min

# Mark complete when done
task.mark_complete()
```

### Resume from Crash

```bash
# Just run the task again - it auto-resumes!
python3 my_task.py
```

The framework automatically detects existing checkpoints and resumes from the last saved step.

---

## 📦 Components

### 1. `safe_task.py` - Core Framework

Main class for checkpointing and recovery.

```python
class SafeTask:
    def __init__(self, task_name: str)
    def save_checkpoint(self, step, total_steps, metadata)
    def heartbeat(self)
    def mark_complete(self)
    def mark_failed(self, error)
    def add_error(self, error)
```

### 2. `task_recovery.py` - CLI Diagnostics

Command-line tool for checking and recovering stuck tasks.

```bash
# Check status
python3 task_recovery.py --status

# Detailed diagnosis
python3 task_recovery.py --diagnose

# Reset all tasks
python3 task_recovery.py --reset
```

### 3. `progress_tracker.py` - Progress Monitoring

Legacy progress tracking utility (backward compatible).

---

## 🤖 For Coding Agents

**OpenClaw, Codex, Claude Code, and other coding agents can use this framework for:**

- ✅ Refactoring large codebases (100s of files)
- ✅ Generating code from specifications
- ✅ Running comprehensive test suites
- ✅ Analyzing dependencies
- ✅ Any multi-hour coding task

**See:** [docs/CODING_AGENT_INTEGRATION.md](docs/CODING_AGENT_INTEGRATION.md) for full guide  
**Try:** [examples/coding_agent_e2e.py](examples/coding_agent_e2e.py) for complete example

---

## 📊 Use Cases

### Machine Learning Training

```python
task = SafeTask("training_model_v1")

for epoch in range(100):
    train_epoch(model, data)
    task.save_checkpoint(
        step=epoch+1,
        total_steps=100,
        checkpoint_file=f"model_epoch_{epoch}.pth",
        metadata={"loss": loss, "accuracy": acc}
    )
    task.heartbeat()

task.mark_complete()
```

### Data Processing Pipeline

```python
task = SafeTask("process_dataset")

for batch in batches:
    results = process_batch(batch)
    task.save_checkpoint(
        step=batch_id,
        metadata={"results": results}
    )
    task.heartbeat()
```

### Stock Analysis (Long-Running)

```python
task = SafeTask("stock_analysis_365d")

steps = ["fetch_news", "get_prices", "analyze", "report"]
for i, step in enumerate(steps):
    execute_step(step)
    task.save_checkpoint(step=i+1, total_steps=len(steps))
    task.heartbeat()
```

---

## 🔧 Configuration

### Progress File Location

Default: `/home/chen/.openclaw/workspace/memory/progress.json`

Custom:
```python
task = SafeTask("my_task", progress_file="/custom/path/progress.json")
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Heartbeat age | >30 min | >60 min |
| Retry count | >3 | >5 |
| Error rate | >10% | >25% |

---

## 📁 Project Structure

```
task-safety-framework/
├── src/
│   ├── __init__.py
│   ├── safe_task.py          # Core framework
│   └── task_recovery.py      # CLI diagnostics
├── tests/
│   ├── test_safe_task.py     # Unit tests
│   └── test_recovery.py      # Recovery tests
├── examples/
│   ├── training_example.py   # ML training
│   ├── data_processing.py    # Data pipeline
│   └── stock_analysis.py     # Long-running analysis
├── docs/
│   ├── QUICKSTART.md         # Getting started
│   ├── API.md                # API reference
│   └── TROUBLESHOOTING.md    # Common issues
├── README.md                 # This file
├── LICENSE                   # MIT License
└── setup.py                  # Installation
```

---

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test
python3 tests/test_safe_task.py

# Test long-running task
python3 examples/test_long_running_task.py
```

---

## 📖 Documentation

- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[API Reference](docs/API.md)** - Full API documentation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Examples](examples/)** - Real-world usage examples

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built for OpenClaw agent system
- Inspired by distributed task frameworks like Ray and Dask
- Designed for personal automation and trading systems

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/chenqin2026/task-safety-framework/issues)
- **Discussions:** [GitHub Discussions](https://github.com/chenqin2026/task-safety-framework/discussions)

---

**Made with 🐶 by Chen Qin**

*Last Updated: March 15, 2026*

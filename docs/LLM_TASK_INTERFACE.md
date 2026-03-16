# LLM Task Interface Specification

**How LLM-based agents should use LLMTask for checkpointing**

---

## 🎯 Purpose

This document specifies the exact file format and interface that LLM-based coding agents (OpenClaw, Codex, Claude Code, etc.) should use when checkpointing long-running tasks.

**Key guarantee:** If an agent crashes or gets interrupted, it can resume from the **exact same LLM conversation point** by reading the checkpoint files.

---

## 📁 File Structure

When an LLM task runs, it creates these files in `~/.openclaw/llm-tasks/{task_name}/`:

```
~/.openclaw/llm-tasks/my_coding_task/
├── context.md          # Last prompt/context sent to LLM
├── output.md           # Last response received from LLM  
├── history.jsonl       # Conversation history (JSON Lines)
└── task_state.json     # Task metadata and state
```

---

## 📄 File Formats

### 1. `context.md` - Last Prompt to LLM

**Format:** Plain Markdown

**Content:** The exact prompt/context that was last sent to the LLM API.

**Example:**
```markdown
Analyze the Python codebase in /home/chen/my-project/

Files to analyze:
- utils.py (150 lines)
- main.py (200 lines)  
- config.py (80 lines)

Provide a refactoring plan.
```

**Usage for LLMs:**
- **On resume:** Read this file and use it as the base for your next prompt
- **On new task:** This file won't exist, create initial prompt

### 2. `output.md` - Last Response from LLM

**Format:** Plain Markdown

**Content:** The exact response received from the LLM API.

**Example:**
```markdown
Analysis complete. Found 3 files to refactor:
1. utils.py - Add type hints
2. main.py - Extract functions
3. config.py - Validate inputs

Next step: Refactor utils.py
```

**Usage for LLMs:**
- **On resume:** Read this to know what the LLM last said
- **Continue conversation:** Use this as the "previous turn" context

### 3. `history.jsonl` - Conversation History

**Format:** JSON Lines (one JSON object per line)

**Schema:**
```json
{
  "timestamp": "2026-03-15T20:22:51.971422",
  "turn": 0,
  "response": "Analysis complete...",
  "tool_calls": [],
  "token_count": 42
}
```

**Usage for LLMs:**
- Read last N lines to reconstruct conversation history
- Use for context window management
- Track tool calls made during conversation

### 4. `task_state.json` - Task Metadata

**Format:** JSON

**Schema:**
```json
{
  "task_name": "python_refactor_demo",
  "started_at": "2026-03-15T20:22:51.971422",
  "last_step": "analyze_codebase",
  "step_count": 1,
  "status": "in_progress",  // or "complete", "failed"
  "total_context_tokens": 329,
  "total_output_tokens": 186,
  "conversation_turns": 1,
  "last_context_update": "2026-03-15T20:22:51.977498",
  "last_output_update": "2026-03-15T20:22:51.977719",
  "metadata": {
    "response_tokens": 42,
    "llm_turn": 1
  }
}
```

**Usage for LLMs:**
- Check `status` to know if task is complete/failed
- Read `last_step` to know where to resume
- Track `conversation_turns` for progress reporting

---

## 🤖 Integration Pattern for LLM Agents

### Step 1: Initialize Task

```python
from llm_task import LLMTask

task = LLMTask("my_coding_task")
```

**What happens:**
- Creates `~/.openclaw/llm-tasks/my_coding_task/` directory
- Loads existing state if task was interrupted
- Prints resume message if checkpoint exists

### Step 2: Check if Resuming

```python
if task.should_resume():
    print(f"Resuming from: {task.state['last_step']}")
    # Load last context and output
    last_context = task.get_context()
    last_output = task.get_output()
    # Decide where to continue from
else:
    print("Starting fresh task")
    # Create initial prompt
```

### Step 3: Send Prompt to LLM

```python
# Build your prompt
prompt = f"""
You are a coding assistant.

Previous conversation:
{task.get_last_response()}

Current task: {task.state['last_step']}

Instructions: {your_instructions}
"""

# Save context (what you're sending)
task.set_context(prompt)

# Call LLM API
response = llm_api.call(prompt=prompt, system_prompt=system_prompt)

# Save output (what LLM returned)
task.save_response(
    response=response["content"],
    tool_calls=response.get("tool_calls", []),
    token_count=response["usage"]["completion_tokens"]
)
```

### Step 4: Create Checkpoint

```python
# After completing a logical step
task.checkpoint(
    step_name="analyze_codebase",
    metadata={"files_analyzed": 5, "issues_found": 3}
)
```

### Step 5: Mark Complete

```python
# When task is done
task.mark_complete()
```

---

## 🔄 Resume Pattern

When your agent restarts (crash, interruption, session end):

```python
from llm_task import resume_llm_task

task = resume_llm_task("my_coding_task")

if task:
    # Task exists and needs resuming
    last_context = task.get_context()  # Last prompt sent
    last_output = task.get_output()    # Last LLM response
    last_step = task.state['last_step']  # Where we stopped
    
    # Rebuild conversation context
    history = task.get_conversation_history(max_turns=5)
    
    # Build next prompt based on where we left off
    next_prompt = build_next_prompt(last_output, last_step, history)
    
    # Continue from here
    task.set_context(next_prompt)
    response = llm_api.call(prompt=next_prompt)
    task.save_response(response=response["content"])
    task.checkpoint(step_name=next_step_name)
else:
    # Task complete or doesn't exist
    print("No task to resume")
```

---

## 📝 Example: Complete Workflow

```python
from llm_task import LLMTask

def refactor_codebase_with_llm():
    # Initialize task
    task = LLMTask("refactor_codebase")
    
    # Define steps
    steps = ["discover", "analyze", "refactor", "test", "summary"]
    
    # Resume if interrupted
    if task.should_resume():
        last_step = task.state['last_step']
        start_idx = steps.index(last_step) + 1
    else:
        start_idx = 0
    
    # Execute steps
    for step in steps[start_idx:]:
        # Build prompt with context
        prompt = build_prompt_for_step(
            step=step,
            previous_response=task.get_last_response(),
            history=task.get_conversation_history()
        )
        
        # Save context
        task.set_context(prompt)
        
        # Call LLM
        response = llm_api.call(prompt=prompt)
        
        # Save output
        task.save_response(
            response=response["content"],
            token_count=response["usage"]["completion_tokens"]
        )
        
        # Checkpoint
        task.checkpoint(step, metadata={"tokens": response["usage"]["total_tokens"]})
    
    # Complete
    task.mark_complete()
```

---

## 🎯 Key Design Decisions

### Why Markdown for context.md and output.md?

1. **LLM-friendly:** LLMs are trained on markdown, can parse it easily
2. **Human-readable:** You can open and read these files directly
3. **Portable:** Works across different LLM APIs and platforms
4. **Simple:** No complex parsing needed

### Why JSON Lines for history?

1. **Stream-friendly:** Can append without rewriting entire file
2. **Easy to parse:** One JSON object per line
3. **Backward compatible:** Can add fields without breaking old readers
4. **Efficient:** Can read last N lines without loading entire file

### Why separate context and output files?

1. **Clear separation:** Know exactly what was sent vs received
2. **Debugging:** Can inspect prompts and responses independently
3. **Resume safety:** Can rebuild conversation from both sides
4. **Context window management:** Can truncate old outputs while keeping prompts

---

## 🧪 Testing Your Integration

### Test 1: Basic Checkpoint

```python
task = LLMTask("test_checkpoint")
task.set_context("Hello, LLM!")
task.save_response("Hello, human!", token_count=3)
task.checkpoint("step_1")

# Verify files created
assert Path(task.context_file).exists()
assert Path(task.output_file).exists()
assert task.state['last_step'] == "step_1"
```

### Test 2: Resume

```python
# First run
task1 = LLMTask("test_resume")
task1.set_context("Prompt 1")
task1.save_response("Output 1")
task1.checkpoint("step_1")

# Second run (simulate resume)
task2 = LLMTask("test_resume")
assert task2.should_resume()
assert task2.get_context() == "Prompt 1"
assert task2.get_output() == "Output 1"
```

---

## 🐛 Common Pitfalls

### ❌ Not saving context before LLM call

**Problem:** If LLM call fails, you lose what prompt was sent.

**Solution:** Always call `task.set_context()` **before** LLM API call.

### ❌ Not saving output after LLM call

**Problem:** If task crashes after LLM call, you lose the response.

**Solution:** Always call `task.save_response()` **immediately** after LLM returns.

### ❌ Not checkpointing after each step

**Problem:** If task crashes mid-step, you lose progress.

**Solution:** Call `task.checkpoint()` after **every** logical step completes.

### ❌ Reading context.md instead of building fresh prompt

**Problem:** Using old prompt verbatim might not work for new step.

**Solution:** Use context.md as **reference**, build **new** prompt for current step.

---

## 📚 Examples

See these files for complete working examples:

- `examples/llm_coding_agent.py` - Full E2E example
- `examples/coding_agent_e2e.py` - Simpler refactoring example
- `tests/test_llm_task.py` - Unit tests

---

## 🔗 Related

- [README.md](../README.md) - Main documentation
- [CODING_AGENT_INTEGRATION.md](CODING_AGENT_INTEGRATION.md) - General coding agent guide
- [llm_task.py](../src/llm_task.py) - Source code

---

**This specification ensures your LLM-based agent can safely run multi-hour tasks with automatic resume capability!** 🐶

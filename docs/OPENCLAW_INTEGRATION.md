# OpenClaw Integration Guide

**How to use Task Safety Framework in OpenClaw agents**

---

## 🎯 OpenClaw Use Cases

### 1. **Main Session - Long-Running Analysis**

When you ask OpenClaw to do multi-hour analysis:

```python
# In OpenClaw session
from task_safety_framework import LLMTask

# Start a long analysis task
task = LLMTask("meta_pins_365d_analysis")

# Each turn, save context and output
task.set_context(user_prompt)
task.save_response(assistant_response)
task.checkpoint("step_analyze_news")

# If session ends, resume next time
```

### 2. **Subagent - experiment_runner**

For training/backtesting tasks:

```python
# In experiment_runner subagent
from task_safety_framework import SafeTask

task = SafeTask("backtest_threshold_grid")

for threshold in thresholds:
    results = run_backtest(threshold)
    task.save_checkpoint(
        step=threshold_id,
        metadata={"threshold": threshold, "pnl": results.pnl}
    )
    task.heartbeat()
```

### 3. **Subagent - lacrosse_manager**

For multi-step admin tasks:

```python
# In lacrosse_manager subagent
from task_safety_framework import LLMTask

task = LLMTask("k2_roster_completion")

for player in players:
    # Extract info via browser/LLM
    info = extract_player_info(player)
    
    task.set_context(f"Extract info for {player}")
    task.save_response(str(info))
    task.checkpoint(f"player_{player.name}")
```

---

## 📁 OpenClaw File Locations

### Context Directory

**Default:** `~/.openclaw/llm-tasks/{task_name}/`

**OpenClaw-specific:** Use workspace context:

```python
# For main session
task = LLMTask("my_task", context_dir="~/.openclaw/workspace/tasks/my_task")

# For subagent
task = LLMTask("my_task", context_dir="~/.openclaw/subagents/agent_name/tasks/my_task")
```

### Progress Tracking

**Heartbeat integration:** OpenClaw cron checks `memory/progress.json`

```python
# Task automatically writes to memory/progress.json
# Cron job monitors it every 10 minutes
# Alerts if no heartbeat for >60 minutes
```

---

## 🤖 Practical OpenClaw Examples

### Example 1: Main Session - Multi-Turn Analysis

**Scenario:** You ask OpenClaw to analyze 365 days of stock data.

**Without SafeTask:**
- Session times out after 2 hours
- All progress lost
- Need to start over from scratch

**With SafeTask:**
- Task checkpoints every 10 symbols analyzed
- Session times out at 150/365 symbols
- Next session resumes from 150/365 automatically

**Implementation:**

```python
# In OpenClaw main session
from task_safety_framework import LLMTask

def analyze_365d_stocks(symbols):
    """Analyze 365 days of stock data for multiple symbols."""
    
    task = LLMTask("stock_analysis_365d", 
                   context_dir="~/.openclaw/workspace/tasks/stock_analysis")
    
    # Resume if interrupted
    if task.should_resume():
        last_symbol = task.state['last_step']
        start_idx = symbols.index(last_symbol) + 1
    else:
        start_idx = 0
    
    for i, symbol in enumerate(symbols[start_idx:], start=start_idx):
        # Build prompt for this symbol
        prompt = f"""
        Analyze {symbol} for last 365 days.
        
        Previous analysis:
        {task.get_last_response()}
        
        Include:
        - Price movement
        - News sentiment
        - Key events
        """
        
        # Save context
        task.set_context(prompt)
        
        # Call LLM (OpenClaw's internal API)
        response = openclaw_llm.call(prompt=prompt)
        
        # Save response
        task.save_response(response=response["content"])
        task.checkpoint(symbol, metadata={"symbol_idx": i})
        
        print(f"✅ {symbol} complete ({i+1}/{len(symbols)})")
    
    task.mark_complete()
    return task.get_conversation_history()
```

### Example 2: experiment_runner - Grid Search

**Scenario:** Testing 100 threshold configurations.

```python
# In experiment_runner subagent
from task_safety_framework import SafeTask

def run_threshold_grid_search():
    """Test 100 threshold combinations."""
    
    task = SafeTask("threshold_grid_search_100")
    
    configs = generate_threshold_configs(100)
    task.save_checkpoint(total_steps=len(configs))
    
    # Resume from checkpoint
    start_idx = task.progress.get("current_step", 0)
    
    results = []
    for i, config in enumerate(configs[start_idx:], start=start_idx):
        # Run backtest
        result = run_backtest(config)
        
        # Save checkpoint
        task.save_checkpoint(
            step=i + 1,
            metadata={
                "config": config,
                "pnl": result.pnl,
                "win_rate": result.win_rate
            }
        )
        task.heartbeat()
        
        results.append(result)
    
    # Find best config
    best = max(results, key=lambda r: r.pnl)
    
    task.mark_complete()
    return best
```

### Example 3: lacrosse_manager - Parent Outreach

**Scenario:** Email 30 parents for roster completion.

```python
# In lacrosse_manager subagent
from task_safety_framework import LLMTask

def email_parents(players):
    """Email parents for missing roster info."""
    
    task = LLMTask("k2_parent_outreach",
                   context_dir="~/.openclaw/subagents/lacrosse_manager/tasks")
    
    # Resume if interrupted
    if task.should_resume():
        last_player = task.state['last_step']
        start_idx = [p['name'] for p in players].index(last_player) + 1
    else:
        start_idx = 0
    
    for i, player in enumerate(players[start_idx:], start=start_idx):
        # Build personalized email
        prompt = f"""
        Write email to {player['parent_name']} about {player['name']}.
        
        Missing info: {player['missing_fields']}
        
        Tone: Friendly, professional
        """
        
        task.set_context(prompt)
        
        # Generate email
        email = openclaw_llm.call(prompt=prompt)
        
        # Save response
        task.save_response(response=email["content"])
        
        # Send email
        send_email(
            to=player['parent_email'],
            subject=f"BBLC K2 Roster - {player['name']}",
            body=email["content"]
        )
        
        # Checkpoint
        task.checkpoint(player['name'], metadata={"email_sent": True})
    
    task.mark_complete()
```

### Example 4: Browser Automation - TeamSnap Scraping

**Scenario:** Extract data from 30 TeamSnap player pages.

```python
# In any agent
from task_safety_framework import SafeTask

def scrape_teamsnap_roster(player_ids):
    """Scrape player info from TeamSnap."""
    
    task = SafeTask("teamsnap_scrape_k2")
    task.save_checkpoint(total_steps=len(player_ids))
    
    start_idx = task.progress.get("current_step", 0)
    
    for i, player_id in enumerate(player_ids[start_idx:], start=start_idx):
        # Navigate to player page
        browser.navigate(f"https://teamsnap.com/player/{player_id}")
        
        # Extract data
        info = extract_player_info()
        
        # Save checkpoint
        task.save_checkpoint(
            step=i + 1,
            metadata={"player_id": player_id, "info": info}
        )
        task.heartbeat()
        
        print(f"✅ Scraped player {i+1}/{len(player_ids)}")
    
    task.mark_complete()
```

---

## 🔗 Integration with OpenClaw Systems

### 1. **Cron Heartbeat Monitoring**

OpenClaw already has cron checking `memory/progress.json`:

```json
{
  "task_name": "stock_analysis_365d",
  "status": "in_progress",
  "last_heartbeat": "2026-03-15T20:30:00Z",
  "current_step": 150,
  "total_steps": 365
}
```

**Cron job checks every 10 minutes:**
- If `last_heartbeat` > 60 min ago → Alert
- If `status` = "in_progress" → Report progress
- If `status` = "complete" → Done

### 2. **Session Persistence**

OpenClaw sessions can end (timeout, crash, user disconnect).

**With SafeTask:**
- Context saved to `context.md`
- Output saved to `output.md`
- Next session reads files and resumes

**Without SafeTask:**
- All context lost
- Need to re-provide all information

### 3. **Subagent Coordination**

Main session can check subagent progress:

```python
# In main session
from task_safety_framework import check_stuck_task

is_stuck, info = check_stuck_task("experiment_runner_backtest")

if is_stuck:
    print(f"⚠️  Subagent stuck! Last update: {info['last_heartbeat']}")
    # Take action: restart, investigate, etc.
```

---

## 🚀 Quick Start in OpenClaw

### Step 1: Install

```bash
# From OpenClaw workspace
cd ~/.openclaw/workspace/task-safety-framework
pip install -e . --break-system-packages
```

### Step 2: Use in Session

```python
# In any OpenClaw session
from task_safety_framework import LLMTask

task = LLMTask("my_openclaw_task")

# Your multi-step logic here
for step in steps:
    task.set_context(prompt)
    response = openclaw_llm.call(prompt=prompt)
    task.save_response(response=response["content"])
    task.checkpoint(step)

task.mark_complete()
```

### Step 3: Resume Automatically

```python
# Next session
from task_safety_framework import resume_llm_task

task = resume_llm_task("my_openclaw_task")

if task:
    # Continue from where you left off
    last_response = task.get_last_response()
    # Build next prompt based on last_response
    ...
```

---

## 📊 Real OpenClaw Workflow Example

**User request:** "Analyze META and PINS for last 365 days, check news, stock movements, and macro trends."

**Without SafeTask:**
1. OpenClaw starts analysis
2. Processes 50/100 steps
3. Session times out
4. User asks again
5. OpenClaw starts from 0
6. Wastes 50 steps of work

**With SafeTask:**
1. OpenClaw starts analysis
2. Processes 50/100 steps (checkpointed)
3. Session times out
4. User asks again
5. OpenClaw reads checkpoint
6. Resumes from 50/100
7. Only does remaining 50 steps

**Savings:** 50% of compute time, better UX

---

## 🎯 Best Practices for OpenClaw

### 1. **Use LLMTask for Multi-Turn Conversations**

```python
# ✅ Good: LLMTask for conversation-based tasks
task = LLMTask("stock_analysis")
task.set_context(prompt)
task.save_response(response)

# ❌ Bad: SafeTask for conversations
task = SafeTask("stock_analysis")  # Loses conversation context
```

### 2. **Use SafeTask for Batch Processing**

```python
# ✅ Good: SafeTask for simple loops
task = SafeTask("process_1000_files")
for file in files:
    process(file)
    task.save_checkpoint(step=i)

# ❌ Bad: LLMTask for simple loops
task = LLMTask("process_1000_files")  # Overkill
```

### 3. **Set Context Directory for Organization**

```python
# ✅ Good: Organized by agent
task = LLMTask("task1", context_dir="~/.openclaw/subagents/experiment_runner/tasks")

# ❌ Bad: Default location (might get crowded)
task = LLMTask("task1")  # Goes to ~/.openclaw/llm-tasks/
```

### 4. **Checkpoint Frequently**

```python
# ✅ Good: Every logical step
for symbol in symbols:
    analyze(symbol)
    task.checkpoint(symbol)  # Can resume per-symbol

# ❌ Bad: Only at end
for symbol in symbols:
    analyze(symbol)
task.checkpoint("done")  # Loses all progress if crashes
```

### 5. **Include Metadata**

```python
# ✅ Good: Rich metadata
task.checkpoint("step_1", metadata={
    "symbol": "META",
    "pnl": 4.53,
    "win_rate": 0.61
})

# ❌ Bad: No metadata
task.checkpoint("step_1")  # Hard to debug
```

---

## 🔧 OpenClaw-Specific Tips

### Tip 1: Check Progress Between Turns

```python
# Between OpenClaw turns
task_status = task.get_status()
print(f"Progress: {task_status['step_count']}/{total_steps}")
```

### Tip 2: Use Heartbeat for Long Turns

```python
# For operations taking >5 minutes
for i in range(1000):
    process_item(i)
    if i % 50 == 0:
        task.heartbeat()  # Update timestamp every 50 items
```

### Tip 3: Clean Up Completed Tasks

```python
# After task complete, optionally clean up
if task.state['status'] == 'complete':
    import shutil
    shutil.rmtree(task.context_dir)  # Remove task files
```

### Tip 4: Monitor Subagent Tasks

```python
# In main session, check subagent health
from task_safety_framework import check_stuck_task

for agent in ['experiment_runner', 'lacrosse_manager']:
    is_stuck, info = check_stuck_task(f"{agent}_current_task")
    if is_stuck:
        print(f"⚠️  {agent} task stuck!")
```

---

## 📚 Related OpenClaw Files

- **AGENTS.md** - Subagent organization
- **HEARTBEAT.md** - Monitoring protocol
- **MEMORY.md** - Long-term memory
- **memory/progress.json** - Progress tracking (used by SafeTask)

---

## 🐶 Summary

**In OpenClaw context:**

1. **Use LLMTask** for multi-turn conversations with LLM
2. **Use SafeTask** for simple batch processing loops
3. **Checkpoint every logical step** (not just at end)
4. **Let cron monitor** via `memory/progress.json`
5. **Resume automatically** on next session

**Result:** Your OpenClaw tasks survive crashes, timeouts, and interruptions! 🎉

---

**Made for OpenClaw agents by OpenClaw Community** 🐶

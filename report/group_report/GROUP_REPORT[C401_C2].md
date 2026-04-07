# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: C401-C2
- **Team Members**: Nguyễn Thùy Linh, Bùi Minh Ngọc, Phạm Việt Anh, Phạm Việt Hoàng, Phan Tuấn Minh, Lê Đức Thanh
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

This project upgrades a baseline chatbot into a ReAct-style agent with tool-calling and structured telemetry.  
The agent was evaluated against the chatbot on 3 practical travel-planning scenarios using OpenAI `gpt-4o`.

- **Success Rate**: 100% (latest 3-case run, no timeout/fallback).
- **Key Outcome**: Agent produced grounded multi-step answers by using tools and looped observations, while chatbot produced longer but less grounded direct responses.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Implemented in `src/agent/agent.py`:
- Thought -> Action -> Observation loop.
- Action parsing and dynamic tool execution.
- Max-step guardrails.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `suggest_destinations` | `string` | Suggest destination options by preference |
| `check_weather` | `string` | Retrieve weather summary |
| `search_flights` | `string` | Estimate flight cost |
| `search_hotels` | `string` | Estimate hotel cost |
| `get_attractions` | `string` | List attractions |
| `calculate_total_cost` | `string` | Estimate total trip cost |

### 2.3 LLM Providers Used
- **Primary**: OpenAI `gpt-4o`
- **Secondary (Backup)**: Local/Google provider interfaces available in `src/core` (not primary in final run)

---

## 3. Telemetry & Performance Dashboard

Data sources:
- `report/group_report/COMPARISON_RESULTS.md`
- `report/group_report/FAILURE_ANALYSIS_LATEST.md`
- `logs/2026-04-06.log`

Latest run metrics:
- **Average Latency (all LLM calls)**: 2012.6 ms
- **P95 Latency**: 4722 ms
- **Average Tokens per Request**: 504.8
- **Agent Status Breakdown**: success=3, fallback=0, timeout=0, parse_error=0

Comparison table (latest run):

| Case | Chatbot (tokens / latency / steps) | Agent (tokens / latency / steps) |
| :--- | :--- | :--- |
| Toi muon du lich bien nhung chua biet di dau | 277 / 3076ms / 1 | 914 / 5788ms / 2 |
| Tu van ke hoach Da Nang 3N2D voi ngan sach 10 trieu | 625 / 5642ms / 1 | 3328 / 9861ms / 6 |
| So sanh Da Nang va Nha Trang cho chuyen di ngan ngay | 442 / 3596ms / 1 | 2996 / 6252ms / 6 |

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Step-Budget Exhaustion in Comparison/Discovery Queries (v1)
- **Input**: comparison and discovery prompts requiring many sub-facts.
- **Observation**: v1 sometimes reached `max_steps` before emitting `Final Answer`.
- **Root Cause**: planner continued collecting extra context instead of summarizing when sufficient evidence already existed.
- **Fix Applied (v2)**:
  - Improved loop termination behavior using observed tool outputs.

Latest validation result:
- No timeout/fallback in the latest 3-case benchmark run.

---
## 5. Ablation Studies & Experiments

### Experiment 1: Agent v1 vs Agent v2
- **Diff**: Improved loop termination behavior.
- **Result**: Latest benchmark moved from timeout/fallback risks to stable completion on all cases.

### Experiment 2: Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple ideation | Fluent generic text | Tool-grounded but concise | Draw |
| Budget planning | Generic estimate | Tool-based calculable estimate | **Agent** |
| Destination comparison | Generic narrative | Explicit cost/weather/attraction comparison | **Agent** |

---

## 6. Production Readiness Review

- **Security**: Validate tool arguments before execution; reject unknown tool calls.
- **Guardrails**: `max_steps`, parse-error logging.
- **Scaling**: Add retrieval/search APIs, async tool execution, and intent-based tool routing.

---

> [!NOTE]
> If required by instructor, include one architecture flowchart image and attach run command screenshots
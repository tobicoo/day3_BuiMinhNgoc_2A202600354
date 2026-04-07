"""
Analyze metrics from log files.
Reads JSON logs from the logs/ directory and displays a summary.
"""

import os
import sys
import json
import glob
from datetime import datetime
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def parse_log_file(filepath: str) -> list:
    """Parse a JSON log file and return list of events."""
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                # Each line is a JSON object
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    return events

def analyze_metrics(log_dir: str = "logs"):
    """Analyze all metrics from log files."""
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}[METRICS] Metrics Analysis Report{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    
    # Find all log files
    log_files = glob.glob(os.path.join(log_dir, "*.log"))
    if not log_files:
        print(f"{Colors.YELLOW}[WARN] No log files found in {log_dir}/{Colors.RESET}")
        print(f"{Colors.BLUE}[INFO] Run the agent first to generate logs.{Colors.RESET}")
        return
    
    print(f"{Colors.GREEN}[OK] Found {len(log_files)} log file(s):{Colors.RESET}")
    for f in log_files:
        print(f"   - {os.path.basename(f)}")
    print()
    
    # Collect all events
    all_events = []
    for log_file in log_files:
        events = parse_log_file(log_file)
        all_events.extend(events)
    
    if not all_events:
        print(f"{Colors.YELLOW}⚠️ No events found in log files.{Colors.RESET}")
        return
    
    # Filter LLM_METRIC events
    llm_metrics = [e for e in all_events if e.get("event") == "LLM_METRIC"]
    session_summaries = [e for e in all_events if e.get("event") == "SESSION_SUMMARY"]
    agent_starts = [e for e in all_events if e.get("event") == "AGENT_START"]
    agent_ends = [e for e in all_events if e.get("event") == "AGENT_END"]
    
    # === LLM Metrics Summary ===
    print(f"{Colors.BOLD}🔢 LLM Request Metrics{Colors.RESET}")
    print(f"{'-'*40}")
    
    if llm_metrics:
        total_requests = len(llm_metrics)
        total_tokens = sum(m["data"].get("total_tokens", 0) for m in llm_metrics)
        total_cost = sum(m["data"].get("cost_estimate_usd", 0) for m in llm_metrics)
        latencies = [m["data"].get("latency_ms", 0) for m in llm_metrics]
        
        print(f"   Total LLM calls: {total_requests}")
        print(f"   Total tokens: {total_tokens:,}")
        print(f"   Estimated cost: ${total_cost:.6f}")
        print(f"   Avg latency: {sum(latencies)/len(latencies):.0f}ms")
        print(f"   Max latency: {max(latencies):.0f}ms")
        print(f"   Min latency: {min(latencies):.0f}ms")
        
        # Token efficiency
        efficiencies = [m["data"].get("token_efficiency_ratio", 0) for m in llm_metrics]
        print(f"   Avg token efficiency: {sum(efficiencies)/len(efficiencies):.2%}")
        
        # Tool call distribution
        tool_calls = defaultdict(int)
        for m in llm_metrics:
            tool = m["data"].get("tool_called")
            if tool:
                tool_calls[tool] += 1
        
        if tool_calls:
            print(f"\n   {Colors.BOLD}Tool Call Distribution:{Colors.RESET}")
            for tool, count in sorted(tool_calls.items(), key=lambda x: -x[1]):
                print(f"      {tool}: {count} calls")
        
        # Model distribution
        model_calls = defaultdict(int)
        for m in llm_metrics:
            model = m["data"].get("model", "unknown")
            model_calls[model] += 1
        
        print(f"\n   {Colors.BOLD}Model Usage:{Colors.RESET}")
        for model, count in sorted(model_calls.items(), key=lambda x: -x[1]):
            print(f"      {model}: {count} calls")
    else:
        print(f"   {Colors.YELLOW}No LLM_METRIC events found.{Colors.RESET}")
    
    # === Agent Sessions ===
    print(f"\n{Colors.BOLD}[AGENT] Agent Sessions{Colors.RESET}")
    print(f"{'-'*40}")
    
    if agent_starts:
        print(f"   Total agent sessions: {len(agent_starts)}")
        for i, start in enumerate(agent_starts):
            user_input = start["data"].get("input", "N/A")
            model = start["data"].get("model", "N/A")
            print(f"   Session {i+1}: \"{user_input[:50]}...\" (model: {model})")
    else:
        print(f"   {Colors.YELLOW}No agent sessions found.{Colors.RESET}")
    
    # === Session Summaries ===
    if session_summaries:
        print(f"\n{Colors.BOLD}[SUMMARY] Session Summaries{Colors.RESET}")
        print(f"{'-'*40}")
        for summary in session_summaries:
            data = summary["data"]
            print(f"   Requests: {data.get('total_requests', 0)}")
            print(f"   Tokens: {data.get('total_tokens', 0):,}")
            print(f"   Cost: ${data.get('total_cost_usd', 0):.6f}")
            print(f"   Duration: {data.get('session_duration_seconds', 0):.1f}s")
            print()
    
    # === Errors/Warnings ===
    print(f"\n{Colors.BOLD}[ERRORS] Errors & Warnings{Colors.RESET}")
    print(f"{'-'*40}")
    
    errors = [e for e in all_events if e.get("event") in ["ERROR", "LLM_ERROR"]]
    if errors:
        for err in errors:
            print(f"   {Colors.RED}[{err['event']}]{Colors.RESET} {json.dumps(err.get('data', {}))}")
    else:
        print(f"   {Colors.GREEN}[OK] No errors found.{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.GREEN}[OK] Analysis complete!{Colors.RESET}")
    print()


if __name__ == "__main__":
    analyze_metrics()

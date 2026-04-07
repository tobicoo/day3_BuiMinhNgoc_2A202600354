import time
from typing import Dict, Any, List, Optional
from src.telemetry.logger import logger

# Real pricing per 1M tokens (USD) - approximate rates as of 2024
MODEL_PRICING = {
    # OpenAI models
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Gemini models
    "gemini-pro": {"input": 0.50, "output": 1.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-2.0-flash-exp": {"input": 0.00, "output": 0.00},  # Free tier
    # Local models (no API cost, just compute)
    "local": {"input": 0.00, "output": 0.00},
    "phi-3": {"input": 0.00, "output": 0.00},
}

# Default pricing if model not found (conservative estimate)
DEFAULT_PRICING = {"input": 1.00, "output": 3.00}


class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    
    Tracks:
    - Token efficiency (prompt vs completion tokens)
    - Latency (response time)
    - Cost estimation
    - Session aggregates
    """
    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []
        self.session_start_time = time.time()

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: float,
                      step: Optional[int] = None, tool_called: Optional[str] = None):
        """
        Logs a single request metric to our telemetry.
        
        Args:
            provider: LLM provider name (openai, gemini, local)
            model: Model name used
            usage: Token usage dict with prompt_tokens, completion_tokens, total_tokens
            latency_ms: Response time in milliseconds
            step: Optional step number in ReAct loop
            tool_called: Optional tool name that was called
        """
        cost = self._calculate_cost(model, usage)
        token_efficiency = self._calculate_token_efficiency(usage)
        
        metric = {
            "provider": provider,
            "model": model,
            "step": step,
            "tool_called": tool_called,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "token_efficiency_ratio": token_efficiency,
            "latency_ms": latency_ms,
            "cost_estimate_usd": cost
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculate real cost based on model pricing.
        Returns cost in USD based on token usage.
        """
        # Find pricing for this model (try exact match, then partial match)
        pricing = MODEL_PRICING.get(model, MODEL_PRICING.get(model.split(":")[0], DEFAULT_PRICING))
        
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        # Cost = (input_tokens / 1M * input_price) + (output_tokens / 1M * output_price)
        input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (completion_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)

    def _calculate_token_efficiency(self, usage: Dict[str, int]) -> float:
        """
        Calculate token efficiency ratio.
        Returns ratio of completion tokens to total tokens (higher = more efficient).
        A low ratio means the prompt is too verbose compared to the answer.
        """
        total = usage.get("total_tokens", 0)
        if total == 0:
            return 0.0
        return round(usage.get("completion_tokens", 0) / total, 4)

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get aggregate statistics for the entire session.
        """
        if not self.session_metrics:
            return {"message": "No metrics recorded this session"}
        
        total_tokens = sum(m["total_tokens"] for m in self.session_metrics)
        total_cost = sum(m["cost_estimate_usd"] for m in self.session_metrics)
        latencies = [m["latency_ms"] for m in self.session_metrics]
        
        # Count tool usage
        tool_calls = {}
        for m in self.session_metrics:
            tool = m.get("tool_called")
            if tool:
                tool_calls[tool] = tool_calls.get(tool, 0) + 1
        
        summary = {
            "total_requests": len(self.session_metrics),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "max_latency_ms": max(latencies),
            "min_latency_ms": min(latencies),
            "avg_token_efficiency": round(
                sum(m["token_efficiency_ratio"] for m in self.session_metrics) / len(self.session_metrics), 4
            ),
            "tool_call_distribution": tool_calls,
            "session_duration_seconds": round(time.time() - self.session_start_time, 2)
        }
        
        logger.log_event("SESSION_SUMMARY", summary)
        return summary

    def get_cost_breakdown(self) -> Dict[str, float]:
        """
        Get cost breakdown by provider and model.
        """
        cost_by_model = {}
        for m in self.session_metrics:
            model = m["model"]
            cost_by_model[model] = cost_by_model.get(model, 0) + m["cost_estimate_usd"]
        
        return {k: round(v, 6) for k, v in cost_by_model.items()}

    def get_latency_percentiles(self) -> Dict[str, float]:
        """
        Calculate latency percentiles (p50, p90, p95, p99).
        """
        if not self.session_metrics:
            return {}
        
        latencies = sorted([m["latency_ms"] for m in self.session_metrics])
        n = len(latencies)
        
        return {
            "p50": latencies[int(n * 0.5)],
            "p90": latencies[int(n * 0.9)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[min(int(n * 0.99), n - 1)],
            "avg": round(sum(latencies) / n, 2)
        }

    def reset_session(self):
        """Reset session metrics."""
        self.session_metrics = []
        self.session_start_time = time.time()
        logger.log_event("SESSION_RESET", {})


# Global tracker instance
tracker = PerformanceTracker()

import os
import re
import json
import time
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    ORANGE = '\033[38;5;208m'  # Orange color
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Implements the core loop logic for travel planning.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        System prompt that instructs the agent to follow ReAct format.
        Structured with: Identity, Capabilities, Instructions, Constraints, Output format.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""1. Identity: You are a Travel Planning Assistant that helps users plan their trips step by step using available tools.

2. Capabilities: You can suggest destinations, check weather, search flights and hotels, find attractions, and calculate total costs.

3. Instructions:
   - Analyze the user's request carefully
   - Use tools one at a time to gather information
   - Build a complete travel plan within the user's budget
   - Provide a clear final answer with all details

4. Constraints:
   - Must follow the ReAct format strictly
   - Only call one tool per step
   - Wait for Observation before next Thought
   - Stop when you have enough information
   - Stay within user's budget

5. Output format:
   Thought: <your reasoning about what to do next>
   Action: <tool_name>(<arg1>=<value1>, <arg2>=<value2>)
   Observation: <result from tool execution>
   ... (repeat as needed) ...
   Thought: I have enough information to provide a final answer.
   Final Answer: <your complete travel plan>

## Available Tools
{tool_descriptions}
"""

    def run(self, user_input: str, stream: bool = False) -> str:
        """
        Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        
        Args:
            user_input: The user's query
            stream: If True, stream the LLM response token by token
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}🚀 START: {user_input}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        current_prompt = user_input
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            # 1. Generate LLM response
            print(f"{Colors.GREEN}📝 Step {steps + 1}/{self.max_steps}: {Colors.RESET}", end="", flush=True)
            
            if stream:
                # Streaming mode with loading indicator
                print(f"{Colors.ORANGE}Thinking...{Colors.RESET} ", end="", flush=True)
                response = ""
                start_time = time.time()
                for chunk in self.llm.stream(current_prompt, system_prompt=self.get_system_prompt()):
                    response += chunk
                latency_ms = (time.time() - start_time) * 1000
                print()  # New line after streaming
                
                # Track metrics for streaming (estimate tokens from characters)
                estimated_tokens = len(response) // 4  # Rough estimate: ~4 chars per token
                tracker.track_request(
                    provider=self.llm.__class__.__name__.replace("Provider", "").lower(),
                    model=self.llm.model_name,
                    usage={"prompt_tokens": 0, "completion_tokens": estimated_tokens, "total_tokens": estimated_tokens},
                    latency_ms=latency_ms,
                    step=steps + 1
                )
            else:
                # Non-streaming mode
                result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
                response = result["content"]
                
                # Track metrics for non-streaming
                usage = result.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
                latency_ms = result.get("latency_ms", 0)
                tracker.track_request(
                    provider=self.llm.__class__.__name__.replace("Provider", "").lower(),
                    model=self.llm.model_name,
                    usage=usage,
                    latency_ms=latency_ms,
                    step=steps + 1
                )
            
            print(f"{Colors.ORANGE}Thinking: {Colors.RESET}{response}\n")
            logger.log_event("LLM_RESPONSE", {"step": steps, "content": response})
            
            # 2. Parse Final Answer
            final_answer = self._parse_final_answer(response)
            if final_answer:
                print(f"{Colors.GREEN}✅ FINAL ANSWER FOUND!{Colors.RESET}")
                logger.log_event("FINAL_ANSWER", {"content": final_answer})
                break
            
            # 3. Parse Thought
            thought = self._parse_thought(response)
            print(f"{Colors.GREEN}🧠 Thought: {thought}{Colors.RESET}")
            
            # 4. Parse Action
            action = self._parse_action(response)
            if action:
                tool_name, args_str = action
                print(f"{Colors.GREEN}🔧 Action: {tool_name}({args_str}){Colors.RESET}")
                
                # 5. Execute tool
                observation = self._execute_tool(tool_name, args_str)
                print(f"{Colors.GREEN}👁️ Observation: {observation}{Colors.RESET}\n")
                logger.log_event("OBSERVATION", {"step": steps, "tool": tool_name, "result": observation})
                
                # 6. Append to prompt for next iteration
                current_prompt += f"\n\nThought: {thought}\nAction: {tool_name}({args_str})\nObservation: {observation}"
            else:
                print(f"{Colors.YELLOW}⚠️ No action found in response. Appending raw response.{Colors.RESET}\n")
                current_prompt += f"\n\n{response}"
            
            steps += 1
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}🏁 END: {steps} steps completed{Colors.RESET}")
        
        # Print session summary
        summary = tracker.get_session_summary()
        print(f"\n{Colors.CYAN}📊 Session Metrics:{Colors.RESET}")
        print(f"   Total LLM calls: {summary.get('total_requests', 0)}")
        print(f"   Total tokens: {summary.get('total_tokens', 0)}")
        print(f"   Estimated cost: ${summary.get('total_cost_usd', 0):.6f}")
        print(f"   Avg latency: {summary.get('avg_latency_ms', 0):.0f}ms")
        print(f"   Token efficiency: {summary.get('avg_token_efficiency', 0):.2%}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
        
        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer, "metrics": summary})
        
        if final_answer:
            return final_answer
        return f"Agent reached max steps ({self.max_steps}) without a final answer. Last response: {response}"

    def _parse_thought(self, response: str) -> str:
        """Extract Thought from LLM response."""
        match = re.search(r"Thought:\s*(.+?)(?=Action:|Final Answer:|$)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: try to get first line
        lines = response.strip().split("\n")
        for line in lines:
            if line.startswith("Thought:"):
                return line.replace("Thought:", "").strip()
        return ""

    def _parse_final_answer(self, response: str) -> Optional[str]:
        """Extract Final Answer from LLM response."""
        match = re.search(r"Final Answer:\s*(.+)", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, response: str) -> Optional[tuple]:
        """Extract Action (tool_name and args) from LLM response."""
        # Pattern: Action: tool_name(arg1=value1, arg2=value2)
        match = re.search(r"Action:\s*(\w+)\((.+?)\)", response, re.DOTALL)
        if match:
            tool_name = match.group(1).strip()
            args_str = match.group(2).strip()
            return (tool_name, args_str)
        return None

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute tool by name and return observation.
        Uses mock responses for testing.
        """
        # Check if tool exists
        tool_exists = any(t["name"] == tool_name for t in self.tools)
        if not tool_exists:
            return f"Error: Tool '{tool_name}' not found. Available tools: {[t['name'] for t in self.tools]}"
        
        # Get mock response
        try:
            observation = get_mock_response(tool_name, args)
            return observation
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

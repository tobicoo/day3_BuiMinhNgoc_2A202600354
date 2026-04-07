"""
Interactive chat mode for Travel Planning Agent.
Run this to chat with the agent in real-time.
"""

import sys
import os
from dotenv import load_dotenv

# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load environment variables from .env
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.tools.mock_tools import MOCK_TOOLS
from src.core.openai_provider import OpenAIProvider

def get_llm():
    """Initialize LLM provider from environment variables."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("[ERROR] OPENROUTER_API_KEY not set in .env file!")
        print("[INFO] Please:")
        print("   1. Get API key from: https://openrouter.ai/keys")
        print("   2. Add OPENROUTER_API_KEY=your_key to .env")
        return None
    
    print(f"[INFO] Using OpenRouter provider ({model_name})")
    return OpenAIProvider(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )

def chat():
    """Interactive chat loop with the agent."""
    
    print("=" * 60)
    print("  Travel Planning Agent - Interactive Chat Mode")
    print("=" * 60)
    print()
    print("Type 'quit' or 'exit' to stop.")
    print()
    
    # Initialize LLM
    llm = get_llm()
    if not llm:
        return
    
    # Create agent
    agent = ReActAgent(llm=llm, tools=MOCK_TOOLS, max_steps=6)
    
    # Chat loop
    while True:
        try:
            # Get user input
            try:
                user_input = input(f"\n{Colors.BLUE}[You]{Colors.RESET} ").strip()
            except EOFError:
                print(f"\n\n{Colors.GREEN}[Agent] Goodbye! Have a great trip! 👋{Colors.RESET}")
                break
            
            # Check for exit
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"\n{Colors.GREEN}[Agent] Goodbye! Have a great trip! 👋{Colors.RESET}")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Run agent with streaming
            print()
            result = agent.run(user_input, stream=True)
            print(f"\n{Colors.GREEN}[Agent]{Colors.RESET} {result}")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}[Agent] Goodbye! 👋{Colors.RESET}")
            break
        except Exception as e:
            print(f"\n{Colors.YELLOW}[ERROR] {e}{Colors.RESET}")

if __name__ == "__main__":
    chat()

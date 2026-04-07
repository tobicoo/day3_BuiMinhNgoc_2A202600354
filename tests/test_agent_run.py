"""
Test script for Travel Planning Agent.
Run this to test the ReAct loop with mock tools.
"""

import sys
import os
from dotenv import load_dotenv

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

def test_stream():
    """Test streaming response from LLM."""
    
    print("[INIT] Testing streaming response...\n")
    
    # Using OpenRouter provider
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("[ERROR] OPENROUTER_API_KEY not set in .env file!")
        print("[INFO] Please:")
        print("   1. Get API key from: https://openrouter.ai/keys")
        print("   2. Add OPENROUTER_API_KEY=your_key to .env")
        return
    
    print(f"[INFO] Using OpenRouter provider ({model_name})")
    llm = OpenAIProvider(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )
    
    user_input = "Toi muon di du lich vao cuoi thang 7 nay, ma chua biet di dau, voi ngan sach 10 tr, trong 3 ngay 2 dem"
    system_prompt = "You are a helpful travel assistant. Respond in Vietnamese."
    
    print(f"[USER] {user_input}\n")
    print("[STREAMING] Response:\n")
    print("-" * 60)
    
    # Stream response
    for chunk in llm.stream(user_input, system_prompt=system_prompt):
        print(chunk, end="", flush=True)
    
    print("\n" + "-" * 60)
    print("\n[STREAMING] Done!")


def test_agent():
    """Test the ReAct agent with mock tools."""
    
    print("[INIT] Initializing Travel Planning Agent...\n")
    
    # Using OpenRouter provider
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
    
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("[ERROR] OPENROUTER_API_KEY not set in .env file!")
        print("[INFO] Please:")
        print("   1. Get API key from: https://openrouter.ai/keys")
        print("   2. Add OPENROUTER_API_KEY=your_key to .env")
        return
    
    print(f"[INFO] Using OpenRouter provider ({model_name})")
    llm = OpenAIProvider(
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )
    
    # Create agent with mock tools
    agent = ReActAgent(llm=llm, tools=MOCK_TOOLS, max_steps=6)
    
    # Test input
    user_input = "Toi muon di du lich vao cuoi thang 7 nay, ma chua biet di dau, voi ngan sach 10 tr, trong 3 ngay 2 dem"
    
    print(f"[USER] {user_input}\n")
    
    # Run agent
    result = agent.run(user_input)
    
    print(f"\n[RESULT] {result}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--stream":
        test_stream()
    else:
        test_agent()

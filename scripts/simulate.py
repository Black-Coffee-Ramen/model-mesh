import asyncio
import httpx
import json
import time
import random
import argparse
import sys

BASE_URL = "http://localhost:8000"

async def run_simulation(mode="v4.1", user_id="sim_user"):
    async with httpx.AsyncClient() as client:
        print(f"--- LLM INFRA PLATFORM SIMULATION (MODE: {mode}) ---")
        
        if mode == "v4.1":
            contexts = ["coding", "translation", "summarization", "extraction", "reasoning", "general"]
            print(f"Generating 40 randomized requests across {len(contexts)} contexts...")
            
            for i in range(40):
                ctx = random.choice(contexts)
                # Simulate realistic prompts per context
                prompts = {
                    "coding": "Write a python function to sort a list of strings by length.",
                    "translation": "Translate 'The weather is beautiful today' into French.",
                    "summarization": "Summarize the key points of the 2024 AI safety accord.",
                    "extraction": "Extract all dates and names from the provided contract text.",
                    "reasoning": "If all A are B, and some B are C, is every A necessarily C?",
                    "general": "What is the capital of Kyrgyzstan?"
                }
                
                resp = await client.post(f"{BASE_URL}/v1/chat/completions", json={
                    "user_id": user_id,
                    "model": "auto",
                    "messages": [{"role": "user", "content": prompts.get(ctx, "Hello!")}],
                    "temperature": 1.0,
                    "workload_type": ctx
                })
                
                if resp.status_code == 200:
                    model_picked = resp.json().get("model")
                    print(f"   [{i+1}/40] Context: {ctx:<15} | Picked: {model_picked}")
                else:
                    print(f"   [{i+1}/40] Context: {ctx:<15} | Failed (Status: {resp.status_code})")
                
                await asyncio.sleep(0.1)
        
        elif mode == "v4":
            print("\nRunning V4 Reward Learning Batch (20 requests)...")
            for i in range(20):
                resp = await client.post(f"{BASE_URL}/v1/chat/completions", json={
                    "user_id": user_id,
                    "model": "auto",
                    "messages": [{"role": "user", "content": f"V4 Probe {i}"}]
                })
                print(f"   Request {i+1}: {resp.json().get('model')}")
                await asyncio.sleep(0.1)

        print("\nSimulation complete. Check the dashboard for results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Infra Platform Simulator")
    parser.add_argument("--mode", type=str, default="v4.1", choices=["v3", "v4", "v4.1"], help="Simulation mode")
    parser.add_argument("--user", type=str, default="admin_user", help="User ID for simulation")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_simulation(mode=args.mode, user_id=args.user))
    except Exception as e:
        print(f"Error: Could not connect to gateway. Ensure 'python src/main.py' is running.")
        sys.exit(1)

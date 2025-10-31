#!/usr/bin/env python3
"""
Tone comparison test - compare current vs high-energy prompt
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_prompt(filename):
    """Load a prompt from file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return f"Error: Could not find {filename}"

def test_prompts():
    """Test different prompts side by side"""
    
    # Set up OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Load both prompts
    prompts = {
        "🔵 CURRENT PROMPT": "prompts/system_prompt.md",
        "🔥 HIGH ENERGY TEST": "prompts/test_prompt_tone.md"
    }
    
    test_query = "I need help with headquarters upgrades"
    
    print("🧪 TONE COMPARISON TEST")
    print("=" * 80)
    print(f"📝 Test Query: '{test_query}'")
    print("=" * 80)
    
    for prompt_name, prompt_file in prompts.items():
        system_prompt = load_prompt(prompt_file)
        
        test_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": test_query}
        ]
        
        print(f"\n{prompt_name}")
        print("-" * 60)
        
        try:
            response = client.chat.completions.create(
                model="gpt-5-chat-latest",  # Non-reasoning GPT-5
                messages=test_messages,
                temperature=0.9,  # Higher temp for more personality
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            if content:
                print(content)
            else:
                print("⚠️ EMPTY RESPONSE!")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
        print("-" * 60)

if __name__ == "__main__":
    test_prompts()
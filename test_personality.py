#!/usr/bin/env python3
"""
Local personality testing script - bypasses Poe to test GPT directly
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_system_prompt():
    """Load the system prompt from file"""
    try:
        with open('prompts/system_prompt.md', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are a Last Z strategy expert. Be engaging and enthusiastic about gaming!"

def test_personality():
    """Test the personality with OpenAI API directly"""
    
    # Set up OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    system_prompt = load_system_prompt()
    
    test_messages = [
        {
            "role": "system", 
            "content": system_prompt
        },
        {
            "role": "user", 
            "content": "here are my heroes"
        }
    ]
    
    print("🧪 Testing personality with gpt-5-chat-latest...")
    print(f"📝 System prompt length: {len(system_prompt)} characters")
    print("\n" + "="*50)
    
    try:
        print("🔄 Sending request to gpt-5-chat-latest...")
        response = client.chat.completions.create(
            model="gpt-5-chat-latest",  # Non-reasoning GPT-5
            messages=test_messages,
            temperature=0.7,  # Should work with this model
            max_tokens=500
        )
        
        print("✅ Got response from gpt-5-chat-latest!")
        print(f"📊 Response object: {response}")
        print(f"📊 Choices length: {len(response.choices)}")
        print(f"📊 Message content: '{response.choices[0].message.content}'")
        print(f"📊 Content length: {len(response.choices[0].message.content or '')}")
        
        print("🤖 GPT Response:")
        print("-" * 50)
        content = response.choices[0].message.content
        if content:
            print(content)
        else:
            print("⚠️ EMPTY RESPONSE! Model returned no content")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Trying with GPT-4 as fallback...")
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=test_messages,
                temperature=0.7,
                max_tokens=500
            )
            
            print("🤖 GPT-4 Response:")
            print("-" * 50)
            print(response.choices[0].message.content)
            print("-" * 50)
            
        except Exception as e2:
            print(f"❌ GPT-4 also failed: {e2}")
            print("\n💡 Make sure OPENAI_API_KEY is set in your environment")

if __name__ == "__main__":
    test_personality()
from openai import OpenAI
from typing import List, Dict

class CaptionChatService:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            timeout=60.0,
            max_retries=3
        )
    
    def chat_edit_caption(
        self,
        current_caption: str,
        user_instruction: str,
        chat_history: List[Dict[str, str]],
        context: Dict
    ) -> str:
        """
        Use GPT-5.1 to edit caption based on user's conversational instruction.
        Maintains chat history for context.
        """
        
        # Build system prompt with context
        system_prompt = f"""You are a caption editing assistant for Urban Air Adventure Parks.

ORIGINAL CONTEXT:
- Location: {context.get('city', 'Unknown')}, {context.get('state', 'Unknown')}
- Post Goal: {context.get('goal', 'Unknown')}
- Platform: {context.get('platform', 'Unknown')}

Your job is to help refine social media captions based on user requests.
- Keep the local, authentic voice
- Maintain relevance to the location and goal
- Follow the user's editing instructions precisely
- Be conversational and helpful

CURRENT CAPTION:
{current_caption}

The user will ask you to modify this caption. Make the requested changes and return ONLY the updated caption text, nothing else."""

        # Build messages with chat history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for msg in chat_history:
            messages.append(msg)
        
        # Add current user instruction
        messages.append({"role": "user", "content": user_instruction})
        
        try:
            # Try GPT-5.1 first
            response = self.client.chat.completions.create(
                model="gpt-5.1",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"GPT-5.1 failed, falling back to GPT-4o: {e}")
            # Fallback to GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()

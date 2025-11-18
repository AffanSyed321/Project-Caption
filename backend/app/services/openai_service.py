import base64
from openai import OpenAI
from typing import Dict, Optional
import os


class OpenAIService:
    """Service for OpenAI Vision and GPT-4o interactions"""

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for Vision API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_image(self, image_path: str) -> str:
        """
        Use GPT-4o Vision to analyze the uploaded image
        Returns description of what the image shows and its purpose
        """
        try:
            base64_image = self.encode_image(image_path)

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this Urban Air promotional image. Describe:
1. What is shown in the image (activities, people, specific attractions)
2. The mood/tone of the image
3. What promotion or message it's trying to convey
4. Any text visible in the image
5. Target demographic (families, kids, teens, etc.)

Be concise but thorough."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def generate_caption(
        self,
        goal: str,
        image_analysis: str,
        local_research: Dict,
        platform: str
    ) -> str:
        """
        Generate localized caption using GPT-4o based on:
        - Goal of the post
        - Image analysis
        - Local area research
        - Target platform (Facebook or Instagram)
        """
        try:
            city = local_research.get("city", "")
            state = local_research.get("state", "")
            chamber_info = local_research.get("chamber_info", "")
            gov_info = local_research.get("government_info", "")
            is_rural = local_research.get("is_rural", False)

            # Build the prompt
            prompt = f"""You are a social media copywriter creating a {platform} caption for Urban Air Adventure Park in {city}, {state}.

**POST GOAL:** {goal}

**IMAGE ANALYSIS:**
{image_analysis}

**LOCAL AREA RESEARCH:**
Chamber of Commerce Info: {chamber_info[:500]}
Government/City Info: {gov_info[:500]}
Area Type: {"Rural" if is_rural else "Urban"}

**YOUR TASK:**
Create an authentic, localized social media caption that:
1. Achieves the stated goal
2. Reflects the local community's culture and vibe (not generic!)
3. Uses language that resonates with {city}, {state} residents
4. Matches the image content and tone
5. Feels personal and community-focused, NOT like a corporate template
6. Optimized for {platform}

**GUIDELINES:**
- Use local references when appropriate (local events, culture, community values)
- Keep it authentic - this should NOT feel like a location swap
- Include relevant hashtags (mix of Urban Air brand + local)
- {"Keep it concise and visual" if platform == "Instagram" else "Can be more detailed"}
- Include a clear call-to-action
- Do NOT use overly generic phrases like "Planning a BIRTHDAY BLAST?"
- Make it sound like it was written BY someone from {city}, FOR people in {city}

Generate the caption now:"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media copywriter who specializes in creating authentic, localized content that resonates with specific communities."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=0.9  # Higher temperature for more creative variety
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating caption: {str(e)}"

    def regenerate_caption(
        self,
        goal: str,
        image_analysis: str,
        local_research: Dict,
        platform: str,
        previous_caption: str
    ) -> str:
        """
        Regenerate a different version of the caption
        """
        try:
            city = local_research.get("city", "")
            state = local_research.get("state", "")
            chamber_info = local_research.get("chamber_info", "")
            gov_info = local_research.get("government_info", "")
            is_rural = local_research.get("is_rural", False)

            prompt = f"""You previously created this caption for Urban Air in {city}, {state}:

"{previous_caption}"

Now create a DIFFERENT version that:
- Has a different tone/approach
- Uses different local references
- Has different wording while maintaining the same goal
- Still feels authentic to {city}, {state}

**POST GOAL:** {goal}
**IMAGE ANALYSIS:** {image_analysis}
**LOCAL INFO:** Chamber: {chamber_info[:500]}
**PLATFORM:** {platform}

Create a fresh, alternative caption now:"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media copywriter creating alternative versions of localized content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=800,
                temperature=1.0  # Even higher temperature for more variety
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error regenerating caption: {str(e)}"

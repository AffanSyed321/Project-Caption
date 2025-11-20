import base64
from openai import OpenAI
from typing import Dict, Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config.brand_voice import get_brand_voice_prompt


class OpenAIService:
    """
    Service for OpenAI Vision and GPT-5.1 interactions

    HYBRID APPROACH:
    - GPT-4o: Image analysis (vision capability required)
    - GPT-5.1: Caption generation using Responses API with reasoning

    This ensures we can analyze images AND use the latest GPT-5.1 reasoning
    for high-quality, localized caption generation.
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            timeout=60.0,  # 60 second timeout for Railway
            max_retries=3   # Retry up to 3 times on connection errors
        )
        self.vision_model = "gpt-4o"  # Vision analysis (GPT-5.1 may not support vision yet)
        self.text_model = "gpt-5.1"   # Caption generation with Responses API + reasoning

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for Vision API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def encode_video(self, video_path: str) -> str:
        """Encode video to base64 for Vision API"""
        with open(video_path, "rb") as video_file:
            return base64.b64encode(video_file.read()).decode('utf-8')

    def is_video_file(self, filename: str) -> bool:
        """Check if file is a video"""
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
        return any(filename.lower().endswith(ext) for ext in video_extensions)

    def analyze_image(self, image_path: str) -> str:
        """
        Use GPT-4o Vision to analyze the uploaded image
        Returns description of what the image shows and its purpose
        """
        try:
            base64_image = self.encode_image(image_path)

            response = self.client.chat.completions.create(
                model=self.vision_model,
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

    def analyze_video(self, video_path: str) -> str:
        """
        Use GPT-4o Vision to analyze the uploaded video by extracting frames
        Returns description of what the video shows and its purpose
        """
        from app.services.video_service import VideoService

        video_service = VideoService()
        frame_paths = []

        try:
            # Extract key frames from video (5 frames evenly distributed)
            print(f"[VIDEO] Extracting frames from {video_path}")
            frame_paths = video_service.extract_key_frames(video_path, max_frames=5)
            print(f"[VIDEO] Extracted {len(frame_paths)} frames")

            if not frame_paths:
                return "Error: Could not extract frames from video"

            # Analyze each frame
            frame_analyses = []
            for idx, frame_path in enumerate(frame_paths):
                print(f"[VIDEO] Analyzing frame {idx + 1}/{len(frame_paths)}")
                base64_frame = self.encode_image(frame_path)

                response = self.client.chat.completions.create(
                    model=self.vision_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"This is frame {idx + 1} from a video. Briefly describe what you see in this moment."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_frame}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=150
                )

                frame_analyses.append(f"Frame {idx + 1}: {response.choices[0].message.content}")

            # Now synthesize all frame analyses into a cohesive video description
            synthesis_prompt = f"""Based on these {len(frame_analyses)} frames from an Urban Air promotional video, provide a comprehensive analysis:

Frames analyzed:
{chr(10).join(frame_analyses)}

Synthesize this into a cohesive video analysis covering:
1. What activities and attractions are shown throughout the video
2. The energy and atmosphere of the location
3. Key moments or highlights across the video
4. People shown (families, kids, teens, staff) and their interactions
5. Any text, graphics, or promotional messages visible
6. The overall message or promotion the video is conveying
7. Target demographic based on the content

Provide a comprehensive analysis that captures the full narrative and feel of the video."""

            synthesis_response = self.client.chat.completions.create(
                model=self.text_model if hasattr(self, 'text_model') else self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": synthesis_prompt
                    }
                ],
                max_tokens=600
            )

            return synthesis_response.choices[0].message.content

        except Exception as e:
            return f"Error analyzing video: {str(e)}"

        finally:
            # Clean up temporary frame files
            if frame_paths:
                print(f"[VIDEO] Cleaning up {len(frame_paths)} temporary frames")
                video_service.cleanup_frames(frame_paths)

    def analyze_media(self, file_path: str) -> str:
        """
        Analyze either image or video based on file type
        """
        if self.is_video_file(file_path):
            return self.analyze_video(file_path)
        else:
            return self.analyze_image(file_path)

    def generate_caption(
        self,
        goal: str,
        image_analysis: str,
        local_research: Dict,
        platform: str
    ) -> str:
        """
        Generate localized caption using GPT-5.1 based on:
        - Goal of the post
        - Image analysis
        - Local area research
        - Target platform (Facebook or Instagram)
        - Urban Air brand voice guidelines
        """
        try:
            city = local_research.get("city", "")
            state = local_research.get("state", "")
            chamber_info = local_research.get("chamber_info", "")
            gov_info = local_research.get("government_info", "")
            is_rural = local_research.get("is_rural", False)
            gpt_research = local_research.get("gpt_research", "")

            # Build the prompt with brand voice guidelines
            brand_voice = get_brand_voice_prompt()

            prompt = f"""You are a local social media personality creating a {platform} caption for Urban Air Adventure Park in {city}, {state}.
            
            {brand_voice}

            **POST GOAL:** {goal}

            **IMAGE/VIDEO ANALYSIS:**
            {image_analysis}

            **DEEP LOCAL RESEARCH:**
            {gpt_research[:4000]}

            **YOUR MISSION:**
            Write a caption that sounds like it was written by a LOCAL, for LOCALS.
            1. **Use the Research:** Reference specific local things mentioned in the research (neighborhoods, events, vibes).
            2. **No Tourist Speak:** Don't say "Welcome to [City]!" or generic phrases. Speak like you live there.
            3. **Authentic Voice:** If the research says locals are sarcastic, be sarcastic. If they are earnest, be earnest.
            4. **Platform Native:** Optimize for {platform} (hashtags, formatting).
            5. **Community Connection:** Make them feel like Urban Air is *part* of the community, not just a business in it.

            DO NOT sound like a corporate marketing bot. Be human, be local, be real."""

            # Use GPT-5.1 with High Reasoning (using chat.completions)
            response = self.client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert local copywriter who writes authentic, community-focused content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # High reasoning often requires higher max_tokens
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            # Fallback if GPT-5.1 is not available (graceful degradation)
            print(f"GPT-5.1 failed: {str(e)}. Falling back to GPT-4o.")
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert local copywriter."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                return response.choices[0].message.content
            except Exception as inner_e:
                return f"Error generating caption: {str(inner_e)}"

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
- Has a completely different angle or "hook"
- Uses different local references from the research
- Feels even MORE "insider" and local
- Still achieves the goal: {goal}

**PLATFORM:** {platform}

Create a fresh, authentic alternative now:"""

            # Use GPT-5.1 for regeneration
            response = self.client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert social media copywriter."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"GPT-5.1 failed: {str(e)}. Falling back to GPT-4o.")
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert social media copywriter."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.8,
                    max_tokens=800
                )
                return response.choices[0].message.content
            except Exception as inner_e:
                return f"Error regenerating caption: {str(inner_e)}"

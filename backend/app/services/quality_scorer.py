from openai import OpenAI
from typing import Dict
import json


class QualityScorer:
    """
    Uses GPT-5.1 to score caption quality and brand consistency
    This is what makes this better than just using ChatGPT manually
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def score_caption(
        self,
        caption: str,
        goal: str,
        location: str,
        image_analysis: str,
        brand_voice_followed: bool = True
    ) -> Dict:
        """
        Score caption on multiple dimensions:
        - Brand consistency (0-100)
        - Local relevance (0-100)
        - Goal alignment (0-100)
        - Overall quality (0-100)
        - Issues (list of problems)
        - Strengths (what works well)
        """

        prompt = f"""You are a quality control expert for Urban Air Adventure Parks reviewing a social media caption.

**CAPTION TO REVIEW:**
"{caption}"

**CONTEXT:**
- Goal: {goal}
- Location: {location}
- Image/Video Content: {image_analysis[:300]}

**SCORE THIS CAPTION ON:**

1. **Brand Consistency (0-100)**: Does it match Urban Air's energetic, family-friendly, community-focused voice? Avoids generic template language?

2. **Local Relevance (0-100)**: Does it feel authentic to {location}? Uses local references appropriately?

3. **Goal Alignment (0-100)**: Does it accomplish the stated goal: "{goal}"?

4. **Overall Quality (0-100)**: Grammar, clarity, engagement, call-to-action effectiveness

5. **Issues**: List any problems (max 3 bullet points)

6. **Strengths**: What works well (max 3 bullet points)

Return ONLY valid JSON in this exact format:
{{
  "brand_consistency": 85,
  "local_relevance": 90,
  "goal_alignment": 95,
  "overall_quality": 88,
  "overall_score": 89,
  "issues": ["Issue 1", "Issue 2"],
  "strengths": ["Strength 1", "Strength 2"],
  "recommendation": "Approve" or "Revise" or "Reject"
}}"""

        try:
            response = self.client.responses.create(
                model="gpt-5.1",
                input=prompt,
                reasoning={"effort": "medium"},  # Need thoughtful analysis
                text={"verbosity": "low"},  # Want concise JSON
                max_output_tokens=400
            )

            # Parse JSON response
            result_text = response.output_text.strip()

            # Try to extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()

            scores = json.loads(result_text)

            # Add quality tier
            overall = scores.get("overall_score", 0)
            if overall >= 90:
                scores["quality_tier"] = "Excellent"
            elif overall >= 80:
                scores["quality_tier"] = "Good"
            elif overall >= 70:
                scores["quality_tier"] = "Fair"
            else:
                scores["quality_tier"] = "Needs Improvement"

            return scores

        except Exception as e:
            print(f"Quality scoring error: {str(e)}")
            # Return default scores if scoring fails
            return {
                "brand_consistency": 75,
                "local_relevance": 75,
                "goal_alignment": 75,
                "overall_quality": 75,
                "overall_score": 75,
                "quality_tier": "Good",
                "issues": ["Could not analyze automatically"],
                "strengths": ["Manual review recommended"],
                "recommendation": "Review",
                "error": str(e)
            }

"""
Urban Air Brand Voice Guidelines
This ensures consistency across all 55+ locations
"""

BRAND_VOICE = {
    "tone": [
        "Energetic and enthusiastic",
        "Family-friendly and inclusive",
        "Authentic and community-focused",
        "Fun but professional",
        "Locally aware, not generic"
    ],

    "dos": [
        "Use local references and community events",
        "Emphasize family fun and safety",
        "Mention specific attractions (trampolines, warrior course, etc.)",
        "Include clear call-to-action",
        "Use emojis sparingly and appropriately",
        "Highlight what makes this location special"
    ],

    "donts": [
        "Generic location-swap language ('Planning a BIRTHDAY BLAST?')",
        "Excessive exclamation points (max 2 per caption)",
        "Corporate jargon or overly formal language",
        "Mentioning competitors",
        "Making false promises about availability or pricing",
        "Using slang that might not resonate with all demographics"
    ],

    "required_elements": [
        "Must mention the specific city/area",
        "Must relate to the posted image/video content",
        "Must have a clear call-to-action (book, visit, call, etc.)",
        "Must align with the stated goal"
    ],

    "style_preferences": {
        "caption_length": {
            "Facebook": "150-250 characters optimal, can go longer for storytelling",
            "Instagram": "100-150 characters + hashtags"
        },
        "hashtag_strategy": {
            "Facebook": "2-3 hashtags max, integrated naturally",
            "Instagram": "5-10 hashtags, mix of brand and local tags"
        },
        "emoji_usage": "1-3 per caption, relevant to content",
        "punctuation": "Conversational but not excessive"
    }
}


def get_brand_voice_prompt() -> str:
    """Generate a prompt section enforcing brand voice"""
    return f"""
**URBAN AIR BRAND VOICE REQUIREMENTS:**

TONE: {', '.join(BRAND_VOICE['tone'])}

YOU MUST:
{chr(10).join([f'- {rule}' for rule in BRAND_VOICE['dos']])}

NEVER:
{chr(10).join([f'- {rule}' for rule in BRAND_VOICE['donts']])}

REQUIRED:
{chr(10).join([f'- {rule}' for rule in BRAND_VOICE['required_elements']])}

This is NOT negotiable - violating these guidelines makes the caption unusable.
"""

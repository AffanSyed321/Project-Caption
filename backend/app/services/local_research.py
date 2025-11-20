from typing import Dict
import re
from openai import OpenAI


class LocalResearchService:
    """Service for researching local areas using GPT-5.1"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=3
            )

    def extract_city_state_from_address(self, address: str) -> Dict[str, str]:
        """Extract city and state from address string"""
        # State name to abbreviation mapping
        state_map = {
            'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
            'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
            'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
            'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
            'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
            'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
            'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
            'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
            'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
            'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'
        }

        # Try pattern with comma before city and 2-letter state: "123 Main St, Springfield, IL 62701"
        pattern1 = r',\s*([^,]+),\s*([A-Z]{2})\s*\d*'
        match = re.search(pattern1, address)
        if match:
            return {
                "city": match.group(1).strip(),
                "state": match.group(2).strip()
            }

        # Try pattern with comma before city and full state: "123 Main St, Springfield, Illinois 62701"
        pattern2 = r',\s*([^,]+),\s*([A-Za-z\s]+)\s*\d*'
        match = re.search(pattern2, address)
        if match:
            city = match.group(1).strip()
            state_full = match.group(2).strip().lower()
            state_abbr = state_map.get(state_full, state_full.upper())
            return {
                "city": city,
                "state": state_abbr
            }

        # Try to find state name in the address first, then extract city before it
        # Match: "anything  CityName, State  zip"
        for state_name, state_abbr in state_map.items():
            # Try full state name (case insensitive) - capture only words immediately before comma
            pattern = rf'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)\s*,\s*{state_name}\s*\d*$'
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                return {
                    "city": match.group(1).strip(),
                    "state": state_abbr
                }

        # Try pattern without comma, just spaces before city, with 2-letter state
        pattern3 = r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*),\s*([A-Z]{2})\s*\d*$'
        match = re.search(pattern3, address)
        if match:
            return {
                "city": match.group(1).strip(),
                "state": match.group(2).strip()
            }

        # If regex patterns fail, use GPT-5.1 to parse the address
        if self.api_key:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": f'Extract the city name and state from this address, return ONLY in this exact format: "City, ST" where ST is the 2-letter state code. Address: {address}'
                        }
                    ],
                    temperature=0,
                    max_tokens=20
                )
                # Parse response like "Springfield, IL"
                result_text = response.choices[0].message.content.strip()
                if ',' in result_text:
                    parts = result_text.split(',')
                    if len(parts) == 2:
                        return {
                            "city": parts[0].strip(),
                            "state": parts[1].strip()
                        }
            except Exception as e:
                print(f"GPT parsing failed: {str(e)}")

        return {"city": "", "state": ""}

    def research_with_gpt(self, city: str, state: str) -> str:
        """
        Use GPT-5.1 to research local area information
        This is more reliable than web scraping various website structures
        """
        if not self.api_key:
            return f"Basic information for {city}, {state} - API key not provided for detailed research"

        try:
            prompt = f"""Research and provide comprehensive, "insider" information about {city}, {state} for creating authentic, localized social media content for an Urban Air Adventure Park location.
            
            ACT LIKE A LOCAL. Dig deep beyond Wikipedia basics. I need:
            1. **Deep Demographics**: Not just numbers, but the *vibe*. Is it old money, blue collar, young families, commuters?
            2. **Hyper-Local Culture**: Specific neighborhoods, local rivalries, inside jokes, slang, or "if you know you know" references.
            3. **Hidden Gems & Habits**: Where do locals *actually* go? What are the specific weekend rituals?
            4. **Specific Events**: Not just "Summer Festival", but "The Gaspee Days Parade" or specific high school football rivalries.
            5. **Economic Reality**: What's the actual economic mood?
            6. **Voice & Tone**: How do locals speak? (e.g., "Wicked" in RI, specific regional dialects).
            7. **Community Priorities**: What are the hot topics or shared values right now?

            GOAL: The content must feel like it was written by a 28-35 year old resident, not a tourist or an AI. Be specific, gritty if needed, and authentic."""

            response = self.client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert local researcher."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"GPT-5.1 research failed: {str(e)}. Falling back to GPT-4o.")
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert local researcher."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.5,
                    max_tokens=2500
                )
                return response.choices[0].message.content
            except Exception as inner_e:
                print(f"Error researching with GPT: {str(inner_e)}")
                return f"Basic information for {city}, {state}"

    def research_location(self, address: str) -> Dict[str, any]:
        """
        Main research function that gathers all local information using GPT-5.1
        """
        # Extract city and state
        location = self.extract_city_state_from_address(address)
        city = location.get("city", "")
        state = location.get("state", "")

        if not city or not state:
            return {
                "error": "Could not parse city and state from address",
                "address": address
            }

        # Use GPT-5.1 to research the location
        research_info = self.research_with_gpt(city, state)

        # Determine if rural based on GPT response (simple heuristic)
        is_rural = "rural" in research_info.lower() and "suburban" not in research_info.lower()

        return {
            "city": city,
            "state": state,
            "address": address,
            "chamber_info": research_info,  # GPT research replaces chamber scraping
            "government_info": research_info,  # Same comprehensive research
            "is_rural": is_rural,
            "search_radius": 15 if is_rural else 10,
            "gpt_research": research_info  # Full GPT research for context
        }

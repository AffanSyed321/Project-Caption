import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import re


class LocalResearchService:
    """Service for researching local areas via web scraping"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def extract_city_state_from_address(self, address: str) -> Dict[str, str]:
        """Extract city and state from address string"""
        # Simple regex to extract city, state
        # Example: "123 Main St, Springfield, IL 62701" -> Springfield, IL
        pattern = r',\s*([^,]+),\s*([A-Z]{2})'
        match = re.search(pattern, address)

        if match:
            return {
                "city": match.group(1).strip(),
                "state": match.group(2).strip()
            }
        return {"city": "", "state": ""}

    def search_chamber_website(self, city: str, state: str) -> str:
        """Search for and scrape chamber of commerce website"""
        try:
            # Try to find chamber website
            search_query = f"{city} {state} chamber of commerce"
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

            # In production, you'd want to use proper search API or direct chamber URL
            # For now, we'll construct likely chamber URLs
            possible_urls = [
                f"https://www.{city.lower().replace(' ', '')}chamber.com",
                f"https://www.{city.lower().replace(' ', '')}{state.lower()}chamber.org",
                f"https://www.{city.lower().replace(' ', '')}chamberofcommerce.com"
            ]

            chamber_info = ""
            for url in possible_urls[:1]:  # Try first URL for now
                try:
                    response = requests.get(url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # Extract text from main content areas
                        text_content = soup.get_text(separator=' ', strip=True)[:3000]
                        chamber_info += text_content
                        break
                except:
                    continue

            return chamber_info if chamber_info else f"Chamber information for {city}, {state}"

        except Exception as e:
            return f"Unable to retrieve chamber info: {str(e)}"

    def search_government_website(self, city: str, state: str) -> str:
        """Search for and scrape official city/government website"""
        try:
            # Construct likely government URLs
            possible_urls = [
                f"https://www.ci.{city.lower().replace(' ', '-')}.{state.lower()}.us",
                f"https://www.{city.lower().replace(' ', '')}.gov",
                f"https://www.cityof{city.lower().replace(' ', '')}.com"
            ]

            gov_info = ""
            for url in possible_urls[:1]:  # Try first URL for now
                try:
                    response = requests.get(url, headers=self.headers, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        # Extract text from main content areas
                        text_content = soup.get_text(separator=' ', strip=True)[:3000]
                        gov_info += text_content
                        break
                except:
                    continue

            return gov_info if gov_info else f"Government information for {city}, {state}"

        except Exception as e:
            return f"Unable to retrieve government info: {str(e)}"

    def get_population_estimate(self, city: str, state: str) -> Dict[str, any]:
        """
        Estimate if area is rural or urban based on city name and state
        In production, this would use Census API or similar
        """
        # For now, return a simple structure
        # In production, integrate with Census API or similar service
        return {
            "city": city,
            "state": state,
            "is_rural": False,  # Default to urban
            "search_radius_miles": 10,  # Default radius
            "estimated_population": "unknown"
        }

    def research_location(self, address: str) -> Dict[str, any]:
        """
        Main research function that gathers all local information
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

        # Gather information
        chamber_info = self.search_chamber_website(city, state)
        gov_info = self.search_government_website(city, state)
        population_data = self.get_population_estimate(city, state)

        return {
            "city": city,
            "state": state,
            "address": address,
            "chamber_info": chamber_info,
            "government_info": gov_info,
            "population_data": population_data,
            "is_rural": population_data.get("is_rural", False),
            "search_radius": population_data.get("search_radius_miles", 10)
        }

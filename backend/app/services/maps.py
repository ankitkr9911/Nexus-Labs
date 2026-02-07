"""
Google Maps API integration
Handles distance calculation and navigation URL generation
"""
from typing import Dict, Any, List, Optional
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Google Maps Distance Matrix API handler"""
    
    def __init__(self):
        """Initialize Maps service"""
        if not settings.GOOGLE_MAPS_API_KEY:
            raise ValueError("GOOGLE_MAPS_API_KEY not set")
        
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    async def calculate_distance(
        self,
        origin: str,
        destination: str,
        modes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate distance and travel time between two points
        
        Args:
            origin: Starting location (address or "current location")
            destination: Ending location
            modes: Travel modes to check (driving, walking, transit)
        
        Returns:
            Dictionary with distance/time for each mode
        """
        if modes is None:
            modes = ["driving", "walking", "transit"]
        
        results = {}
        
        async with httpx.AsyncClient() as client:
            for mode in modes:
                try:
                    response = await client.get(
                        f"{self.base_url}/distancematrix/json",
                        params={
                            "origins": origin,
                            "destinations": destination,
                            "mode": mode,
                            "key": self.api_key
                        },
                        timeout=10.0
                    )
                    
                    data = response.json()
                    
                    if data["status"] == "OK":
                        element = data["rows"][0]["elements"][0]
                        
                        if element["status"] == "OK":
                            results[mode] = {
                                "distance": element["distance"]["text"],
                                "duration": element["duration"]["text"],
                                "distance_value": element["distance"]["value"],  # meters
                                "duration_value": element["duration"]["value"]   # seconds
                            }
                        else:
                            results[mode] = {"error": element["status"]}
                    else:
                        logger.warning(f"Maps API error for mode {mode}: {data['status']}")
                        
                except Exception as e:
                    logger.error(f"Error calculating distance for {mode}: {e}")
                    results[mode] = {"error": str(e)}
        
        return results
    
    def format_distance_summary(
        self,
        distance_data: Dict[str, Any],
        destination: str
    ) -> str:
        """
        Format distance data into human-readable summary
        
        Args:
            distance_data: Results from calculate_distance
            destination: Destination name
        
        Returns:
            Formatted summary text
        """
        summary_parts = [f"To {destination}:"]
        
        mode_labels = {
            "driving": "by car",
            "walking": "on foot",
            "transit": "by public transit"
        }
        
        for mode, data in distance_data.items():
            if "error" not in data:
                label = mode_labels.get(mode, mode)
                summary_parts.append(
                    f"• {data['duration']} {label} ({data['distance']})"
                )
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def generate_directions_url(
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> str:
        """
        Generate Google Maps directions URL
        
        Args:
            origin: Starting location
            destination: Ending location
            mode: Travel mode (driving, walking, transit, bicycling)
        
        Returns:
            Google Maps URL
        """
        # Use current location if origin is not specified
        origin_param = "Current+Location" if origin.lower() in ["current", "here", "my location"] else origin.replace(" ", "+")
        destination_param = destination.replace(" ", "+")
        
        return (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin_param}"
            f"&destination={destination_param}"
            f"&travelmode={mode}"
        )
    
    @staticmethod
    def generate_place_url(place_name: str) -> str:
        """
        Generate Google Maps place search URL
        
        Args:
            place_name: Name of place to search
        
        Returns:
            Google Maps search URL
        """
        place_param = place_name.replace(" ", "+")
        return f"https://www.google.com/maps/search/{place_param}"
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Convert address to coordinates
        
        Args:
            address: Address string
        
        Returns:
            Dictionary with lat/lng or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/geocode/json",
                    params={
                        "address": address,
                        "key": self.api_key
                    },
                    timeout=10.0
                )
                
                data = response.json()
                
                if data["status"] == "OK":
                    location = data["results"][0]["geometry"]["location"]
                    return {
                        "lat": location["lat"],
                        "lng": location["lng"],
                        "formatted_address": data["results"][0]["formatted_address"]
                    }
                else:
                    logger.warning(f"Geocoding failed: {data['status']}")
                    return None
                    
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None

"""
Spotify Web API integration
Handles music playback control and search
"""
from typing import Dict, Any, List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SpotifyService:
    """Spotify Web API handler"""
    
    def __init__(self, access_token: str):
        """
        Initialize Spotify service
        
        Args:
            access_token: Spotify OAuth access token
        """
        self.sp = spotipy.Spotify(auth=access_token)
    
    async def search_and_play(
        self,
        query: str,
        search_type: str = "track"
    ) -> Dict[str, Any]:
        """
        Search for music and start playback
        
        Args:
            query: Search query (song name, artist, genre)
            search_type: Type of search (track, playlist, album)
        
        Returns:
            Dictionary with playback status and track info
        """
        try:
            # Search for track/playlist
            results = self.sp.search(q=query, type=search_type, limit=1)
            
            if search_type == "track":
                items = results.get('tracks', {}).get('items', [])
                if not items:
                    return {"error": f"No tracks found for '{query}'"}
                
                track = items[0]
                track_uri = track['uri']
                
                # Start playback
                self.sp.start_playback(uris=[track_uri])
                
                return {
                    "status": "playing",
                    "track": {
                        "name": track['name'],
                        "artist": track['artists'][0]['name'],
                        "uri": track_uri,
                        "url": track['external_urls']['spotify']
                    }
                }
            
            elif search_type == "playlist":
                items = results.get('playlists', {}).get('items', [])
                if not items:
                    return {"error": f"No playlists found for '{query}'"}
                
                playlist = items[0]
                context_uri = playlist['uri']
                
                # Start playlist playback
                self.sp.start_playback(context_uri=context_uri)
                
                return {
                    "status": "playing",
                    "playlist": {
                        "name": playlist['name'],
                        "uri": context_uri,
                        "url": playlist['external_urls']['spotify']
                    }
                }
                
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify playback error: {e}")
            if "NO_ACTIVE_DEVICE" in str(e):
                return {"error": "No active Spotify device found. Please open Spotify on a device."}
            return {"error": str(e)}
    
    async def pause_playback(self) -> Dict[str, Any]:
        """
        Pause current playback
        
        Returns:
            Status dictionary
        """
        try:
            self.sp.pause_playback()
            return {"status": "paused"}
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify pause error: {e}")
            return {"error": str(e)}
    
    async def resume_playback(self) -> Dict[str, Any]:
        """
        Resume playback
        
        Returns:
            Status dictionary
        """
        try:
            self.sp.start_playback()
            return {"status": "playing"}
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify resume error: {e}")
            return {"error": str(e)}
    
    async def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get currently playing track
        
        Returns:
            Current track information or None
        """
        try:
            current = self.sp.current_playback()
            
            if not current or not current.get('item'):
                return None
            
            track = current['item']
            
            return {
                "name": track['name'],
                "artist": track['artists'][0]['name'],
                "album": track['album']['name'],
                "is_playing": current['is_playing'],
                "progress_ms": current['progress_ms'],
                "duration_ms": track['duration_ms'],
                "url": track['external_urls']['spotify']
            }
            
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Error getting current track: {e}")
            return None
    
    async def skip_to_next(self) -> Dict[str, Any]:
        """
        Skip to next track
        
        Returns:
            Status dictionary
        """
        try:
            self.sp.next_track()
            return {"status": "skipped"}
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify skip error: {e}")
            return {"error": str(e)}
    
    async def skip_to_previous(self) -> Dict[str, Any]:
        """
        Skip to previous track
        
        Returns:
            Status dictionary
        """
        try:
            self.sp.previous_track()
            return {"status": "skipped_back"}
        except spotipy.exceptions.SpotifyException as e:
            logger.error(f"Spotify previous error: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def generate_spotify_url(
        uri: Optional[str] = None,
        url_type: str = "app"
    ) -> str:
        """
        Generate Spotify web/app URL
        
        Args:
            uri: Spotify URI (track, playlist, etc.)
            url_type: 'app' or 'web'
        
        Returns:
            Spotify URL
        """
        if not uri:
            return "https://open.spotify.com"
        
        # Extract ID from URI (spotify:track:xxx -> xxx)
        if ":" in uri:
            parts = uri.split(":")
            resource_type = parts[1]  # track, playlist, album
            resource_id = parts[2]
            return f"https://open.spotify.com/{resource_type}/{resource_id}"
        
        return "https://open.spotify.com"
    
    def format_track_info(self, track_data: Dict[str, Any]) -> str:
        """
        Format track information for voice response
        
        Args:
            track_data: Track information dictionary
        
        Returns:
            Formatted string
        """
        if "error" in track_data:
            return track_data["error"]
        
        if "track" in track_data:
            track = track_data["track"]
            return f"Now playing: {track['name']} by {track['artist']}"
        
        if "playlist" in track_data:
            playlist = track_data["playlist"]
            return f"Now playing playlist: {playlist['name']}"
        
        return "Playback started"

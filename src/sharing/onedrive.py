"""
OneDrive uploader for cloud photo sharing.
"""

import os
import logging
import threading
import json
from typing import Optional, List, Callable
from pathlib import Path

try:
    import msal
    import requests
    MSAL_AVAILABLE = True
except ImportError:
    MSAL_AVAILABLE = False


logger = logging.getLogger(__name__)


class OneDriveUploader:
    """
    Uploads photos to OneDrive for easy sharing.
    Uses Microsoft Authentication Library (MSAL) for OAuth2.
    """
    
    # Microsoft Graph API endpoints
    GRAPH_URL = "https://graph.microsoft.com/v1.0"
    AUTHORITY = "https://login.microsoftonline.com/consumers"
    SCOPES = ["Files.ReadWrite"]
    
    def __init__(self, config: dict = None):
        """
        Initialize OneDrive uploader.
        
        Args:
            config: Configuration dictionary
        """
        if not MSAL_AVAILABLE:
            logger.warning("MSAL not available. Install with: pip install msal requests")
        
        self.config = config or {}
        self.sharing_config = self.config.get('sharing', {})
        
        self._client_id = self.sharing_config.get('onedrive_client_id', '')
        self._folder_name = self.sharing_config.get('onedrive_folder', 'PhotoBooth')
        self._token_cache_path = os.path.expanduser('~/.photobooth_token_cache.json')
        
        self._access_token: Optional[str] = None
        self._msal_app: Optional[msal.PublicClientApplication] = None
        self._upload_callback: Optional[Callable] = None
        
        if MSAL_AVAILABLE and self._client_id:
            self._init_msal()
    
    def _init_msal(self) -> None:
        """Initialize MSAL application."""
        # Load token cache if exists
        cache = msal.SerializableTokenCache()
        if os.path.exists(self._token_cache_path):
            with open(self._token_cache_path, 'r') as f:
                cache.deserialize(f.read())
        
        self._msal_app = msal.PublicClientApplication(
            self._client_id,
            authority=self.AUTHORITY,
            token_cache=cache
        )
    
    def is_configured(self) -> bool:
        """Check if OneDrive is configured."""
        return bool(self._client_id) and MSAL_AVAILABLE
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        if self._access_token:
            return True
        
        if self._msal_app:
            accounts = self._msal_app.get_accounts()
            if accounts:
                result = self._msal_app.acquire_token_silent(
                    self.SCOPES,
                    account=accounts[0]
                )
                if result and 'access_token' in result:
                    self._access_token = result['access_token']
                    return True
        
        return False
    
    def get_auth_url(self) -> Optional[str]:
        """
        Get the authentication URL for device code flow.
        
        Returns:
            URL string for authentication
        """
        if not self._msal_app:
            return None
        
        flow = self._msal_app.initiate_device_flow(scopes=self.SCOPES)
        if 'user_code' in flow:
            return flow.get('verification_uri_complete', flow.get('verification_uri'))
        
        return None
    
    def authenticate_with_device_code(self) -> bool:
        """
        Authenticate using device code flow (for headless devices).
        
        Returns:
            True if authentication successful
        """
        if not self._msal_app:
            return False
        
        flow = self._msal_app.initiate_device_flow(scopes=self.SCOPES)
        
        if 'user_code' not in flow:
            logger.error(f"Failed to create device flow: {flow.get('error_description')}")
            return False
        
        logger.info(f"Please visit: {flow['verification_uri']}")
        logger.info(f"Enter code: {flow['user_code']}")
        
        # This will block until user completes authentication
        result = self._msal_app.acquire_token_by_device_flow(flow)
        
        if 'access_token' in result:
            self._access_token = result['access_token']
            self._save_token_cache()
            logger.info("OneDrive authentication successful")
            return True
        
        logger.error(f"Authentication failed: {result.get('error_description')}")
        return False
    
    def upload_photos(self, photo_paths: List[str], 
                     progress_callback: Optional[Callable] = None) -> Optional[str]:
        """
        Upload photos to OneDrive.
        
        Args:
            photo_paths: List of photo file paths to upload
            progress_callback: Optional callback(current, total) for progress updates
        
        Returns:
            Shareable link URL, or None on failure
        """
        if not self.is_authenticated():
            if not self.authenticate_with_device_code():
                return None
        
        try:
            # Create folder if it doesn't exist
            folder_id = self._ensure_folder_exists()
            if not folder_id:
                logger.error("Failed to create/find OneDrive folder")
                return None
            
            # Create session subfolder
            import time
            session_name = time.strftime("%Y%m%d_%H%M%S")
            session_folder_id = self._create_folder(session_name, folder_id)
            
            if not session_folder_id:
                session_folder_id = folder_id
            
            # Upload each photo
            total = len(photo_paths)
            for i, photo_path in enumerate(photo_paths):
                if progress_callback:
                    progress_callback(i + 1, total)
                
                filename = os.path.basename(photo_path)
                self._upload_file(photo_path, filename, session_folder_id)
            
            # Create sharing link
            share_url = self._create_share_link(session_folder_id)
            
            logger.info(f"Uploaded {total} photos to OneDrive")
            return share_url
            
        except Exception as e:
            logger.error(f"OneDrive upload failed: {e}")
            return None
    
    def upload_photos_async(self, photo_paths: List[str],
                           completion_callback: Callable[[Optional[str]], None]) -> None:
        """
        Upload photos asynchronously.
        
        Args:
            photo_paths: List of photo file paths
            completion_callback: Called with share URL or None on completion
        """
        def upload_thread():
            result = self.upload_photos(photo_paths)
            completion_callback(result)
        
        thread = threading.Thread(target=upload_thread, daemon=True)
        thread.start()
    
    def _ensure_folder_exists(self) -> Optional[str]:
        """Ensure the PhotoBooth folder exists in OneDrive root."""
        # Try to get existing folder
        response = self._make_api_request(
            'GET',
            f'/me/drive/root:/{self._folder_name}'
        )
        
        if response and 'id' in response:
            return response['id']
        
        # Create folder
        return self._create_folder(self._folder_name)
    
    def _create_folder(self, name: str, parent_id: str = None) -> Optional[str]:
        """Create a folder in OneDrive."""
        if parent_id:
            endpoint = f"/me/drive/items/{parent_id}/children"
        else:
            endpoint = "/me/drive/root/children"
        
        response = self._make_api_request(
            'POST',
            endpoint,
            json={
                'name': name,
                'folder': {},
                '@microsoft.graph.conflictBehavior': 'rename'
            }
        )
        
        if response and 'id' in response:
            return response['id']
        
        return None
    
    def _upload_file(self, file_path: str, filename: str, 
                    folder_id: str) -> bool:
        """Upload a file to OneDrive."""
        file_size = os.path.getsize(file_path)
        
        # For small files (< 4MB), use simple upload
        if file_size < 4 * 1024 * 1024:
            with open(file_path, 'rb') as f:
                response = self._make_api_request(
                    'PUT',
                    f"/me/drive/items/{folder_id}:/{filename}:/content",
                    data=f.read(),
                    headers={'Content-Type': 'application/octet-stream'}
                )
                return response is not None
        
        # For larger files, use upload session
        # (Simplified - would need chunked upload for large files)
        return False
    
    def _create_share_link(self, item_id: str) -> Optional[str]:
        """Create a sharing link for a OneDrive item."""
        response = self._make_api_request(
            'POST',
            f"/me/drive/items/{item_id}/createLink",
            json={
                'type': 'view',
                'scope': 'anonymous'
            }
        )
        
        if response and 'link' in response:
            return response['link'].get('webUrl')
        
        return None
    
    def _make_api_request(self, method: str, endpoint: str, **kwargs) -> Optional[dict]:
        """Make an authenticated API request."""
        if not self._access_token:
            return None
        
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f'Bearer {self._access_token}'
        
        url = f"{self.GRAPH_URL}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            
            if response.status_code == 401:
                # Token expired, try to refresh
                self._access_token = None
                if self.is_authenticated():
                    return self._make_api_request(method, endpoint, **kwargs)
                return None
            
            if response.status_code in (200, 201):
                return response.json()
            
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
    
    def _save_token_cache(self) -> None:
        """Save the token cache to disk."""
        if self._msal_app and self._msal_app.token_cache.has_state_changed:
            with open(self._token_cache_path, 'w') as f:
                f.write(self._msal_app.token_cache.serialize())

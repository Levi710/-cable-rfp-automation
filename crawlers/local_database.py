"""
Load tenders from local JSON database.
Fallback when API connectivity fails.
"""

import json
import logging
from typing import List, Dict
import os

logger = logging.getLogger(__name__)

class LocalTenderDatabase:
    """
    Load tenders from local JSON file.
    No internet required!
    """
    
    def __init__(self, json_file: str = "data/local_tenders.json"):
        self.json_file = json_file
    
    def load_tenders(self) -> List[Dict]:
        """Load tenders from local JSON file."""
        
        try:
            if not os.path.exists(self.json_file):
                logger.warning(f"⚠️ Local database not found: {self.json_file}")
                return []
            
            with open(self.json_file, 'r') as f:
                data = json.load(f)
            
            tenders = data.get('tenders', [])
            
            logger.info(f"✅ Loaded {len(tenders)} tenders from local database")
            
            return tenders
        
        except Exception as e:
            logger.error(f"❌ Error loading local database: {str(e)}")
            return []

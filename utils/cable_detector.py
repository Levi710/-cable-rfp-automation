"""
Enhanced cable detection with scoring system.
"""

import re
import logging

logger = logging.getLogger(__name__)

class CableDetector:
    """
    Advanced cable tender detection.
    """
    
    def __init__(self):
        # Primary cable keywords (high confidence)
        self.primary_keywords = [
            'cable', 'wire', 'conductor', 'xlpe', 'pvc',
            'power cable', 'transmission cable', 'distribution cable',
            'underground cable', 'overhead cable', 'armored cable'
        ]
        
        # Secondary keywords (supporting evidence)
        self.secondary_keywords = [
            'electrical', 'voltage', 'kv', 'ampere', 'insulation',
            'copper', 'aluminum', 'aluminium', 'stranded', 'core'
        ]
        
        # Voltage patterns (strong indicator)
        self.voltage_pattern = re.compile(
            r'(\d+)\s*(kv|v|kilovolt|volt)',
            re.IGNORECASE
        )
        
        # Negative keywords (exclude these)
        self.negative_keywords = [
            'furniture', 'stationery', 'office', 'building',
            'construction', 'vehicle', 'food', 'uniform',
            'catering', 'housekeeping', 'security'
        ]
    
    def is_cable_tender(self, tender: dict, threshold: float = 0.6) -> bool:
        """
        Determine if tender is cable-related.
        
        Returns: True if confidence > threshold
        """
        
        score, details = self.calculate_cable_score(tender)
        
        logger.debug(f"Cable score: {score:.2f} for '{tender.get('title', '')[:50]}'")
        
        return score >= threshold
    
    def calculate_cable_score(self, tender: dict) -> tuple:
        """
        Calculate cable relevance score (0-1).
        
        Returns: (score, details_dict)
        """
        
        text = (
            tender.get('title', '') + ' ' +
            tender.get('description', '')
        ).lower()
        
        score = 0.0
        details = {}
        
        # Check primary keywords (0.5 max)
        primary_matches = [kw for kw in self.primary_keywords if kw in text]
        if primary_matches:
            score += min(len(primary_matches) * 0.15, 0.5)
            details['primary_keywords'] = primary_matches
        
        # Check secondary keywords (0.2 max)
        secondary_matches = [kw for kw in self.secondary_keywords if kw in text]
        if secondary_matches:
            score += min(len(secondary_matches) * 0.05, 0.2)
            details['secondary_keywords'] = secondary_matches
        
        # Check voltage pattern (0.3 bonus)
        voltage_matches = self.voltage_pattern.findall(text)
        if voltage_matches:
            score += 0.3
            details['voltage'] = voltage_matches
        
        # Penalty for negative keywords
        negative_matches = [kw for kw in self.negative_keywords if kw in text]
        if negative_matches:
            score -= 0.4
            details['negative_keywords'] = negative_matches
        
        # Ensure score is between 0-1
        score = max(0.0, min(1.0, score))
        
        details['final_score'] = score
        
        return score, details

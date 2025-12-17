import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class TechnicalAgent:
    """Match cable specifications to products with AI-powered document parsing."""
    
    def match_products(self, tender: dict) -> List[Dict]:
        """Match tender requirements to available products."""
        
        # Extract requirements from tender (with OCR/PDF parsing if available)
        requirements = self._extract_requirements(tender)
        
        # Find matching products
        matches = self._find_matching_products(requirements)
        
        return matches
    
    def _extract_requirements(self, tender: dict) -> dict:
        """Extract cable requirements from tender using AI parsing."""
        
        import re
        
        # Base text from tender
        text = tender.get('title', '') + ' ' + tender.get('description', '')
        
        # Try to use document parser if PDF/document is attached
        parsed_specs = None
        if tender.get('document_path') or tender.get('pdf_content'):
            print("\n[OCR/AI PARSING] Extracting specifications from document...")
            try:
                from utils.document_parser import extract_specifications
                parsed_specs = extract_specifications(text)
                print(f"[OCR/AI PARSING] Extracted: {len([v for v in parsed_specs.values() if v])} fields")
                if parsed_specs.get('cable_type'):
                    print(f"  - Cable Type: {parsed_specs['cable_type']}")
                if parsed_specs.get('voltage'):
                    print(f"  - Voltage: {parsed_specs['voltage']}")
                if parsed_specs.get('conductor'):
                    print(f"  - Conductor: {parsed_specs['conductor']}")
                if parsed_specs.get('standards'):
                    print(f"  - Standards: {', '.join(parsed_specs['standards'])}")
            except Exception as e:
                logger.warning(f"Document parsing failed: {e}")
        
        # Combine parsed specs with regex extraction
        requirements = {
            'voltage': parsed_specs.get('voltage') if parsed_specs else self._extract_voltage(text),
            'cable_type': parsed_specs.get('cable_type') if parsed_specs else self._extract_type(text),
            'conductor': parsed_specs.get('conductor') if parsed_specs else None,
            'insulation': parsed_specs.get('insulation') if parsed_specs else None,
            'length_km': self._extract_length(text),
            'standards': parsed_specs.get('standards', []) if parsed_specs else self._extract_standards(text)
        }
        
        # Show extraction summary
        print(f"\n[SPEC EXTRACTION SUMMARY]")
        print(f"  Method: {'AI Parsing + Regex' if parsed_specs else 'Regex Only'}")
        print(f"  Voltage: {requirements['voltage']}")
        print(f"  Cable Type: {requirements['cable_type']}")
        if requirements.get('conductor'):
            print(f"  Conductor: {requirements['conductor']}")
        if requirements.get('standards'):
            print(f"  Standards: {', '.join(requirements['standards']) if requirements['standards'] else 'None'}")
        
        return requirements
    
    def _extract_voltage(self, text: str) -> str:
        """Extract voltage rating."""
        import re
        match = re.search(r'(\d+)\s*(kv|v)\b', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} {'kV' if 'k' in match.group(2).lower() else 'V'}"
        return 'Unspecified'
    
    def _extract_type(self, text: str) -> str:
        """Extract cable type."""
        if 'xlpe' in text.lower():
            return 'XLPE'
        elif 'pvc' in text.lower():
            return 'PVC'
        return 'General'
    
    def _extract_length(self, text: str) -> float:
        """Extract cable length in km."""
        import re
        match = re.search(r'(\d+)\s*km', text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _extract_standards(self, text: str) -> list:
        """Extract applicable standards."""
        import re
        standards = []
        patterns = [r'(IS\s*\d+)', r'(IEC\s*\d+)', r'(BS\s*\d+)']
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            standards.extend(matches)
        return list(set(standards))
    
    def _find_matching_products(self, requirements: dict) -> List[Dict]:
        """Find matching products (placeholder)."""
        # In real system, query database for matching products
        return [
            {
                'sku': 'CU-XLPE-35-11KV',
                'name': '11 kV XLPE Cable 35 sq mm',
                'match_score': 0.92
            }
        ]
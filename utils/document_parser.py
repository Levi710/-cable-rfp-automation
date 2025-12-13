"""
Document parsing utility for PDF tender documents.
Uses PDFMiner for text extraction with optional OCR fallback.
"""

import logging
from typing import Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)

def parse_pdf(pdf_path_or_bytes: Any) -> Dict[str, Any]:
    """
    Parse PDF document and extract text.
    
    Args:
        pdf_path_or_bytes: Path to PDF file or bytes
        
    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        from pdfminer.high_level import extract_text
        
        # Handle both file path and bytes
        if isinstance(pdf_path_or_bytes, bytes):
            text = extract_text(BytesIO(pdf_path_or_bytes))
        else:
            text = extract_text(pdf_path_or_bytes)
        
        return {
            'text': text,
            'method': 'pdfminer',
            'success': True,
            'page_count': text.count('\x0c') + 1  # Form feed character
        }
        
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        return {
            'text': '',
            'method': 'failed',
            'success': False,
            'error': str(e)
        }


def extract_specifications(text: str) -> Dict[str, Any]:
    """
    Extract cable specifications from document text.
    
    Args:
        text: Document text
        
    Returns:
        Dictionary of extracted specifications
    """
    specs = {
        'cable_type': None,
        'voltage': None,
        'conductor': None,
        'insulation': None,
        'quantity': None,
        'standards': []
    }
    
    # Simple keyword extraction (can be enhanced with NLP)
    text_lower = text.lower()
    
    # Extract cable types
    if 'xlpe' in text_lower:
        specs['cable_type'] = 'XLPE'
    elif 'pvc' in text_lower:
        specs['cable_type'] = 'PVC'
    elif 'aerial' in text_lower:
        specs['cable_type'] = 'Aerial Bundle'
    
    # Extract voltage
    import re
    voltage_patterns = [
        r'(\d+)\s*kv',
        r'(\d+)\s*v\s*(?:rated|class)',
    ]
    for pattern in voltage_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            specs['voltage'] = f"{matches[0]} kV" if int(matches[0]) > 1000 else f"{matches[0]} V"
            break
    
    # Extract conductor material
    if 'copper' in text_lower or 'cu' in text_lower:
        specs['conductor'] = 'Copper'
    elif 'aluminum' in text_lower or 'aluminium' in text_lower or 'al' in text_lower:
        specs['conductor'] = 'Aluminum'
    
    # Extract standards
    standards_keywords = ['is 1554', 'is 7098', 'iec 60502', 'iec 60332', 'bs 6346']
    for std in standards_keywords:
        if std in text_lower:
            specs['standards'].append(std.upper())
    
    return specs


def parse_tender_document(pdf_path_or_bytes: Any) -> Dict[str, Any]:
    """
    Parse complete tender document and extract structured data.
    
    Args:
        pdf_path_or_bytes: Path to PDF or bytes
        
    Returns:
        Parsed tender data with specifications
    """
    # Parse PDF
    parsed = parse_pdf(pdf_path_or_bytes)
    
    if not parsed['success']:
        return parsed
    
    # Extract specifications
    specs = extract_specifications(parsed['text'])
    
    return {
        'raw_text': parsed['text'],
        'specifications': specs,
        'method': parsed['method'],
        'success': True,
        'page_count': parsed.get('page_count', 0)
    }

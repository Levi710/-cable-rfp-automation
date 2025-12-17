"""
Distributed tracing utility for Jaeger instrumentation.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer = None

def init_tracer():
    """Initialize global tracer instance."""
    global _tracer
    if _tracer is None:
        try:
            from ai_enhancements.jaeger_tracing import init_jaeger
            _tracer = init_jaeger('cable-rfp-system')
            logger.info("Jaeger tracer initialized")
        except Exception as e:
            logger.warning(f"Jaeger tracer initialization failed: {e}")
    return _tracer

def get_tracer():
    """Get global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = init_tracer()
    return _tracer

@contextmanager
def trace_span(operation_name: str, tags: Optional[Dict[str, Any]] = None):
    """
    Context manager for creating traced spans.
    
    Usage:
        with trace_span('discover_tenders', {'source': 'GeM'}):
            # your code here
            pass
    """
    tracer = get_tracer()
    
    if tracer is None:
        # No-op if tracer not available
        yield None
        return
    
    try:
        with tracer.start_span(operation_name) as span:
            if tags:
                for key, value in tags.items():
                    span.set_tag(key, str(value))
            yield span
    except Exception as e:
        logger.debug(f"Span error for {operation_name}: {e}")
        yield None

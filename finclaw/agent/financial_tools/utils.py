import math
from typing import Any

def sanitize_json(obj: Any) -> Any:
    """
    Recursively replaces NaN, Inf, and -Inf with None for JSON compliance.
    
    This ensures that tool results containing float('nan') or float('inf') 
    from libraries like Pandas/yfinance do not crash the LLM API JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(v) for v in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj

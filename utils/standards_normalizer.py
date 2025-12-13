import re
from typing import Dict

NORMALIZE_MAP = {
    'armoured': 'Armored',
    'armored': 'Armored',
    'xlpe': 'XLPE',
    'pvc': 'PVC',
    'aluminium': 'Aluminum',
    'aluminum': 'Aluminum',
    'copper': 'Copper',
}

VOLTAGE_RE = re.compile(r"(\d{1,3})\s*k\s*V", re.IGNORECASE)

def normalize_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    v = value.strip()
    low = v.lower()
    for k, mapped in NORMALIZE_MAP.items():
        if low == k:
            return mapped
    return v

def normalize_voltage(value: str) -> str:
    if not value:
        return value
    m = VOLTAGE_RE.search(value)
    if m:
        return f"{m.group(1)} kV"
    return value

def normalize_specs(specs: Dict) -> Dict:
    out = dict(specs or {})
    out['cable_type'] = normalize_text(out.get('cable_type', ''))
    out['insulation_type'] = normalize_text(out.get('insulation_type', ''))
    out['conductor_material'] = normalize_text(out.get('conductor_material', ''))
    out['armoring'] = 'Armored' if normalize_text(out.get('armoring', '')) in ['Armored'] else 'Unarmored' if out.get('armoring') else out.get('armoring')
    if out.get('voltage'):
        out['voltage'] = normalize_voltage(str(out['voltage']))
    return out

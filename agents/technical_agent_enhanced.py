import logging
from typing import List, Dict, Tuple
import re

logger = logging.getLogger(__name__)

class TechnicalAgentEnhanced:
    """
    Technical Agent: Receives RFP summary, recommends top 3 OEM products with comparison tables.
    Uses equal weightage for all spec parameters.
    """
    
    def __init__(self):
        # Product catalog from datasheets with fallback
        self.product_catalog = self._load_product_catalog()
    
    def process_rfp(self, rfp_summary: Dict) -> Dict:
        """
        Main processing: Receives RFP summary from main agent.
        Returns top 3 OEM recommendations with comparison tables.
        """
        
        logger.info("Technical Agent: Processing RFP summary")
        
        # Extract scope of supply from RFP summary
        scope_of_supply = rfp_summary.get('scope_of_supply', [])
        product_requirements = rfp_summary.get('product_requirements', {})
        
        results = {
            'scope_summary': self._summarize_scope(scope_of_supply),
            'products': []
        }
        
        # Process each item in scope of supply
        for item in scope_of_supply:
            item_result = self._process_scope_item(item, product_requirements)
            results['products'].append(item_result)
        
        # Generate final selection table
        results['final_selection_table'] = self._generate_final_selection(results['products'])
        
        logger.info(f"Technical Agent: Processed {len(scope_of_supply)} items in scope")
        
        return results
    
    def _summarize_scope(self, scope_of_supply: List[Dict]) -> str:
        """Summarize products in scope of supply."""
        
        if not scope_of_supply:
            return "No items in scope"
        
        summary_lines = []
        for item in scope_of_supply:
            summary_lines.append(
                f"Item {item.get('item_no')}: {item.get('description')} - "
                f"{item.get('quantity')} {item.get('unit')}"
            )
        
        return "\n".join(summary_lines)
    
    def _process_scope_item(self, item: Dict, requirements: Dict) -> Dict:
        """
        Process single scope item: find top 3 OEM matches, create comparison table.
        Uses EQUAL WEIGHTAGE for all spec parameters.
        """
        
        # Get RFP requirements for this item
        rfp_specs = self._extract_rfp_specs(item, requirements)
        
        # Normalize specs for consistent comparison
        try:
            from utils.standards_normalizer import normalize_specs
            rfp_specs = normalize_specs(rfp_specs)
        except Exception:
            pass
        
        # Find all matching products
        candidate_products = self._find_candidate_products(rfp_specs)
        
        # Score each product with EQUAL WEIGHTAGE
        scored_products = []
        for product in candidate_products:
            match_score = self._calculate_spec_match_equal_weight(rfp_specs, product)
            scored_products.append({
                'product': product,
                'match_score': match_score
            })
        
        # Sort by match score and get top 3
        scored_products.sort(key=lambda x: x['match_score'], reverse=True)
        top_3 = scored_products[:3]
        
        # Generate comparison table
        comparison_table = self._generate_comparison_table(rfp_specs, top_3)
        
        # Build basic compliance items with evidence
        compliance_items = self._generate_compliance_items(rfp_specs, top_3[0]['product'] if top_3 else None)
        
        # Select top product
        selected_product = top_3[0]['product'] if top_3 else None
        
        return {
            'item_no': item.get('item_no'),
            'description': item.get('description'),
            'rfp_specs': rfp_specs,
            'top_3_recommendations': [
                {
                    'rank': i + 1,
                    'sku': rec['product']['sku'],
                    'name': rec['product']['name'],
                    'match_score': rec['match_score'],
                    'specs': rec['product']['specs']
                }
                for i, rec in enumerate(top_3)
            ],
'comparison_table': comparison_table,
            'compliance_items': compliance_items,
            'selected_product': {
                'sku': selected_product['sku'],
                'name': selected_product['name'],
                'match_score': top_3[0]['match_score']
            } if selected_product else None
        }
    
    def _extract_rfp_specs(self, item: Dict, requirements: Dict) -> Dict:
        """Extract RFP specifications for matching."""
        
        return {
            'voltage': item.get('voltage') or requirements.get('voltage', 'Unknown'),
            'cable_type': item.get('cable_type') or requirements.get('cable_type', 'Unknown'),
            'conductor_material': requirements.get('conductor_material', 'Copper'),
            'insulation_type': requirements.get('insulation_type', 'XLPE'),
            'armoring': requirements.get('armoring', 'Unarmored'),
            'cores': requirements.get('cores', '3-core'),
            'standards': requirements.get('standards', ['IS 7098'])
        }
    
    def _find_candidate_products(self, rfp_specs: Dict) -> List[Dict]:
        """Find candidate OEM products from catalog."""
        
        candidates = []
        
        # Filter products by basic criteria
        for product in self.product_catalog:
            # Must match cable type
            if product['specs']['cable_type'] == rfp_specs.get('cable_type'):
                candidates.append(product)
            # Or close voltage match
            elif self._voltage_match(rfp_specs.get('voltage', ''), product['specs']['voltage']):
                candidates.append(product)
        
        return candidates if candidates else self.product_catalog[:5]  # Return some products if none match
    
    def _calculate_spec_match_equal_weight(self, rfp_specs: Dict, product: Dict) -> float:
        """
        Calculate spec match percentage with EQUAL WEIGHTAGE for all parameters.
        Each parameter contributes equally to the final score.
        """
        
        product_specs = product['specs']
        
        # Define all parameters to check (equal weightage)
        parameters = [
            ('voltage', self._voltage_match),
            ('cable_type', lambda a, b: a == b),
            ('conductor_material', lambda a, b: a.lower() == b.lower()),
            ('insulation_type', lambda a, b: a == b),
            ('armoring', lambda a, b: a == b),
            ('cores', lambda a, b: a == b),
            ('standards', self._standards_match)
        ]
        
        matches = 0
        total_params = len(parameters)
        
        for param_name, match_func in parameters:
            rfp_value = rfp_specs.get(param_name)
            product_value = product_specs.get(param_name)
            
            if rfp_value and product_value:
                if match_func(rfp_value, product_value):
                    matches += 1
        
        # Equal weightage: each parameter = 1/total_params
        match_percentage = (matches / total_params) * 100
        
        return round(match_percentage, 2)
    
    def _voltage_match(self, rfp_voltage: str, product_voltage: str) -> bool:
        """Check if voltages match (allowing slight variations)."""
        
        # Extract numeric values
        rfp_val = re.search(r'(\d+)', str(rfp_voltage))
        prod_val = re.search(r'(\d+)', str(product_voltage))
        
        if rfp_val and prod_val:
            return abs(int(rfp_val.group(1)) - int(prod_val.group(1))) <= 1
        
        return rfp_voltage == product_voltage
    
    def _standards_match(self, rfp_standards: List[str], product_standards: List[str]) -> bool:
        """Check if any standard matches."""
        
        if not rfp_standards or not product_standards:
            return False
        
        # Check if any RFP standard is in product standards
        return any(std in product_standards for std in rfp_standards)
    
    def _generate_comparison_table(self, rfp_specs: Dict, top_3: List[Dict]) -> Dict:
        """
        Generate comparison table: RFP specs vs Top 1, 2, 3 OEM products.
        """
        
        table = {
            'rfp_requirements': rfp_specs,
            'oem_products': []
        }
        
        for i, rec in enumerate(top_3, 1):
            product = rec['product']
            table['oem_products'].append({
                'rank': i,
                'sku': product['sku'],
                'name': product['name'],
                'match_score': f"{rec['match_score']}%",
                'specs': product['specs']
            })
        
        return table
        
    def _generate_final_selection(self, products: List[Dict]) -> List[Dict]:
        """Generate final table of selected OEM products for all scope items."""
        
        final_table = []
        
        for product_result in products:
            if product_result.get('selected_product'):
                final_table.append({
                    'item_no': product_result['item_no'],
                    'description': product_result['description'],
                    'selected_sku': product_result['selected_product']['sku'],
                    'selected_product': product_result['selected_product']['name'],
                    'match_score': f"{product_result['selected_product']['match_score']}%"
                })
        
        return final_table
    
    def _generate_compliance_items(self, rfp_specs: Dict, product: Dict) -> List[Dict]:
        items: List[Dict] = []
        if not product:
            return items
        p_specs = product.get('specs', {})
        raw = product.get('raw_text') or ''
        params = ['voltage', 'cable_type', 'conductor_material', 'insulation_type', 'armoring', 'cores', 'standards']
        for k in params:
            rv = rfp_specs.get(k)
            pv = p_specs.get(k)
            status = 'Pass' if rv and pv and (rv == pv or (isinstance(rv, list) and any(x in (pv or []) for x in rv))) else 'Gap'
            ev = ''
            try:
                if raw:
                    for line in raw.splitlines():
                        if isinstance(rv, str) and rv and rv.lower() in line.lower():
                            ev = line.strip()
                            break
                        if isinstance(pv, str) and pv and pv.lower() in line.lower():
                            ev = line.strip()
                            break
            except Exception:
                pass
            items.append({'parameter': k, 'rfp': rv, 'offered': pv, 'status': status, 'evidence': ev})
        return items
    
    def _load_product_catalog(self) -> List[Dict]:
        """Load OEM product catalog from markdown datasheets, with fallback variants."""
        import re
        from pathlib import Path

        catalog: List[Dict] = []
        ds_dir = Path('data/oem_datasheets')
        files = list(ds_dir.glob('*.md')) if ds_dir.exists() else []

        def parse_md(p: Path) -> Dict:
            text = p.read_text(encoding='utf-8')
            def find(pattern, default=''):
                m = re.search(pattern, text, re.IGNORECASE)
                if not m:
                    return default
                # If there is a capturing group, return group(1); otherwise full match
                try:
                    return (m.group(1) if m.lastindex else m.group(0)).strip()
                except IndexError:
                    return m.group(0).strip()

            sku = find(r'Product\s*Code\s*[:：]\s*([A-Z0-9\-]+)') or find(r'\*\*Product Code\*\*:\s*([A-Z0-9\-]+)')
            product_line = find(r'###\s*Product:\s*(.+)')
            manufacturer = find(r'^#\s*([A-Z][A-Za-z\s&]+)$', default=p.stem.split('_')[0]).title()

            # Specs
            voltage = find(r'Rated Voltage.*?([0-9]{1,3}\s*/?\s*(?:[0-9]{1,3}\s*/)?\s*(\d{1,3})\s*kV)', default=find(r'33\s*kV|11\s*kV|22\s*kV'))
            if '/' in voltage:
                # pick system voltage (second number)
                try:
                    voltage = re.search(r'/\s*(\d{1,3})\s*kV', voltage, re.IGNORECASE).group(1) + ' kV'
                except Exception:
                    voltage = re.sub(r'.*?([0-9]{1,3})\s*kV.*', r'\1 kV', voltage)
            elif not voltage:
                voltage = find(r'(\d{1,3})\s*kV', default='') + (' kV' if find(r'(\d{1,3})\s*kV') else '')

            cores = find(r'Number of Cores\s*[:：]\s*([0-9]+\s*-?core)') or find(r'\b(3-core|4-core)\b')
            conductor_size = find(r'(\d+\s*sq\.mm)')
            conductor_material = 'Aluminum' if re.search(r'Aluminum|Aluminium', text, re.IGNORECASE) else 'Copper'
            insulation_type = 'XLPE' if re.search(r'XLPE', text, re.IGNORECASE) else ('PVC' if re.search(r'\bPVC\b', text, re.IGNORECASE) else 'XLPE')
            armoring = 'Armored' if re.search(r'Armou?r', text, re.IGNORECASE) else 'Unarmored'
            cable_type = 'XLPE' if 'XLPE' in insulation_type else insulation_type

            standards = []
            if re.search(r'IS\s*7098', text, re.IGNORECASE):
                standards.append('IS 7098')
            if re.search(r'IEC\s*60502', text, re.IGNORECASE):
                standards.append('IEC 60502')
            if re.search(r'IS\s*1554', text, re.IGNORECASE):
                standards.append('IS 1554')

            price = 0
            pm = re.search(r'List Price\s*[:：]\s*Rs\s*([\d,]+)', text, re.IGNORECASE)
            if pm:
                price = float(pm.group(1).replace(',', ''))

            name = product_line or f"{voltage} {cable_type} {cores or ''} {conductor_size or ''}".strip()
            return {
                'sku': sku or f"SKU-{abs(hash(p.name)) % 100000}",
                'name': name,
                'manufacturer': manufacturer.strip(),
                'specs': {
                    'voltage': voltage or 'Unknown',
                    'cable_type': cable_type or 'XLPE',
                    'conductor_material': conductor_material,
                    'insulation_type': insulation_type,
                    'armoring': armoring,
                    'cores': cores or '3-core',
                    'conductor_size': conductor_size or '',
                    'standards': standards or ['IS 7098']
                },
                'price_per_meter': price or 0,
                'raw_text': text
            }

        # Parse all datasheets
        for f in files:
            try:
                catalog.append(parse_md(f))
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed parsing datasheet {f}: {e}")

        # Fallback variants to ensure coverage (33kV 150/185, 22kV 95/120, AL 120)
        fallback_variants = [
            # 11kV Variants (Common for Distribution)
            {
                'sku': 'OEM-XLPE-11KV-3C-185', 'name': '11kV XLPE 3C 185 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '11 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '185 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 850
            },
            {
                'sku': 'OEM-XLPE-11KV-3C-300', 'name': '11kV XLPE 3C 300 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '11 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '300 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1250
            },
            {
                'sku': 'OEM-XLPE-11KV-3C-240', 'name': '11kV XLPE 3C 240 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '11 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '240 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1050
            },
            
            # 33kV Variants
            {
                'sku': 'OEM-XLPE-33KV-3C-150', 'name': '33kV XLPE 3C 150 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '33 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '150 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1650
            },
            {
                'sku': 'OEM-XLPE-33KV-3C-185', 'name': '33kV XLPE 3C 185 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '33 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '185 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1850
            },
            {
                'sku': 'AL-XLPE-33KV-3C-120', 'name': '33kV XLPE 3C 120 sq.mm (Aluminum)', 'manufacturer': 'Polycab',
                'specs': {'voltage': '33 kV','cable_type': 'XLPE','conductor_material': 'Aluminum','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '120 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1100
            },
            # 22kV Variants
            {
                'sku': 'OEM-XLPE-22KV-3C-95', 'name': '22kV XLPE 3C 95 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '22 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '95 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1150
            },
            {
                'sku': 'OEM-XLPE-22KV-3C-120', 'name': '22kV XLPE 3C 120 sq.mm', 'manufacturer': 'Polycab',
                'specs': {'voltage': '22 kV','cable_type': 'XLPE','conductor_material': 'Copper','insulation_type': 'XLPE','armoring': 'Armored','cores': '3-core','conductor_size': '120 sq.mm','standards': ['IS 7098','IEC 60502']},
                'price_per_meter': 1250
            }
        ]

        # Merge, keeping existing SKUs unique
        existing_skus = {p['sku'] for p in catalog}
        for v in fallback_variants:
            if v['sku'] not in existing_skus:
                catalog.append(v)

        # Ensure at least one LV control cable exists (from previous defaults)
        if not any('440V' in p['specs'].get('voltage','') for p in catalog):
            catalog.append({
                'sku': 'OEM-PVC-440V-3C-16',
                'name': '440V PVC Control Cable 3-Core 16 sq.mm',
                'manufacturer': 'Generic',
                'specs': {
                    'voltage': '440V', 'cable_type': 'PVC', 'conductor_material': 'Copper',
                    'insulation_type': 'PVC', 'armoring': 'Unarmored', 'cores': '3-core',
                    'conductor_size': '16 sq.mm', 'standards': ['IS 1554']
                },
                'price_per_meter': 120
            })

        return catalog

import logging
from typing import List, Dict
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class PricingAgentEnhanced:
    """
    Pricing Agent: Receives test requirements from main agent and product recommendations from technical agent.
    Assigns unit prices from pricing table and test prices from services table.
    
    Pricing sources (in priority order):
    1) CSV sheets under data/pricing/*.csv (flexible headers)
    2) JSON sheets under data/pricing/*.json (key->value)
    3) Built-in defaults
    """
    
    def __init__(self):
        # Load pricing tables
        self.product_pricing = self._load_product_pricing()
        self.test_pricing = self._load_test_pricing()
        self.policy = self._load_policy()
        self.market_costs = self._load_market_costs()
    
    def process_pricing(self, test_requirements: List[str], product_recommendations: List[Dict], context: Dict = None) -> Dict:
        """
        Main processing: Receives test requirements and product recommendations.
        Returns consolidated material + services pricing, with overheads and final quote.
        Supports dynamic overhead/margin adjustment via context:
        - context = { 'estimated_value': float, 'organization': str }
        """
        
        logger.info("Pricing Agent: Processing pricing request")
        logger.info(f"  - Test requirements: {len(test_requirements)}")
        logger.info(f"  - Products to price: {len(product_recommendations)}")
        
        results = {
            'products': [],
            'tests': [],
            'total_material_cost': 0,
            'total_services_cost': 0,
            'grand_total': 0
        }
        
        # Price each product
        for product in product_recommendations:
            product_cost = self._price_product(product)
            results['products'].append(product_cost)
            results['total_material_cost'] += product_cost['total_cost']
        
        # Price each test
        for test_req in test_requirements:
            test_cost = self._price_test(test_req)
            results['tests'].append(test_cost)
            results['total_services_cost'] += test_cost['cost']
        
        results['grand_total'] = results['total_material_cost'] + results['total_services_cost']
        
        # Dynamic overheads/margin
        base_overheads = self.policy.get('overheads', {})
        dynamic = self._compute_dynamic_overheads(base_overheads, results, context or {})

        # Optional: small margin optimizer to hit a target competitiveness ratio
        optimized = self._maybe_optimize_margin(dynamic, results, context or {})
        if optimized:
            dynamic = optimized
        
        transport = round(results['grand_total'] * dynamic.get('transport_pct', 0.0))
        install_support = round(results['grand_total'] * dynamic.get('installation_support_pct', 0.0))
        contingency = round(results['grand_total'] * dynamic.get('contingency_pct', 0.0))
        subtotal = results['grand_total'] + transport + install_support + contingency
        profit_margin_val = round(subtotal * dynamic.get('profit_margin_pct', 0.0))
        taxable = subtotal + profit_margin_val
        gst = round(taxable * dynamic.get('gst_pct', 0.0))
        final_quote = taxable + gst
        
        results['breakdown'] = {
            'transport_cost': transport,
            'installation_support': install_support,
            'contingency': contingency,
            'profit_margin': profit_margin_val,
            'gst': gst,
            'applied_pcts': {
                'transport_pct': dynamic.get('transport_pct'),
                'installation_support_pct': dynamic.get('installation_support_pct'),
                'contingency_pct': dynamic.get('contingency_pct'),
                'profit_margin_pct': dynamic.get('profit_margin_pct'),
                'gst_pct': dynamic.get('gst_pct')
            }
        }
        results['final_quote'] = final_quote
        
        logger.info(f"Pricing complete: Material={results['total_material_cost']}, Services={results['total_services_cost']}, FinalQuote={final_quote}")
        
        return results
    
    def _price_product(self, product: Dict) -> Dict:
        """Assign unit price to product from pricing table (with optional market adjustment)."""
        
        sku = product.get('selected_sku') or product.get('sku')
        quantity = product.get('quantity', 1)
        
        # Look up price in table
        unit_price = self.product_pricing.get(sku, 850)  # Default price
        
        # Market-linked adjustment (optional, based on conductor material in description)
        desc = (product.get('description') or '').lower()
        if 'copper' in desc and self.market_costs:
            unit_price = round(unit_price * float(self.market_costs.get('copper_multiplier', 1.0)))
        elif 'aluminum' in desc or 'aluminium' in desc:
            unit_price = round(unit_price * float(self.market_costs.get('aluminum_multiplier', 1.0)))
        
        # Calculate total
        total_cost = unit_price * quantity * 1000  # Convert km to meters
        
        return {
            'item_no': product.get('item_no'),
            'sku': sku,
            'description': product.get('description') or product.get('selected_product'),
            'quantity': quantity,
            'unit': 'km',
            'unit_price': unit_price,
            'total_cost': total_cost
        }
    
    def _price_test(self, test_requirement: str) -> Dict:
        """Assign price to test from services pricing table."""
        
        # Match test requirement to pricing table
        test_name = test_requirement
        test_cost = 5000  # Default
        
        # Look for matching test in pricing table
        for test_key, price in self.test_pricing.items():
            if test_key.lower() in test_requirement.lower():
                test_cost = price
                break
        
        return {
            'test_name': test_name,
            'cost': test_cost
        }
    
    def _load_product_pricing(self) -> Dict[str, float]:
        """Load product pricing table from CSV/JSON sheets or defaults.
        CSV support (data/pricing/product_prices.csv): expects columns for SKU and price.
        Header autodetect across: sku|SKU|product_sku|product|code and unit_price|price|rate|per_meter.
        JSON support (data/pricing/product_prices.json): { "SKU": price, ... }.
        """
        # Try CSV first
        try:
            import csv
            pcsv = Path(__file__).resolve().parent.parent / 'data' / 'pricing' / 'product_prices.csv'
            if pcsv.exists():
                with open(pcsv, 'r', encoding='utf-8') as f:
                    r = csv.DictReader(f)
                    rows = list(r)
                    if rows:
                        sku_keys = ['sku','SKU','product_sku','product','code']
                        price_keys = ['unit_price','price','rate','per_meter']
                        pricing: Dict[str, float] = {}
                        for row in rows:
                            sku = next((row[k] for k in sku_keys if k in row and row[k]), None)
                            price = next((row[k] for k in price_keys if k in row and row[k] not in (None,'')), None)
                            if not sku or price is None:
                                continue
                            try:
                                pricing[str(sku).strip()] = float(str(price).replace(',','').strip())
                            except Exception:
                                continue
                        if pricing:
                            return pricing
        except Exception:
            pass
        # Try JSON next
        try:
            p = Path(__file__).resolve().parent.parent / 'data' / 'pricing' / 'product_prices.json'
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return {str(k): float(v) for k, v in data.items()}
        except Exception:
            pass
        # Defaults
        return {
            # 11kV SKUs
            'OEM-XLPE-11KV-3C-35': 850,
            'OEM-XLPE-11KV-3C-50': 920,
            'OEM-XLPE-11KV-4C-35': 980,
            'KEI-XLPE-11KV-3C-35': 880,
            # 22kV SKUs
            'OEM-XLPE-22KV-3C-95': 1150,
            'OEM-XLPE-22KV-3C-120': 1250,
            # 33kV SKUs
            'OEM-XLPE-33KV-3C-120': 1450,
            'OEM-XLPE-33KV-3C-150': 1650,
            'OEM-XLPE-33KV-3C-185': 1850,
            'HAVELLS-33KV-3C-120': 1480,
            'AL-XLPE-33KV-3C-120': 1100,
            # LV SKUs
            'OEM-PVC-440V-3C-16': 120,
            # Default pricing
            'DEFAULT': 850
        }
    
    def _load_test_pricing(self) -> Dict[str, float]:
        """Load test pricing from CSV/JSON or defaults.
        CSV (data/pricing/test_prices.csv): columns test|name|test_name and price|cost|rate.
        JSON (data/pricing/test_prices.json): { "routine": 6000, ... }.
        """
        # CSV first
        try:
            import csv
            pcsv = Path(__file__).resolve().parent.parent / 'data' / 'pricing' / 'test_prices.csv'
            if pcsv.exists():
                with open(pcsv, 'r', encoding='utf-8') as f:
                    r = csv.DictReader(f)
                    rows = list(r)
                    if rows:
                        name_keys = ['test','name','test_name']
                        price_keys = ['price','cost','rate']
                        out: Dict[str, float] = {}
                        for row in rows:
                            name = next((row[k] for k in name_keys if k in row and row[k]), None)
                            price = next((row[k] for k in price_keys if k in row and row[k] not in (None,'')), None)
                            if not name or price is None:
                                continue
                            try:
                                out[str(name).strip()] = float(str(price).replace(',','').strip())
                            except Exception:
                                continue
                        if out:
                            return out
        except Exception:
            pass
        # JSON next
        try:
            p = Path(__file__).resolve().parent.parent / 'data' / 'pricing' / 'test_prices.json'
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and data:
                        return {str(k): float(v) for k, v in data.items()}
        except Exception:
            pass
        return {
            'routine': 5000,
            'type test': 15000,
            'voltage': 8000,
            'resistance': 3000,
            'insulation': 3500,
            'discharge': 12000,
            'visual': 2000,
            'mechanical': 6000,
            'standard': 5000
        }
    
    def _load_policy(self) -> Dict:
        """Load client policy with overhead percentages."""
        try:
            p = Path(__file__).resolve().parent.parent / 'config' / 'client_policy.json'
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'overheads': {'transport_pct': 0.05, 'installation_support_pct': 0.03, 'contingency_pct': 0.02, 'profit_margin_pct': 0.1, 'gst_pct': 0.18}}
    
    def _load_market_costs(self) -> Dict:
        try:
            p = Path(__file__).resolve().parent.parent / 'data' / 'feeds' / 'market_costs.json'
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _compute_dynamic_overheads(self, base: Dict, results: Dict, context: Dict) -> Dict:
        """Adjust overheads/margins based on estimated value, organization, and competitiveness.
        Pulls tuning parameters from config/client_policy.json.dynamic_overheads when available.
        """
        est_val = float(context.get('estimated_value') or 0)
        org = (context.get('organization') or '').lower()
        grand = float(results.get('grand_total') or 0)
        ratio = (grand / est_val) if est_val > 0 else None
        # Start with base
        out = dict(base)
        pm = out.get('profit_margin_pct', 0.10)
        cont = out.get('contingency_pct', 0.02)
        # Load dynamic knobs
        dyn = (self.policy or {}).get('dynamic_overheads', {})
        large_cap = float(dyn.get('large_tender_margin_cap', 0.08))
        large_cont_cap = float(dyn.get('large_tender_contingency_cap', 0.015))
        mid_cap = float(dyn.get('mid_tender_margin_cap', 0.09))
        pm_min = float(dyn.get('profit_margin_min', 0.04))
        pm_max = float(dyn.get('profit_margin_max', 0.18))
        cont_min = float(dyn.get('contingency_min', 0.0))
        cont_max = float(dyn.get('contingency_max', 0.03))
        strat_accounts = [s.lower() for s in dyn.get('strategic_accounts', ['powergrid','pgcil','ntpc','railway','ireps'])]
        strat_delta = float(dyn.get('strategic_margin_delta', -0.01))
        sharpen_thresh = float(dyn.get('high_ratio_sharpen_threshold', 1.2))
        sharpen_delta = float(dyn.get('high_ratio_margin_delta', -0.02))
        # Tier by estimated value (lower margins on larger projects)
        if est_val >= 100_000_000:      # >= 10 Cr
            pm = min(pm, large_cap)
            cont = min(cont, large_cont_cap)
        elif est_val >= 50_000_000:     # >= 5 Cr
            pm = min(pm, mid_cap)
        else:
            pm = max(pm, out.get('profit_margin_pct', 0.10))
        # Strategic accounts (slightly sharper)
        if any(k in org for k in strat_accounts):
            pm = max(pm + strat_delta, pm_min)
        # If quote far above estimate, try to sharpen the margin further
        if ratio and ratio > sharpen_thresh:
            pm = max(pm + sharpen_delta, pm_min)
        # Clamp
        pm = max(pm_min, min(pm, pm_max))
        cont = max(cont_min, min(cont, cont_max))
        out['profit_margin_pct'] = pm
        out['contingency_pct'] = cont
        return out
    
    def _maybe_optimize_margin(self, dynamic: Dict, results: Dict, context: Dict) -> Dict:
        """If ENABLE_MARGIN_OPT is set, grid search margin to approach a target ratio."""
        import os
        if os.getenv('ENABLE_MARGIN_OPT', 'false').lower() not in ('1','true','yes'):
            return {}
        est_val = float(context.get('estimated_value') or 0)
        if est_val <= 0:
            return {}
        dyn = (self.policy or {}).get('dynamic_overheads', {})
        target = float(dyn.get('target_competitiveness_ratio', 1.10))
        pm_min = float(dyn.get('profit_margin_min', 0.04))
        pm_max = float(dyn.get('profit_margin_max', 0.18))
        best = None
        # Compute non-margin subtotal base
        transport = results['grand_total'] * dynamic.get('transport_pct', 0.0)
        install = results['grand_total'] * dynamic.get('installation_support_pct', 0.0)
        cont = results['grand_total'] * dynamic.get('contingency_pct', 0.0)
        base_subtotal = results['grand_total'] + transport + install + cont
        for pm in [pm_min + i*0.005 for i in range(int((pm_max-pm_min)/0.005)+1)]:
            taxable = base_subtotal * (1 + pm)
            quoted = taxable * (1 + dynamic.get('gst_pct', 0.18))
            ratio = quoted / est_val
            score = abs(ratio - target)
            if (best is None) or (score < best[0]):
                best = (score, pm)
        if best is None:
            return {}
        opt = dict(dynamic)
        opt['profit_margin_pct'] = best[1]
        opt['optimizer'] = {'target_ratio': target, 'chosen_margin_pct': best[1]}
        return opt
    
    def generate_consolidated_table(self, pricing_results: Dict) -> Dict:
        """Generate consolidated price table with material + services for each product."""
        
        consolidated = []
        
        for product in pricing_results['products']:
            # Calculate proportional test costs for this product
            product_ratio = product['total_cost'] / pricing_results['total_material_cost'] if pricing_results['total_material_cost'] > 0 else 1
            product_test_cost = pricing_results['total_services_cost'] * product_ratio
            
            consolidated.append({
                'item_no': product['item_no'],
                'sku': product['sku'],
                'description': product['description'],
                'material_cost': product['total_cost'],
                'services_cost': product_test_cost,
                'total_cost': product['total_cost'] + product_test_cost
            })
        
        return {
            'line_items': consolidated,
            'summary': {
                'total_material': pricing_results['total_material_cost'],
                'total_services': pricing_results['total_services_cost'],
                'grand_total': pricing_results['grand_total']
            }
        }

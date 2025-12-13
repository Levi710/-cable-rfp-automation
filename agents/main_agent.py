import logging
from typing import Dict, List
from agents.sales_agent import SalesAgent
from agents.technical_agent_enhanced import TechnicalAgentEnhanced
from agents.pricing_agent_enhanced import PricingAgentEnhanced
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class MainAgent:
    """
    Main Agent: Hub-and-spoke coordinator for RFP processing.
    
    Architecture:
        Sales Agent → Main Agent → Technical Agent
                           ↓              ↓
                     Pricing Agent ← Main Agent
                           ↓
                     Main Agent → Final Decision
    
    Responsibilities:
    - Receives selected RFP from Sales Agent
    - Routes RFP summary to Technical Agent
    - Routes test requirements to Pricing Agent
    - Routes product recommendations to Pricing Agent
    - Collects all responses and makes final decision
    """
    
    def __init__(self):
        self.sales_agent = SalesAgent()
        self.technical_agent = TechnicalAgentEnhanced()
        self.pricing_agent = PricingAgentEnhanced()
        self.policy = self._load_policy()
    
    async def process_tenders(self, discovered_tenders: List[Dict]) -> Dict:
        """
        Complete workflow: Process discovered tenders through all agents.
        
        Returns:
            Complete processing results with final recommendation
        """
        
        print("\n" + "="*80)
        print("MAIN AGENT: COORDINATING RFP PROCESSING")
        print("="*80)
        
        # STEP 1: Sales Agent - Filter, Summarize, Select
        print("\n" + "-"*80)
        print("STEP 1: SALES AGENT - RFP IDENTIFICATION & SELECTION")
        print("-"*80)
        
        sales_result = self.sales_agent.process_rfps(discovered_tenders)
        
        if sales_result['status'] != 'success':
            print(f"\nSTATUS: {sales_result['message']}")
            return {
                'status': 'no_rfp_selected',
                'message': sales_result['message'],
                'recommendation': 'NO-BID'
            }
        
        selected_rfp = sales_result['selected_rfp']
        rfp_summary = sales_result['rfp_summary']
        
        print(f"\nSelected RFP: {rfp_summary['tender_id']}")
        print(f"  Title: {rfp_summary['title']}")
        print(f"  Organization: {rfp_summary['organization']}")
        print(f"  Estimated Value: Rs {rfp_summary['estimated_value']:,}")
        print(f"  Deadline: {rfp_summary['deadline']}")
        print(f"  Days until due: {rfp_summary['days_until_due']}")
        print(f"\nFiltering Summary:")
        print(f"  Total tenders: {sales_result['total_tenders']}")
        print(f"  Filtered (next 3 months): {sales_result['filtered_count']}")
        print(f"  Qualified (cable-related): {sales_result['qualified_count']}")
        
        # STEP 2: Main Agent prepares contextual summary for Technical Agent
        print("\n" + "-"*80)
        print("STEP 2: MAIN AGENT - PREPARING TECHNICAL SUMMARY")
        print("-"*80)
        print("Main Agent → Preparing contextual summary for Technical Agent...")
        
        # Prepare Technical Agent summary (focused on specifications)
        technical_summary = self._prepare_technical_summary(rfp_summary)
        
        print("\nTechnical Summary (contextual to Technical Agent role):")
        print(f"  Tender ID: {technical_summary['tender_id']}")
        print(f"  Scope Items: {len(technical_summary['scope_of_supply'])}")
        print(f"  Key Specs: {technical_summary['product_requirements']}")
        
        print("\n" + "-"*80)
        print("STEP 3: TECHNICAL AGENT - PRODUCT MATCHING & COMPARISON")
        print("-"*80)
        print("Main Agent → Sending technical summary to Technical Agent...")
        
        technical_result = self.technical_agent.process_rfp(technical_summary)
        
        # Check for new SKU requests based on match threshold
        new_sku_requests = self._generate_new_sku_requests(rfp_summary['tender_id'], technical_result)
        if new_sku_requests:
            print(f"\nENGINEERING ACTION: {len(new_sku_requests)} New SKU request(s) generated (see output/new_sku_requests)")
        
        print(f"\nScope of Supply:")
        print(technical_result['scope_summary'])
        
        # Display comparison tables
        for product_result in technical_result['products']:
            print(f"\n--- Item {product_result['item_no']}: {product_result['description']} ---")
            print(f"\nRFP Requirements:")
            for key, value in product_result['rfp_specs'].items():
                print(f"  {key}: {value}")
            
            print(f"\nTop 3 OEM Recommendations:")
            for rec in product_result['top_3_recommendations']:
                print(f"\n  {rec['rank']}. {rec['name']} (SKU: {rec['sku']})")
                print(f"     Match Score: {rec['match_score']}%")
            
            print(f"\nSelected Product:")
            if product_result['selected_product']:
                print(f"  SKU: {product_result['selected_product']['sku']}")
                print(f"  Name: {product_result['selected_product']['name']}")
                print(f"  Match: {product_result['selected_product']['match_score']}%")
        
        # STEP 4: Main Agent prepares contextual summary for Pricing Agent
        print("\n" + "-"*80)
        print("STEP 4: MAIN AGENT - PREPARING PRICING SUMMARY")
        print("-"*80)
        print("Main Agent → Preparing contextual summary for Pricing Agent...")
        
        # Prepare Pricing Agent summary (focused on costs and quantities)
        pricing_summary = self._prepare_pricing_summary(rfp_summary, technical_result)
        
        print("\nPricing Summary (contextual to Pricing Agent role):")
        print(f"  Test Requirements: {len(pricing_summary['test_requirements'])} items")
        print(f"  Product Recommendations: {len(pricing_summary['product_recommendations'])} items")
        print(f"  Tender Value: Rs {rfp_summary['estimated_value']:,.0f}")
        
        print("\n" + "-"*80)
        print("STEP 5: PRICING AGENT - QUOTE GENERATION")
        print("-"*80)
        print("Main Agent → Sending pricing summary to Pricing Agent...")
        
        test_requirements = pricing_summary['test_requirements']
        final_selection = pricing_summary['product_recommendations']
        
        # Add quantity info to products for pricing
        for product in final_selection:
            for scope_item in rfp_summary['scope_of_supply']:
                if product['item_no'] == scope_item['item_no']:
                    product['quantity'] = scope_item['quantity']
                    break
        
        pricing_result = self.pricing_agent.process_pricing(
            test_requirements=test_requirements,
            product_recommendations=final_selection,
            context={
                'estimated_value': rfp_summary.get('estimated_value', 0),
                'organization': rfp_summary.get('organization', '')
            }
        )
        
        consolidated_table = self.pricing_agent.generate_consolidated_table(pricing_result)
        
        print(f"\nTest Requirements ({len(test_requirements)} items):")
        for i, test in enumerate(test_requirements[:5], 1):  # Show first 5
            print(f"  {i}. {test}")
        if len(test_requirements) > 5:
            print(f"  ... and {len(test_requirements) - 5} more")
        
        print(f"\nPricing Summary:")
        print(f"  Total Material Cost: Rs {pricing_result['total_material_cost']:,.0f}")
        print(f"  Total Services Cost: Rs {pricing_result['total_services_cost']:,.0f}")
        print(f"  Grand Total (Direct): Rs {pricing_result['grand_total']:,.0f}")
        if pricing_result.get('breakdown'):
            b = pricing_result['breakdown']
            print(f"  Transport: Rs {b.get('transport_cost', 0):,}")
            print(f"  Installation Support: Rs {b.get('installation_support', 0):,}")
            print(f"  Contingency: Rs {b.get('contingency', 0):,}")
            print(f"  Profit Margin: Rs {b.get('profit_margin', 0):,}")
            print(f"  GST: Rs {b.get('gst', 0):,}")
            print(f"  Final Quote: Rs {pricing_result.get('final_quote', pricing_result['grand_total']):,}")
        
        # STEP 6: Main Agent - Consolidate responses and make final decision
        print("\n" + "-"*80)
        print("STEP 6: MAIN AGENT - CONSOLIDATING RESPONSES & FINAL DECISION")
        print("-"*80)
        print("Main Agent → Consolidating Technical and Pricing Agent responses...")
        
        # Create consolidated overall response
        overall_response = self._consolidate_responses(
            rfp_summary=rfp_summary,
            technical_result=technical_result,
            pricing_result=pricing_result
        )
        
        print("\nConsolidated Overall Response:")
        print(f"  OEM Products Suggested: {len(overall_response['oem_products'])} SKUs")
        for p in overall_response['oem_products']:
            print(f"    - {p['sku']}: Rs {p['unit_price']}/m (Match: {p['match_score']}%)")
        print(f"  Tests Required: {len(overall_response['tests_required'])} items")
        for i, t in enumerate(overall_response['tests_required'][:3], 1):
            print(f"    {i}. {t['test_name']}: Rs {t['cost']:,.0f}")
        if len(overall_response['tests_required']) > 3:
            print(f"    ... and {len(overall_response['tests_required']) - 3} more")
        print(f"  Total Quote: Rs {overall_response['grand_total']:,.0f}")
        
        print("\n" + "-"*80)
        print("STEP 7: MAIN AGENT - FINAL DECISION")
        print("-"*80)
        
        # Calculate win probability
        estimated_value = rfp_summary['estimated_value']
        quoted_value = pricing_result.get('final_quote', pricing_result['grand_total'])
        
        win_probability = self._calculate_win_probability(
            estimated_value=estimated_value,
            quoted_value=quoted_value,
            match_scores=[p['selected_product']['match_score'] for p in technical_result['products'] if p.get('selected_product')],
            days_until_due=rfp_summary['days_until_due']
        )
        
        recommendation = 'BID' if win_probability > 50 and quoted_value > 0 else 'NO-BID'
        
        print(f"\nDecision Analysis:")
        print(f"  Estimated Value: Rs {estimated_value:,.0f}")
        print(f"  Our Quote: Rs {quoted_value:,.0f}")
        if estimated_value and estimated_value > 0:
            competitiveness_pct = (quoted_value / estimated_value) * 100.0
            print(f"  Quote Competitiveness: {competitiveness_pct:.1f}% of estimate")
        else:
            print("  Quote Competitiveness: n/a (no estimate)")
        print(f"  Average Match Score: {sum(p['selected_product']['match_score'] for p in technical_result['products'] if p.get('selected_product'))/len(technical_result['products']):.1f}%")
        print(f"  Win Probability: {win_probability:.1f}%")
        print(f"\n  FINAL RECOMMENDATION: {recommendation}")
        
        print("\n" + "="*80)
        print(f"MAIN AGENT: PROCESSING COMPLETE - {recommendation}")
        print("="*80)
        
        return {
            'status': 'success',
            'recommendation': recommendation,
            'selected_rfp': {
                'tender_id': rfp_summary['tender_id'],
                'title': rfp_summary['title'],
                'organization': rfp_summary['organization'],
                'deadline': rfp_summary['deadline'],
                'estimated_value': estimated_value
            },
            'engineering_action_required': bool(new_sku_requests),
            'sales_agent_output': {
                'rfp_summary': rfp_summary,
                'filtering_stats': {
                    'total': sales_result['total_tenders'],
                    'filtered': sales_result['filtered_count'],
                    'qualified': sales_result['qualified_count']
                }
            },
            'technical_agent_output': {
                'scope_summary': technical_result['scope_summary'],
                'products': technical_result['products'],
                'final_selection': final_selection
            },
            'pricing_agent_output': {
                'pricing_details': pricing_result,
                'consolidated_table': consolidated_table
            },
            'overall_response': overall_response,  # Consolidated response with SKUs, prices, and tests
            'new_sku_requests': new_sku_requests,
            'decision': {
                'recommendation': recommendation,
                'win_probability': win_probability,
                'quoted_value': quoted_value,
                'estimated_value': estimated_value
            }
        }
    
    def _calculate_win_probability(self, estimated_value: float, quoted_value: float,
                                    match_scores: List[float], days_until_due: int) -> float:
        """Calculate win probability based on multiple factors."""
        
        base_probability = 50.0
        
        # Factor 1: Price competitiveness (±20%)
        if estimated_value > 0:
            price_ratio = quoted_value / estimated_value
            if 0.85 <= price_ratio <= 1.05:  # Within 15% below to 5% above
                base_probability += 20
            elif 1.05 < price_ratio <= 1.15:
                base_probability += 10
            elif price_ratio < 0.85:
                base_probability += 5  # Too low might seem suspicious
            else:
                base_probability -= 10
        
        # Factor 2: Technical match quality (±15%)
        if match_scores:
            avg_match = sum(match_scores) / len(match_scores)
            if avg_match >= 90:
                base_probability += 15
            elif avg_match >= 80:
                base_probability += 10
            elif avg_match >= 70:
                base_probability += 5
            else:
                base_probability -= 5
        
        # Factor 3: Time urgency (±10%)
        if days_until_due:
            if days_until_due < 30:
                base_probability += 10  # Less competition on urgent tenders
            elif days_until_due > 60:
                base_probability -= 5  # More competition on distant tenders
        
        return min(max(base_probability, 0), 100)  # Clamp between 0-100
    
    def _prepare_technical_summary(self, rfp_summary: Dict) -> Dict:
        """
        Prepare contextual summary for Technical Agent.
        Focus: Product specifications, technical requirements, scope of supply.
        """
        return {
            'tender_id': rfp_summary['tender_id'],
            'title': rfp_summary['title'],
            'organization': rfp_summary['organization'],
            # Technical Agent needs: specs, scope, standards
            'product_requirements': rfp_summary['product_requirements'],
            'scope_of_supply': rfp_summary['scope_of_supply'],
            'voltage_class': rfp_summary.get('voltage_class'),
            'cable_type': rfp_summary.get('cable_type')
        }
    
    def _prepare_pricing_summary(self, rfp_summary: Dict, technical_result: Dict) -> Dict:
        """
        Prepare contextual summary for Pricing Agent.
        Focus: Test requirements, product recommendations with quantities, tender value.
        """
        # Get product recommendations with quantities
        final_selection = technical_result['final_selection_table']
        
        # Add quantity info to products
        for product in final_selection:
            for scope_item in rfp_summary['scope_of_supply']:
                if product['item_no'] == scope_item['item_no']:
                    product['quantity'] = scope_item['quantity']
                    break
        
        return {
            'tender_id': rfp_summary['tender_id'],
            'estimated_value': rfp_summary['estimated_value'],
            'organization': rfp_summary.get('organization'),
            # Pricing Agent needs: test requirements and product recommendations
            'test_requirements': rfp_summary['test_requirements'],
            'product_recommendations': final_selection
        }
    
    def _consolidate_responses(self, rfp_summary: Dict, technical_result: Dict, 
                               pricing_result: Dict) -> Dict:
        """
        Consolidate responses from Technical and Pricing agents.
        Overall response contains: OEM product SKUs, their prices, and test costs.
        """
        # Extract OEM products with SKUs and prices
        oem_products = []
        for product in pricing_result['products']:
            # Find matching technical result for match score
            match_score = 0
            for tech_product in technical_result['products']:
                if tech_product['item_no'] == product['item_no']:
                    if tech_product.get('selected_product'):
                        match_score = tech_product['selected_product']['match_score']
                    break
            
            oem_products.append({
                'item_no': product['item_no'],
                'sku': product['sku'],
                'description': product['description'],
                'quantity': product['quantity'],
                'unit': product['unit'],
                'unit_price': product['unit_price'],
                'total_material_cost': product['total_cost'],
                'match_score': match_score
            })
        
        # Extract test costs
        tests_required = pricing_result['tests']
        
        # Summary
        return {
            'tender_id': rfp_summary['tender_id'],
            'tender_title': rfp_summary['title'],
            'oem_products': oem_products,
            'tests_required': tests_required,
            'total_material_cost': pricing_result['total_material_cost'],
            'total_services_cost': pricing_result['total_services_cost'],
            'grand_total': pricing_result['grand_total']
        }
    
    def _load_policy(self) -> Dict:
        """Load client policy JSON for thresholds and overheads."""
        try:
            p = Path(__file__).resolve().parent.parent / 'config' / 'client_policy.json'
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'thresholds': {'min_match_percent': 80}}
    
    def _generate_new_sku_requests(self, tender_id: str, technical_result: Dict) -> List[Dict]:
        """Generate new SKU request docs when match score is below threshold."""
        threshold = int(self.policy.get('thresholds', {}).get('min_match_percent', 80))
        requests: List[Dict] = []
        out_dir = Path('output') / 'new_sku_requests'
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for product in technical_result.get('products', []):
            selected = product.get('selected_product')
            if not selected:
                continue
            score = selected.get('match_score', 0)
            if score >= threshold:
                continue
            
            rfp_specs = product.get('rfp_specs', {})
            # Find closest product specs
            closest_specs = None
            for rec in product.get('top_3_recommendations', []):
                if rec.get('sku') == selected.get('sku'):
                    closest_specs = rec.get('specs', {})
                    break
            closest_specs = closest_specs or {}
            
            # Compute gaps
            gaps = []
            for key in ['voltage', 'cable_type', 'conductor_material', 'insulation_type', 'armoring', 'cores', 'standards']:
                rv = rfp_specs.get(key)
                pv = closest_specs.get(key)
                if rv and pv and rv != pv:
                    gaps.append({'parameter': key, 'rfp': rv, 'closest': pv})
            
            req = {
                'tender_id': tender_id,
                'item_no': product.get('item_no'),
                'rfp_description': product.get('description'),
                'closest_sku': selected.get('sku'),
                'closest_match_score': score,
                'rfp_specs': rfp_specs,
                'closest_specs': closest_specs,
                'gaps': gaps,
                'recommendation': 'Create made-to-order SKU aligned with RFP specs or request OEM deviation approval.'
            }
            requests.append(req)
            
            # Write file
            file_path = out_dir / f"REQUEST_{tender_id}_ITEM_{product.get('item_no')}.md"
            lines = [
                f"# New SKU Request - Tender {tender_id} | Item {product.get('item_no')}",
                "",
                f"Description: {product.get('description')}",
                f"Closest SKU: {selected.get('sku')} (Match: {score}%)",
                "",
                "## RFP Specs vs Closest Product",
                "",
                "| Parameter | RFP | Closest Product |",
                "|---|---|---|"
            ]
            for g in gaps:
                lines.append(f"| {g['parameter']} | {g['rfp']} | {g['closest']} |")
            if not gaps:
                lines.append("| All | Matching/Comparable | Matching/Comparable |")
            lines += [
                "",
                "## Recommendation",
                req['recommendation']
            ]
            file_path.write_text("\n".join(lines), encoding='utf-8')
        
        return requests

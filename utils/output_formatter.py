"""
Output formatter for comprehensive RFP display with pricing summaries.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

class RFPOutputFormatter:
    """Format RFP processing results for display."""
    
    @staticmethod
    def format_rfp_header(tender: Dict, index: int = 1) -> str:
        """Format RFP identification header."""
        tender_id = tender.get('tender_id', f'RFP-{index:03d}')
        title = tender.get('title', 'Untitled RFP')
        
        # Calculate deadline
        published = tender.get('published_date', datetime.now().strftime('%Y-%m-%d'))
        deadline = tender.get('deadline', (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        
        # Calculate days remaining
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d')
            days_remaining = (deadline_date - datetime.now()).days
        except:
            days_remaining = 30
        
        output = "\n" + "="*80 + "\n"
        output += f"RFP IDENTIFIER: {tender_id}\n"
        output += f"TITLE: {title}\n"
        output += f"ORGANIZATION: {tender.get('organization', 'N/A')}\n"
        output += f"LOCATION: {tender.get('location', 'N/A')}\n"
        output += f"DEADLINE: {deadline} ({days_remaining} days remaining)\n"
        output += "="*80 + "\n"
        
        return output
    
    @staticmethod
    def format_scope_of_supply(tender: Dict, specs: Dict) -> str:
        """Format scope of supply section."""
        output = "\nSCOPE OF SUPPLY:\n"
        output += "-" * 60 + "\n"
        
        cable_type = specs.get('cable_type', tender.get('cable_type', 'Unknown'))
        voltage = specs.get('voltage_class', tender.get('voltage_class', 'Unknown'))
        length = tender.get('length_km', tender.get('estimated_length_km', 0))
        quantity_m = int(length * 1000)
        
        output += f"• Cable Type: {cable_type}\n"
        output += f"• Voltage Class: {voltage}\n"
        output += f"• Quantity: {quantity_m:,} meters ({length:.2f} km)\n"
        
        # Specifications
        if 'conductor' in specs or 'insulation' in specs:
            output += f"\nSPECIFICATIONS:\n"
            if specs.get('conductor'):
                output += f"  - Conductor: {specs['conductor']}\n"
            if specs.get('insulation'):
                output += f"  - Insulation: {specs['insulation']}\n"
            if specs.get('armor'):
                output += f"  - Armor: {specs.get('armor')}\n"
            if specs.get('sheath'):
                output += f"  - Sheath: {specs.get('sheath')}\n"
        
        return output
    
    @staticmethod
    def format_technical_recommendations(matches: List[Dict], specs: Dict) -> str:
        """Format technical recommendations with match scores."""
        output = "\nTECHNICAL RECOMMENDATIONS SUMMARY:\n"
        output += "=" * 80 + "\n"
        
        if not matches:
            output += "No matching products found.\n"
            return output
        
        # Best match
        best_match = max(matches, key=lambda x: x.get('match_score', 0))
        output += f"\nBEST MATCH:\n"
        output += f"  Product: {best_match.get('name', best_match.get('sku', 'Unknown'))}\n"
        output += f"  SKU: {best_match.get('sku', 'N/A')}\n"
        output += f"  Match Score: {best_match.get('match_score', 0):.2%}\n"
        
        # All matches
        if len(matches) > 1:
            output += f"\nALL MATCHES (Sorted by Score):\n"
            output += "-" * 80 + "\n"
            sorted_matches = sorted(matches, key=lambda x: x.get('match_score', 0), reverse=True)
            
            for i, match in enumerate(sorted_matches[:5], 1):  # Top 5
                output += f"{i}. {match.get('name', match.get('sku', 'Unknown'))}\n"
                output += f"   SKU: {match.get('sku', 'N/A')}\n"
                output += f"   Match Score: {match.get('match_score', 0):.2%}\n"
                if i < len(sorted_matches[:5]):
                    output += "\n"
        
        # Specification matching details
        output += "\n" + "-" * 80 + "\n"
        output += "SPECIFICATION MATCH DETAILS:\n"
        output += f"  Required Voltage: {specs.get('voltage_class', 'N/A')}\n"
        output += f"  Required Cable Type: {specs.get('cable_type', 'N/A')}\n"
        if specs.get('conductor'):
            output += f"  Conductor: {specs.get('conductor')}\n"
        if specs.get('insulation'):
            output += f"  Insulation: {specs.get('insulation')}\n"
        
        return output
    
    @staticmethod
    def format_products_in_scope(line_items: List[Dict]) -> str:
        """Format products in scope section."""
        output = "\nPRODUCTS IN SCOPE:\n"
        output += "-" * 60 + "\n"
        
        for i, item in enumerate(line_items, 1):
            output += f"{i}. {item['product']}\n"
            output += f"   - SKU: {item.get('sku', 'N/A')}\n"
            output += f"   - Quantity: {item['quantity_m']:,} meters\n"
            output += f"   - Unit Price: Rs {item['unit_price']:,}/meter\n"
            output += f"   - Material Cost: Rs {item['material_cost']:,.0f}\n"
        
        return output
    
    @staticmethod
    def format_testing_requirements(line_items: List[Dict]) -> str:
        """Format testing requirements section."""
        output = "\nTESTING REQUIRED:\n"
        output += "-" * 60 + "\n"
        
        # Collect all unique tests
        all_tests = set()
        for item in line_items:
            all_tests.update(item.get('tests', []))
        
        for i, test in enumerate(sorted(all_tests), 1):
            output += f"{i}. {test}\n"
        
        # Add test costs
        total_test_cost = sum(item.get('test_cost', 0) for item in line_items)
        output += f"\nTotal Testing Cost: ₹{total_test_cost:,.0f}\n"
        
        return output
    
    @staticmethod
    def format_pricing_summary(quote: Dict) -> str:
        """Format detailed pricing summary table."""
        output = "\nPRICING SUMMARY:\n"
        output += "=" * 100 + "\n\n"
        
        line_items = quote.get('line_items', [])
        
        # Table header
        output += "| Product              | Qty (m)  | Unit (Rs) | Material Cost (Rs) | Tests | Test Cost (Rs) | Total (Rs)    |\n"
        output += "|----------------------|----------|-----------|--------------------| ------|----------------|---------------|\n"
        
        # Table rows
        for item in line_items:
            product = item['product'][:20].ljust(20)
            qty = f"{item['quantity_m']:,}".rjust(8)
            unit = f"{item['unit_price']:,}".rjust(9)
            material = f"{item['material_cost']:,.0f}".rjust(18)
            tests = str(item['test_count']).center(5)
            test_cost = f"{item['test_cost']:,}".rjust(14)
            total = f"{item['total']:,.0f}".rjust(13)
            
            output += f"| {product} | {qty} | {unit} | {material} | {tests} | {test_cost} | {total} |\n"
        
        output += "\n" + "-" * 100 + "\n"
        
        # Detailed cost breakdown
        output += "\nDETAILED COST BREAKDOWN:\n"
        output += "=" * 60 + "\n"
        
        subtotal_material = quote['material_cost']
        subtotal_testing = quote['test_cost']
        subtotal = subtotal_material + subtotal_testing
        
        output += f"\n1. DIRECT COSTS:\n"
        output += f"   Material Cost:                Rs {quote['material_cost']:>15,.0f}\n"
        output += f"   Testing Cost:                 Rs {quote['test_cost']:>15,.0f}\n"
        output += f"   {'-'*50}\n"
        output += f"   Subtotal (Direct):            Rs {subtotal:>15,.0f}\n"
        
        output += f"\n2. INDIRECT COSTS:\n"
        output += f"   Transport (5%):               Rs {quote.get('transport_cost', 0):>15,.0f}\n"
        output += f"   Installation Support (3%):    Rs {quote.get('installation_support', 0):>15,.0f}\n"
        output += f"   Contingency Buffer (2%):      Rs {quote.get('contingency', 0):>15,.0f}\n"
        
        subtotal_before_tax = subtotal + quote.get('transport_cost', 0) + quote.get('installation_support', 0) + quote.get('contingency', 0)
        
        output += f"   {'-'*50}\n"
        output += f"   Subtotal (Before Tax):        Rs {subtotal_before_tax:>15,.0f}\n"
        
        output += f"\n3. TAXES:\n"
        output += f"   GST @ 18%:                    Rs {quote.get('gst', 0):>15,.0f}\n"
        
        output += f"\n{'='*60}\n"
        output += f"TOTAL PROJECT COST:              Rs {quote['total_value']:>15,.0f}\n"
        output += f"{'='*60}\n"
        
        output += f"\nPROJECT DETAILS:\n"
        output += f"  Lead Time:           {quote.get('lead_time_days', 0)} days\n"
        output += f"  Warranty Period:     {quote.get('warranty_years', 10)} years\n"
        output += f"  Quote Valid Until:   {quote.get('valid_until', 'N/A')}\n"
        
        return output
    
    @staticmethod
    def format_evaluation_metrics(metrics: Dict) -> str:
        """Format evaluation metrics from FMCG guide."""
        output = "\nEVALUATION METRICS (FMCG Guide Compliant):\n"
        output += "=" * 80 + "\n"
        
        output += f"  Spec Match Accuracy:        {metrics.get('spec_match_accuracy', 0):>6.1f}% (Target: >90%)\n"
        output += f"  Price Competitiveness:      {metrics.get('price_competitiveness', 0):>6.1f}% (Target: >85%)\n"
        output += f"  Response Time:              {metrics.get('response_time_seconds', 0):>6.0f}s  (Target: <60s)\n"
        output += f"  Cost per Meter:             ₹{metrics.get('cost_per_meter', 0):>6,.2f}\n"
        output += f"  Lead Time:                  {metrics.get('lead_time_days', 0):>6}d  (Target: <60d)\n"
        output += f"  Price Variance:             {metrics.get('estimated_vs_actual_variance', 0):>6.1f}% (Target: <10%)\n"
        
        # Overall score
        avg_score = (
            metrics.get('spec_match_accuracy', 90) * 0.3 +
            metrics.get('price_competitiveness', 85) * 0.3 +
            (100 if metrics.get('response_time_seconds', 60) < 60 else 80) * 0.2 +
            (100 if metrics.get('lead_time_days', 45) < 60 else 85) * 0.2
        )
        
        output += "\n" + "-" * 80 + "\n"
        output += f"  OVERALL SCORE:              {avg_score:>6.1f}/100"
        
        if avg_score >= 90:
            output += " [EXCELLENT]\n"
        elif avg_score >= 80:
            output += " [GOOD]\n"
        elif avg_score >= 70:
            output += " [ACCEPTABLE]\n"
        else:
            output += " [NEEDS IMPROVEMENT]\n"
        
        return output
    
    @staticmethod
    def format_recommendation(result: Dict) -> str:
        """Format bid recommendation."""
        recommendation = result.get('recommendation', 'NO-BID')
        analysis = result.get('analysis', {})
        win_probability = analysis.get('win_probability', 0)
        
        output = "\nRECOMMENDATION:\n"
        output += "=" * 80 + "\n"
        
        if recommendation == 'BID':
            output += f"[RECOMMENDED] ACTION: SUBMIT BID\n"
            output += f"   Win Probability: {win_probability:.1%}\n"
            output += f"   Confidence Level: {'HIGH' if win_probability > 0.7 else 'MEDIUM' if win_probability > 0.5 else 'LOW'}\n"
        else:
            output += f"[NOT RECOMMENDED] ACTION: NO-BID\n"
            output += f"   Reason: {result.get('reason', 'Not competitive')}\n"
        
        # Success factors
        if 'success_factors' in analysis:
            output += f"\n   Success Factors:\n"
            for factor in analysis['success_factors']:
                output += f"   - {factor}\n"
        
        # Risk factors
        if 'risk_factors' in analysis:
            output += f"\n   Risk Factors:\n"
            for risk in analysis['risk_factors']:
                output += f"   - {risk}\n"
        
        return output
    
    @staticmethod
    def format_complete_rfp_output(tender: Dict, result: Dict, index: int = 1) -> str:
        """Format complete RFP processing output."""
        output = ""
        
        # Header
        output += RFPOutputFormatter.format_rfp_header(tender, index)
        
        # Scope
        if result.get('specs'):
            output += RFPOutputFormatter.format_scope_of_supply(tender, result['specs'])
        
        # Technical Recommendations (NEW)
        if result.get('matches') and result.get('specs'):
            output += RFPOutputFormatter.format_technical_recommendations(result['matches'], result['specs'])
        
        # Products
        if result.get('quote') and result['quote'].get('line_items'):
            output += RFPOutputFormatter.format_products_in_scope(result['quote']['line_items'])
        
        # Testing
        if result.get('quote') and result['quote'].get('line_items'):
            output += RFPOutputFormatter.format_testing_requirements(result['quote']['line_items'])
        
        # Pricing Summary
        if result.get('quote'):
            output += RFPOutputFormatter.format_pricing_summary(result['quote'])
        
        # Metrics
        if result.get('quote') and result['quote'].get('metrics'):
            output += RFPOutputFormatter.format_evaluation_metrics(result['quote']['metrics'])
        
        # Recommendation
        output += RFPOutputFormatter.format_recommendation(result)
        
        output += "\n" + "="*80 + "\n"
        
        return output

#!/usr/bin/env python3
"""
Complete RFP Processing Pipeline with Main Agent Architecture
Runs discovery, then processes through Main Agent (hub-and-spoke pattern).

Usage:
    python run_pipeline_new.py [--output results.json]
"""

import json
import sys
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from crawlers.official_sources_only import OfficialSourcesCrawler
from agents.main_agent import MainAgent


async def run_complete_pipeline(output_file="output/pipeline_results_new.json", force_tender_id: str = ""):
    """
    Run complete RFP processing pipeline with Main Agent coordination.
    
    Args:
        output_file: Path to save JSON results
        force_tender_id: If provided, restricts selection to this tender_id
        
    Returns:
        dict: Complete pipeline results
    """
    
    print("=" * 80)
    print("CABLE RFP AUTOMATION - MAIN AGENT ARCHITECTURE")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    # Create output directory
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "pipeline_info": {
            "execution_time": None,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0 (Main Agent)",
            "architecture": "Hub-and-Spoke with Main Agent Coordinator",
            "status": "running",
            "forced_tender_id": force_tender_id or None
        },
        "discovery": {
            "total_discovered": 0,
            "sources": {},
            "tenders": []
        },
        "processing": None
    }
    
    try:
        # STAGE 1: DISCOVERY
        print("=" * 80)
        print("STAGE 1: TENDER DISCOVERY")
        print("=" * 80)
        print()
        
        crawler = OfficialSourcesCrawler()
        discovered_tenders = await crawler.discover_tenders()
        
        # If forcing a specific tender, filter the list to that one (if found)
        if force_tender_id:
            discovered_tenders = [t for t in discovered_tenders if str(t.get("tender_id")) == force_tender_id]
            if not discovered_tenders:
                print(f"WARNING: Forced tender_id '{force_tender_id}' not found in discovery. Proceeding with full list.")
                discovered_tenders = await crawler.discover_tenders()
            else:
                # Normalize deadline to within next 60 days so SalesAgent doesn't drop it
                dl = (datetime.now() + timedelta(days=60)).isoformat() + "Z"
                discovered_tenders[0]["deadline"] = dl
        
        results["discovery"]["total_discovered"] = len(discovered_tenders)
        
        # Group by source
        for tender in discovered_tenders:
            source = tender.get("source", "unknown")
            if source not in results["discovery"]["sources"]:
                results["discovery"]["sources"][source] = 0
            results["discovery"]["sources"][source] += 1
            
            results["discovery"]["tenders"].append({
                "tender_id": tender.get("tender_id"),
                "title": tender.get("title"),
                "source": source,
                "organization": tender.get("organization"),
                "estimated_value": tender.get("estimated_value"),
                "deadline": tender.get("deadline")
            })
        
        print(f"Discovery complete: {len(discovered_tenders)} tenders found")
        for source, count in results["discovery"]["sources"].items():
            print(f"  - {source}: {count} tenders")
        print()
        
        # STAGE 2: MAIN AGENT PROCESSING
        print("=" * 80)
        print("STAGE 2: MAIN AGENT COORDINATION")
        print("=" * 80)
        
        main_agent = MainAgent()
        processing_result = await main_agent.process_tenders(discovered_tenders)
        
        results["processing"] = processing_result
        
        # Mark as complete
        results["pipeline_info"]["status"] = "complete"
        
    except Exception as e:
        results["pipeline_info"]["status"] = "error"
        results["pipeline_info"]["error"] = str(e)
        print(f"\nPIPELINE ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Calculate execution time
        execution_time = time.time() - start_time
        results["pipeline_info"]["execution_time"] = round(execution_time, 2)
        
        # Save to JSON file
        print("\n" + "=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Results saved to: {output_file}")
        print(f"File size: {output_path.stat().st_size:,} bytes")
        print()
        
        # Print summary
        print("=" * 80)
        print("PIPELINE SUMMARY")
        print("=" * 80)
        print(f"Execution Time: {execution_time:.2f} seconds")
        print(f"Status: {results['pipeline_info']['status'].upper()}")
        print()
        print(f"Discovery:")
        print(f"  Total Discovered: {results['discovery']['total_discovered']}")
        print()
        
        if results.get('processing') and results['processing'].get('status') == 'success':
            processing = results['processing']
            print(f"Processing:")
            print(f"  Selected RFP: {processing['selected_rfp']['tender_id']}")
            print(f"  Recommendation: {processing['recommendation']}")
            print(f"  Win Probability: {processing['decision']['win_probability']:.1f}%")
            print(f"  Quoted Value: Rs {processing['decision']['quoted_value']:,.0f}")
            print()
            print(f"Sales Agent:")
            stats = processing['sales_agent_output']['filtering_stats']
            print(f"  Filtered (3-month deadline): {stats['filtered']}")
            print(f"  Qualified (cable-related): {stats['qualified']}")
            print()
            print(f"Technical Agent:")
            products = processing['technical_agent_output']['final_selection']
            print(f"  Products selected: {len(products)}")
            if products:
                for p in products:
                    print(f"    - {p['selected_sku']}: {p['match_score']} match")
            print()
            print(f"Pricing Agent:")
            pricing = processing['pricing_agent_output']['pricing_details']
            print(f"  Material Cost: Rs {pricing['total_material_cost']:,.0f}")
            print(f"  Services Cost: Rs {pricing['total_services_cost']:,.0f}")
            print(f"  Grand Total: Rs {pricing['grand_total']:,.0f}")
        elif results.get('processing'):
            print(f"Processing:")
            print(f"  Status: {results['processing'].get('status', 'unknown')}")
            print(f"  Message: {results['processing'].get('message', 'No details')}")
        
        print()
        print("=" * 80)
    
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run complete Cable RFP automation pipeline with Main Agent"
    )
    parser.add_argument(
        "--output",
        default="output/pipeline_results_new.json",
        help="Output JSON file path (default: output/pipeline_results_new.json)"
    )
    parser.add_argument(
        "--force-tender-id",
        default="",
        help="Optional tender_id to force selection (bypasses normal scoring)"
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    results = asyncio.run(run_complete_pipeline(args.output, force_tender_id=args.force_tender_id))
    
    # Exit with appropriate code
    if results["pipeline_info"]["status"] == "complete":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

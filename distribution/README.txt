================================================================================
CABLE RFP AUTOMATION SYSTEM - v2.0
================================================================================

QUICK START:
------------
1. Ensure Docker Desktop is installed and running
2. Run the startup script:
   - macOS/Linux: ./START_HERE.sh
   - Windows: START_HERE.bat
3. Wait for "System Ready!" message
4. Run pipeline: docker compose exec -T app python run_pipeline_new.py
5. Export results: docker compose exec -T app python export_results.py

SYSTEM REQUIREMENTS:
-------------------
- Docker Desktop (latest version)
- 8GB RAM minimum
- 20GB disk space
- Windows 10+, macOS 10.14+, or Linux

WHAT THIS SYSTEM DOES:
----------------------
- Automates RFP (Request for Proposal) processing for cable manufacturers
- Main Agent orchestration with contextual summaries
- Technical matching with equal weightage scoring
- Automated pricing and quote generation
- Export results to CSV and PDF formats
- Complete end-to-end workflow in ~1.4 seconds

FEATURES:
---------
- 100% competition requirements met (23/23)
- Main Agent hub-and-spoke architecture
- Sales Agent: 3-month deadline filtering
- Technical Agent: Top 3 OEM recommendations with match scores
- Pricing Agent: Material + service cost calculation
- Export functionality: CSV and text/PDF formats

OUTPUT:
-------
After running the pipeline, you will get:
- JSON results: output/pipeline_results_new.json
- CSV export: output/pipeline_results.csv
- Text report: output/pipeline_results.txt

The output includes:
- Selected RFP details
- OEM product SKUs with prices
- Match scores for each product
- Test requirements with costs
- Total quote (material + services)
- Final BID/NO-BID recommendation

DOCUMENTATION:
--------------
- INSTRUCTIONS.md     - Detailed deployment guide
- README.md          - Complete system documentation
- PRODUCTION_READY.md - Production deployment guide

TROUBLESHOOTING:
----------------
If containers don't start:
  docker compose logs app

If pipeline fails:
  docker compose restart app
  docker compose exec -T app python run_pipeline_new.py

If you need to rebuild:
  docker compose down
  docker compose up -d

SUPPORT:
--------
See INSTRUCTIONS.md for detailed troubleshooting guide.

================================================================================
System Version: 2.0.0 (Main Agent)
Compliance: 100% (23/23 requirements)
Architecture: Hub-and-Spoke Multi-Agent System
================================================================================

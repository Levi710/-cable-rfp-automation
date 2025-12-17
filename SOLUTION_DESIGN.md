# Planned Solution Design

## 1) Design Objectives and Constraints

- Scale RFP responses using AI without linear headcount growth
- Eliminate discovery lag (supporting the 90% win correlation)
- Shorten SKU matching time (supporting the 60% win correlation)
- Maintain auditability and compliance (explainable decisions)
- Operate reliably despite portal variability (fallbacks, retries, feature flags)

---

## 2) High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         External Sources                                 │
│  GEM API │ CPPP/eProcure │ NTPC │ POWERGRID │ TenderDetail │ Seed URLs   │
└──────────┴────────────────┴──────┴───────────┴──────────────┴────────────┘
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
│ Source Adapters /        │  │ HTML Scrapers (with      │  │ UrlListCrawler (seed     │
│ API Clients (JSON feeds) │  │ retries + demo fallback) │  │ URLs, heuristic extract) │
└──────────┬───────────────┘  └──────────┬───────────────┘  └──────────┬───────────────┘
           │                               │                               │
           └──────────────┬────────────────┴────────────────┬─────────────┘
                          ▼                                 ▼
                 ┌────────────────────────────────────────────────┐
                 │             Sales Agent (Qualification)         │
                 │  • Keyword filters • Deadline checks • Scoring  │
                 │  • Deduplication • 90-day horizon • CSV log     │
                 └───────────────┬────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────┐
                 │            Technical Agent (Matching)           │
                 │ • Spec extraction/normalization                 │
                 │ • Catalog SKU matching + scores                 │
                 │ • Compliance evidence • New SKU requests        │
                 └───────────────┬────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────┐
                 │         Pricing Agent (Optional/Flag)          │
                 │ • Cost model • Overheads • Margin optimization │
                 │ • Policy rules • Market feeds (optional)       │
                 └───────────────┬────────────────────────────────┘
                                 ▼
                 ┌────────────────────────────────────────────────┐
                 │            Main Orchestrator Agent              │
                 │  • Workflow • Decisions • Bid pack generation  │
                 │  • Audit trail • Exports                       │
                 └───────────────┬────────────────────────────────┘
                                 ▼
           ┌──────────────────────────────────────────────────────────────┐
           │            Storage, APIs, and Observability                  │
           │ JSON files + (optional) PostgreSQL via SQLAlchemy            │
           │ Adaptive scheduler state • Sales CSV • Decision logs         │
           │ Optional FastAPI service • Analytics dashboard script        │
           └──────────────────────────────────────────────────────────────┘
```

Key cross-cutting: feature flags per source; retries/backoff; demo fallbacks; policy-driven configuration.

---

## 3) Data Model (Logical)

- Tender
  - tender_id, source, organization, title, description, publish_date, deadline, url, estimated_value
- Qualification
  - priority_score, reasons, filtered_at, sales_user_notes
- TechnicalMatch
  - rfp_specs (normalized), matched_skus [sku_id, score], compliance_evidence[], new_sku_requested(bool)
- Pricing (optional)
  - base_cost, overhead_breakdown, margin_pct, final_price, policy_rules_applied[]
- DecisionLog
  - decision(BID/NO_BID), rationale, timestamps, attachments[], generated_files[]
- SchedulerMetrics
  - per-source: success_rate, avg_new_rfps_per_crawl, last_crawl, priority

---

## 4) Core Process Flows

1. Discovery Loop
   - Scheduler triggers source adapters/scrapers
   - Normalize tenders → dedupe → persist
2. Sales Qualification
   - Keyword filters → deadline checks → priority scoring
   - Append to `output/sales_selected_rfps.csv`
3. Technical Matching
   - Extract/normalize specs → match catalog → score → evidence
   - If best_score < threshold → emit new SKU request
4. Pricing (flagged)
   - Apply policy-driven components and market feeds → pricing breakdown
5. Bid Pack Generation
   - Compose executive summary, compliance checklists, pricing sheet, certificates, decision log
6. Audit & Export
   - Persist JSON/CSV/MD; optional DB writes; dashboard summaries

---

## 5) Algorithms and Rules

- Sales priority scoring (weights configurable): keyword relevance (0.4), deadline urgency (0.3), estimated value (0.2), organization reputation (0.1)
- Technical match scoring: voltage compatibility (0.4), material match (0.3), standards compliance (0.3); threshold default 0.7
- Pricing: base + overheads + margin with policy adjustments (organization/value-based), optional market-linked inputs

---

## 6) Reliability & Error Handling

- Exponential backoff retries; circuit-breaker per source
- Demo fallback feeds per crawler to maintain continuous operation
- Feature flags to enable/disable brittle sources (e.g., network/DNS issues)
- Deduplication on (tender_id, organization) composite key
- Robust date parsing and deadline validation

---

## 7) Deployment Topologies

- Local dev: `DISABLE_DB=1` (JSON-only); demo feeds; no external dependencies
- Production batch: Docker Compose (App + Postgres) + cron/scheduler
- API mode: FastAPI for integrations (trigger runs, query status)

---

## 8) Security & Governance

- Secrets via environment variables (no plaintext in code/logs)
- Role-based review gates (human-in-loop for final submission)
- Full audit trail: inputs, rules applied, outputs, timestamps

---

## 9) Observability

- Structured logs with per-source success/failure stats
- Adaptive scheduler metrics persisted to `output/adaptive_metrics.json`
- Sales selections persisted to `output/sales_selected_rfps.csv`
- Analytics script to summarize weekly volume, lag, win/loss (when available)

---

## 10) Extensibility Roadmap

- Add new crawlers (Railways, SEBs)
- PDF OCR/NLP for unstructured tenders
- Predictive win probability; deeper margin optimization
- CRM integration for pipeline tracking

---

## 11) Acceptance Tests

- End-to-end: Demo set of 10 tenders processed into bid packs
- Matching accuracy: ≥85% agreement with technical team on pilot set
- Discovery lag SLO: <1 hour for enabled sources
- Submission timeliness: ≥90% submitted >48 hours pre-deadline

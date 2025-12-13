# Cable RFP Automation (Agentic AI System)

An autonomous multi-agent system designed to discover, analyze, and bid on government cable tenders. The system uses a **Hub-and-Spoke Agentic Architecture** to automate the end-to-end RFP process, from discovery to final bid generation.

![Status](https://img.shields.io/badge/Status-Production_Ready-green)
![Python](https://img.shields.io/badge/Python-3.11+-blue)

---

## System Architecture

The system is built on a **Main Agent** architecture that coordinates specialized sub-agents.

```latex
\begin{tikzpicture}[
    node distance=2cm,
    auto,
    agent/.style={rectangle, draw=blue!60, fill=blue!5, very thick, minimum size=10mm, rounded corners, align=center},
    source/.style={rectangle, draw=green!60, fill=green!5, very thick, minimum size=5mm},
    user/.style={circle, draw=black!60, fill=gray!5, very thick, minimum size=5mm},
    line/.style={draw, thick, ->, >=stealth},
]

% Nodes
\node [user] (user) {User};
\node [agent, right of=user, node distance=4cm] (main) {Main Agent\\(Coordinator)};

% Discovery Stage (Left-Below)
\node [agent, below of=main, node distance=3cm, xshift=-3cm] (crawler) {Official Sources\\Crawler};
\node [source, below of=crawler, node distance=2cm] (ntpc) {NTPC Portal};
\node [source, right of=ntpc, node distance=2.5cm] (pg) {POWERGRID};
\node [source, right of=pg, node distance=2.5cm] (seb) {State SEBs};

% Processing Stage (Right)
\node [agent, right of=main, node distance=5cm, yshift=2cm] (sales) {Sales Agent\\(Filter)};
\node [agent, below of=sales, node distance=2.5cm] (tech) {Technical Agent\\(Specs)};
\node [agent, below of=tech, node distance=2.5cm] (price) {Pricing Agent\\(Costing)};

% Output
\node [agent, right of=main, node distance=9cm] (output) {Final Decision\\\& Bid Pack};

% Paths
\path [line] (user) -- node {Start Pipeline} (main);

% Crawler flows
\path [line] (crawler) -- node [left] {Scrapes} (ntpc);
\path [line] (crawler) -- node [right] {Scrapes} (pg);
\path [line] (crawler) -- node [right] {Scrapes} (seb);
\path [line] (ntpc) -- (crawler); % conceptual return
\path [line] (pg) -- (crawler);
\path [line] (seb) -- (crawler);
\path [line] (crawler) -- node [midway, above, sloped] {Returns Tenders} (main);

% Agent flows
\path [line] (main) to [bend left=15] node [above] {1. Filter} (sales);
\path [line] (sales) to [bend left=15] node [below] {Selection} (main);

\path [line] (main) to [bend left=15] node [above] {2. Specs} (tech);
\path [line] (tech) to [bend left=15] node [below] {Matches} (main);

\path [line] (main) to [bend left=15] node [above] {3. Costing} (price);
\path [line] (price) to [bend left=15] node [below] {Quote} (main);

% Final
\path [line] (main) -- node [above] {4. Decision} (output);

\end{tikzpicture}
```

---

## Agents & Capabilities

### 1. Main Agent (The Brain)
- **Role:** Orchestrator & Decision Maker
- **Function:** Coordinates data flow between agents, consolidates results, and calculates **Win Probability**.
- **Logic:**
  - `Win Probability > 50%` → **BID**
  - `Win Probability < 50%` → **NO-BID**

### 2. Sales Agent
- **Role:** Gatekeeper
- **Function:** Filters tenders based on:
  - **Deadlines:** Ensures tender is active (next 3-60 days).
  - **Relevance:** Checks for cable-specific keywords (XLPE, Power Cable, etc.).
- **Output:** Selects the most promising RFP for processing.

### 3. Technical Agent (Enhanced)
- **Role:** Engineer
- **Function:** 
  - Parses complex technical specifications from tender documents.
  - Matches requirements against an **OEM Product Catalog**.
  - Handles **Gap Analysis** (e.g., matching 11kV requirements to 11kV products).
  - Generates "New SKU Requests" if no suitable product exists.

### 4. Pricing Agent
- **Role:** Commercial Lead
- **Function:** 
  - Calculates **Material Costs** (Cable lengths * Unit rates).
  - Estimates **Service Costs** (Transport, Installation, Testing).
  - Adds **Margins & Taxes** (GST, Contingency).
  - Generates the final **Bill of Quantities (BOQ)**.

---

## Crawler System

The system includes robust crawlers for major Indian government e-procurement portals.

| Source | Feature | URL | resilience |
|--------|---------|-----|------------|
| **NTPC** | eProcurement | `eprocurentpc.nic.in` | Proxy Supported |
| **POWERGRID** | PRANIT Portal | `eprocure.powergrid.in` | Proxy Supported |
| **State SEBs** | Maharashtra, etc. | `mahadiscom.in` | Auto-Retry |

*   **Status Logging:** Tracks successful/failed scrapes in `output/crawler_status.json`.
*   **Proxy Support:** Configurable via `.env` for accessing geo-restricted portals.

---

## How to Run

### Prerequisites
- Python 3.11+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Luciferai04/-cable-rfp-automation.git
cd -cable-rfp-automation
```

### 2. Setup Environment
Rename the template file and configure your settings:
```bash
cp .env.example .env
```
Edit `.env` to add your keys (optional) and Proxy settings if needed.

### 3. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Pipeline
Execute the main pipeline script:
```bash
python run_pipeline_new.py
```

### Outputs
Results are generated in the `output/` directory:
- `pipeline_results_new.json`: Complete JSON dump of the process.
- `crawler_status.json`: Health check of all crawlers.
- `new_sku_requests/`: Markdown files for any custom manufacturing requests.

---

## Decision Logic

The **BID / NO-BID** decision is based on a weighted probability algorithm:

1.  **Base Score:** 50%
2.  **Product Match:** 
    *   Match > 70%: **+5%** (Qualifies for BID)
    *   Match < 70%: **-5%** (Rejects as NO-BID)
3.  **Price Competitiveness** (if estimated value known):
    *   Quote within range: **+20%**
4.  **Urgency:**
    *   Urgent (<30 days): **+10%**

---

## Security
- **.gitignore:** Configured to exclude all sensitive data and outputs.
- **Environment Variables:** All secrets managed via `.env`.
- **Crawler resilience:** Handles SSL errors and proxies securely.

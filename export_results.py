import json
import csv
from pathlib import Path


def load_latest_result() -> dict:
    """
    Load the main pipeline output. Prefer the latest run output file that the
    pipeline generates (`pipeline_results_new.json`). Fall back to
    `pipeline_results.json` if needed.
    """
    output_dir = Path("output")
    candidates = [
        output_dir / "pipeline_results_new.json",
        output_dir / "pipeline_results.json",
    ]
    for path in candidates:
        if path.exists():
            return json.loads(path.read_text())
    raise FileNotFoundError("No pipeline results JSON found in output/")


def export_csv(data: dict, csv_path: Path) -> None:
    processing = data.get("processing", {})
    selected = processing.get("selected_rfp", {}) or processing.get("selected_tender", {})
    overall = processing.get("overall_response", {})
    decision = processing.get("decision", {})

    rows = [{
        "tender_id": selected.get("tender_id"),
        "title": selected.get("title"),
        "organization": selected.get("organization"),
        "estimated_value": selected.get("estimated_value"),
        "recommendation": decision.get("recommendation") or processing.get("recommendation"),
        "win_probability": decision.get("win_probability") or processing.get("win_probability"),
        "quoted_value": decision.get("quoted_value") or processing.get("quoted_value"),
        "grand_total": overall.get("grand_total"),
    }]

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def export_text(data: dict, txt_path: Path) -> None:
    output = []
    processing = data.get("processing", {})
    selected = processing.get("selected_rfp", {}) or processing.get("selected_tender", {})
    decision = processing.get("decision", {})
    overall = processing.get("overall_response", {})

    output.append("CABLE RFP AUTOMATION - PIPELINE RESULTS")
    output.append("=" * 60)
    output.append(f"Recommendation: {decision.get('recommendation') or processing.get('recommendation')}")
    output.append(f"Win Probability: {decision.get('win_probability') or processing.get('win_probability')}")
    output.append(f"Quoted Value: {decision.get('quoted_value') or processing.get('quoted_value')}")
    output.append("")
    output.append("Selected RFP")
    output.append(f"  ID: {selected.get('tender_id')}")
    output.append(f"  Title: {selected.get('title')}")
    output.append(f"  Organization: {selected.get('organization')}")
    output.append(f"  Estimated Value: {selected.get('estimated_value')}")
    output.append("")
    output.append("Overall Response")
    output.append(f"  Grand Total: {overall.get('grand_total')}")
    output.append(f"  OEM Products: {len(overall.get('oem_products', []))}")
    output.append(f"  Tests Required: {len(overall.get('tests_required', []))}")

    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text("\n".join(output))


def main():
    data = load_latest_result()
    export_csv(data, Path("output/pipeline_results.csv"))
    export_text(data, Path("output/pipeline_results.txt"))
    print("Exports written to output/pipeline_results.csv and output/pipeline_results.txt")


if __name__ == "__main__":
    main()


"""AI-assisted scheme discovery pipeline — run on demand, never scheduled.

Fetches candidate scheme records from a configured source, maps them into
Setu's schema, runs each through app.discovery.gate's safety checks, and
merges anything that passes straight into the target dataset file.

There is no human-approval queue by design (that tradeoff was made
explicitly, accepting the residual risk, in exchange for the gate below
being as strict as it reasonably can be). The one review checkpoint that
still exists is `git diff` before you commit/push — always read it.

Usage (run from the backend/ directory):
  # Test the pipeline end-to-end against a local sample file (no network,
  # no API key needed) — good for a first run to see the report format.
  # Add --skip-url-check too if you're offline / behind a restrictive proxy:
  python scripts/discover_schemes.py --source local --input scripts/sample_candidates.json --dry-run

  # Real run against a data.gov.in resource you've found and verified yourself:
  export DATA_GOV_IN_API_KEY=your_key_here
  python scripts/discover_schemes.py --source datagovin --resource-id <uuid>

Both accept --dataset student|senior and --dry-run (report only, don't write).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.discovery.fetcher import DataGovInFetcher, LocalSampleFetcher
from app.discovery.gate import run_gate
from app.discovery.mapper import map_record

DATASET_PATHS = {
    "student": Path(__file__).resolve().parent.parent / "app" / "data" / "schemes.json",
    "senior": Path(__file__).resolve().parent.parent / "app" / "data" / "senior_citizen_schemes.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", choices=["student", "senior"], default="student")
    parser.add_argument("--source", choices=["local", "datagovin"], required=True)
    parser.add_argument("--input", help="Path to local sample JSON (for --source local)")
    parser.add_argument("--resource-id", help="data.gov.in resource UUID (for --source datagovin)")
    parser.add_argument("--source-url", default="", help="URL to record as provenance in ai_metadata")
    parser.add_argument("--skip-url-check", action="store_true", help="Skip live HTTP reachability check (offline testing only)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would happen, don't write the dataset file")
    args = parser.parse_args()

    dataset_path = DATASET_PATHS[args.dataset]
    existing = json.loads(dataset_path.read_text(encoding="utf-8"))
    existing_ids = {s["scheme_id"] for s in existing}

    if args.source == "local":
        if not args.input:
            parser.error("--input is required for --source local")
        fetcher = LocalSampleFetcher(args.input)
        source_url = args.source_url or f"local:{args.input}"
    else:
        if not args.resource_id:
            parser.error("--resource-id is required for --source datagovin")
        fetcher = DataGovInFetcher(resource_id=args.resource_id)
        source_url = args.source_url or f"https://www.data.gov.in/resource/{args.resource_id}"

    print(f"Fetching candidates from {args.source}...")
    raw_records = fetcher.fetch()
    print(f"Got {len(raw_records)} raw record(s).\n")

    accepted, rejected = [], []
    for raw in raw_records:
        scheme = map_record(raw, source_url=source_url, existing_ids=existing_ids)
        if scheme is None:
            rejected.append(("(unmappable record — no name/description found)", ["too sparse to map"]))
            continue

        result = run_gate(scheme, existing, check_urls=not args.skip_url_check)
        if result.accepted:
            accepted.append(scheme)
            existing_ids.add(scheme["scheme_id"])
            existing.append(scheme)  # so later records in this batch dedup against it too
        else:
            rejected.append((scheme["scheme_name"], result.reasons))

    print(f"ACCEPTED: {len(accepted)}")
    for s in accepted:
        print(f"  + {s['scheme_id']} — {s['scheme_name']}")

    print(f"\nREJECTED: {len(rejected)}")
    for name, reasons in rejected:
        print(f"  - {name}")
        for r in reasons:
            print(f"      · {r}")

    if not accepted:
        print("\nNothing to merge.")
        return 0

    if args.dry_run:
        print(f"\n--dry-run set: not writing to {dataset_path}")
        return 0

    dataset_path.write_text(
        json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nMerged {len(accepted)} new scheme(s) into {dataset_path}.")
    print("Review the diff before committing: git diff -- " + str(dataset_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

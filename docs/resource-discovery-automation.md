# Resource Discovery Automation

The weekly resource-discovery job watches high-value registries for grants, business capital, fiscal sponsors, nonprofits, businesses, artists, and creative opportunities.

A separate Thursday event-source run uses the same review-only engine for fifteen local calendars and event-submission hubs: five each for Colfax, Las Animas, and Huerfano counties.

## Files

- `data/resource-keyword-registry.json` controls phrases used to identify relevant candidate links.
- `data/resource-discovery-sources.json` lists source hubs, their purpose, cadence, and automation mode.
- `scripts/audit_resource_discovery_sources.py` checks pages and extracts review-only candidate links.
- `.github/workflows/weekly-resource-discovery.yml` runs the process each Wednesday and opens a draft review pull request when tracked outputs change.
- `data/event-watch-sources.json` lists the fifteen county-balanced event hubs shown on the public Events page.
- `data/event-watch-state.json` stores the last successful event-hub snapshots.
- `.github/workflows/weekly-event-source-watch.yml` checks those hubs and opens a draft review pull request when a page changes or a new candidate event link appears.

## Safe Boundary

The job never adds a candidate to the public directory. A reviewer must open the original page and confirm:

1. The organization, program, or opportunity is real and relevant to the tri-county audience.
2. The source permits the intended use of its data.
3. Deadlines, geography, applicant type, funding range, fees, fiscal-sponsor rules, and contact details are current.
4. The public description uses the organization's own current language where practical without copying long passages.
5. The permanent exclusion check passes before deployment.

## Local Check

```powershell
python scripts/audit_resource_discovery_sources.py --no-network
python -m unittest discover -s tests -p "test_*.py"
```

Run the network check only when you want a fresh private review queue:

```powershell
python scripts/audit_resource_discovery_sources.py --timeout 20
```

Run the event watcher locally without network access:

```powershell
python scripts/audit_resource_discovery_sources.py --sources data/event-watch-sources.json --keywords data/resource-keyword-registry.json --state data/event-watch-state.json --out-dir review/event-watch --report-slug event-watch --report-title "Tri-County Event Source Review" --no-network
```

# Weekly Listing Keyword Sweep

The keyword sweep improves directory search without rewriting listing descriptions, names, contacts, eligibility, rates, deadlines, or civic guidance.

## Data Flow

1. Read every canonical row in `data/tri_county_persona_resources.csv`.
2. Match stable terms from the listing name, category, resource type, notes, goals, audience, and access mode.
3. Select the oldest unchecked public URLs, up to the configured weekly limit.
4. Read only page titles, description metadata, and `h1`-`h3` headings.
5. Map those signals to a controlled regional vocabulary.
6. Write `data/listing-keyword-index.json`.
7. Rebuild and validate the directory.
8. Open a review pull request. Public search changes only after merge.

The generator combines the reviewed keyword index with existing listing fields. The index is search metadata and is not displayed as developer or verification copy on public cards.

## Rotation

The scheduled workflow checks up to 120 distinct public pages each Wednesday. Pages with no prior check date run first. After a successful review branch is merged, older pages move ahead of recently checked pages, allowing the sweep to cover the full source set over several runs.

Several listings may share one chamber, tourism, directory, or social page. The sweep fetches that URL once and applies matched source terms to the linked listing IDs.

## Controlled Vocabulary

The script recognizes practical terms such as:

- gallery, artist, maker, photography, pottery, tattoo, music, theater, writing;
- restaurant, cafe, bakery, catering, brewery, lodging, camping, outfitter;
- grant, loan, scholarship, stipend, sponsorship, training, mentorship;
- chamber, directory, calendar, newsletter, newspaper, radio, visitor guide;
- flyer distribution, bulletin board, event submission, event venue;
- retail, construction, professional services, health, education, transportation.

Aliases are normalized, but partial words do not count. For example, `art` inside `cart` does not mark a listing as an art gallery.

## Failure Rules

- A timeout, bot block, or HTTP failure does not erase previously reviewed source keywords.
- A page without a URL still receives keywords from canonical listing fields.
- Raw webpage copy is not stored. The index keeps controlled terms, a content hash, status, dates, and URL provenance.
- A person reviews additions and removals before merging the automation branch.

## Local Commands

Seed or validate all listings without network access:

```powershell
python scripts/sweep_listing_keywords.py --no-network --write-index
```

Refresh the oldest 120 public pages:

```powershell
python scripts/sweep_listing_keywords.py --limit 120 --write-index
```

The latest review files are:

```text
review/keyword-sweep/keyword-sweep-latest.md
review/keyword-sweep/keyword-sweep-latest.json
```

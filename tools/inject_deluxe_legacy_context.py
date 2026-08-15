from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "tri-county-netlify-guide-deep"


def inject(relative_path: str, marker: str, section: str) -> None:
    path = OUT / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Generated page not found: {path}")
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return
    if "</main>" not in text:
        raise RuntimeError(f"Could not find </main> in {path}")
    path.write_text(text.replace("</main>", section.strip() + "\n</main>", 1), encoding="utf-8")

REGION = r"""
<section id="legacy-regional-context" class="section">
  <div class="section-heading"><p class="eyebrow">Why this is a tri-county guide</p>
    <h2>Market across the state line when the audience already does.</h2></div>
  <div class="mini-grid">
    <article class="mini-card"><h3>Regional economic-development lens</h3><p>The earlier guide used the Stronger Economies Together (SET) framework to explain a practical point: Colfax, Las Animas, and Huerfano counties share customers, visitors, workers, media, events, suppliers, and cultural networks. Begin locally and widen across the three-county area when the audience, season, or project warrants it.</p></article>
    <article class="mini-card"><h3>Know the audience before choosing the channel</h3><p>Use broadband and device access, commuting and workforce patterns, visitor seasonality, and local business-sector concentrations as marketing inputs before choosing digital, print, radio, tourism, hiring, or partnership channels.</p></article>
    <article class="mini-card"><h3>Use county pages as starting points, not walls</h3><p>Start where the activity happens, then add neighboring channels when people realistically cross county or state lines for the same event, service, attraction, job, or purchase.</p></article>
  </div>
</section>
"""
PLAN = r"""
<section id="legacy-campaign-timeline" class="section">
  <div class="section-heading"><p class="eyebrow">Reusable workflow</p><h2>A practical four-week promotion timeline</h2></div>
  <div class="mini-grid">
    <article class="mini-card"><h3>3–4 weeks out</h3><p>Prepare the core asset packet and submit to event calendars, tourism channels, newsletters, venue calendars, chambers, and other channels with longer lead times.</p></article>
    <article class="mini-card"><h3>About 2 weeks out</h3><p>Confirm media, partner, sponsor, and cross-promotion placements. Give collaborators a clean image, short description, date, time, location, link, contact, and accessibility information.</p></article>
    <article class="mini-card"><h3>About 1 week out</h3><p>Run reminder posts, community-calendar follow-up, bulletin-board or flyer distribution, and direct partner sharing. Correct stale listings before duplicating outreach.</p></article>
    <article class="mini-card"><h3>After the campaign</h3><p>Record which channels responded, what was free or paid, deadlines, contacts, traffic or attendance signals, and anything that should change before the next campaign.</p></article>
  </div>
</section>
"""

COLFAX = r"""
<section id="legacy-inventory-method" class="section">
  <div class="section-heading"><p class="eyebrow">From the original Raton inventory</p><h2>Use the directory as an outreach inventory, not just a list of names.</h2></div>
  <div class="mini-grid">
    <article class="mini-card"><h3>Check what kind of connection exists</h3><p>Distinguish a direct website from a hosted profile, directory listing, phone or email contact, physical promotion location, or calendar, newsletter, and media route. The current directory exposes these differences so outreach can match the connection actually available.</p></article>
    <article class="mini-card"><h3>Use the inventory to find gaps</h3><p>A missing or stale listing is a support opportunity: confirm the organization still exists, find the strongest official contact route, update the directory when appropriate, and avoid treating an unverified lead as current fact.</p></article>
  </div>
</section>
"""
PROMOTE = r"""
<section id="legacy-local-tags" class="section">
  <div class="section-heading"><p class="eyebrow">Copyable local vocabulary</p><h2>Local hashtag starters</h2>
    <p>These are starter terms from the earlier guide, not a requirement to use a fixed number of hashtags. Use only tags that accurately fit the post and check current platform conventions before relying on them for reach.</p></div>
  <div class="mini-grid">
    <article class="mini-card"><h3>Raton / Colfax</h3><p><code>#RatonNM</code> <code>#ExploreRaton</code> <code>#RatonMainStreet</code> <code>#ColfaxCountyNM</code></p></article>
    <article class="mini-card"><h3>Trinidad / Las Animas</h3><p><code>#TrinidadColorado</code> <code>#VisitTrinidadColorado</code> <code>#LasAnimasCounty</code></p></article>
    <article class="mini-card"><h3>Walsenburg / Huerfano</h3><p><code>#WalsenburgCO</code> <code>#HuerfanoCounty</code> <code>#SpanishPeaksCountry</code></p></article>
    <article class="mini-card"><h3>Regional</h3><p>Pair a specific town or county tag with an accurate subject tag such as arts, live music, outdoor recreation, local business, tourism, nonprofit, hiring, or community events.</p></article>
  </div>
</section>
"""

TEMPLATES = r"""
<section id="legacy-accessibility-checklist" class="section">
  <div class="section-heading"><p class="eyebrow">Before publishing</p><h2>Make the promotion usable by more people.</h2></div>
  <div class="mini-grid">
    <article class="mini-card"><h3>Images</h3><p>Write useful alt text for informative images and keep essential event information in actual text as well as inside a flyer image.</p></article>
    <article class="mini-card"><h3>Video and audio</h3><p>Caption spoken content and provide a text alternative when important information is delivered through audio alone.</p></article>
    <article class="mini-card"><h3>Readability</h3><p>Use strong contrast, readable type sizes, plain language, descriptive link text, and a logical order: what, when, where, cost, access, and contact.</p></article>
    <article class="mini-card"><h3>Event details</h3><p>Include accessibility notes when known: physical access, seating, restrooms, interpretation, sensory considerations, transportation, and the best contact for accommodation questions.</p></article>
  </div>
</section>
"""
inject("region/index.html", "legacy-regional-context", REGION)
inject("plan/index.html", "legacy-campaign-timeline", PLAN)
inject("counties/colfax/index.html", "legacy-inventory-method", COLFAX)
inject("promote/index.html", "legacy-local-tags", PROMOTE)
inject("templates/index.html", "legacy-accessibility-checklist", TEMPLATES)

print("Injected retained Deluxe Horse context into generated site.")

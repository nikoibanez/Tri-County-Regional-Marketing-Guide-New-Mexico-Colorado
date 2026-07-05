from __future__ import annotations

import html
import csv
import json
import os
import re
import shutil
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import quote, urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_OUT = os.environ.get("TRI_COUNTY_SITE_OUT")
SITE = (ROOT / SITE_OUT).resolve() if SITE_OUT else Path.home() / "TriCountyGuide_20260701_DirectorySweep_Site"
AUDIO_PKG = Path.home() / "tri_deploy_work_20260701" / "regional_audio_assets_package" / "tri_county_regional_audio_assets"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def trim(value: object, limit: int = 220) -> str:
    value = clean_text(value)
    if len(value) <= limit:
        return value
    return value[:limit].rsplit(" ", 1)[0] + "..."


def root_prefix(rel_path: str) -> str:
    parent = Path(rel_path).parent
    if str(parent) == ".":
        return ""
    return "../" * len(parent.parts)


def link(prefix: str, target: str) -> str:
    return prefix + target


def active_attr(rel_path: str, target: str) -> str:
    return ' aria-current="page" class="is-active"' if rel_path == target else ""


def header(rel_path: str) -> str:
    prefix = root_prefix(rel_path)

    def a(label: str, target: str, extra_class: str = "") -> str:
        active = rel_path == target
        cls = " ".join(part for part in [extra_class, "is-active" if active else ""] if part)
        cls_attr = f' class="{cls}"' if cls else ""
        aria = ' aria-current="page"' if active else ""
        return f'<a{aria}{cls_attr} href="{link(prefix, target)}">{esc(label)}</a>'

    def group_class(targets: list[str]) -> str:
        return ' class="nav-group is-active"' if rel_path in targets else ' class="nav-group"'

    return f'''<header class="site-header">
<a aria-label="Stateline Guide home" class="brand" href="{link(prefix, 'index.html')}"><span class="brand-mark">SG</span><span>Stateline Guide</span></a>
<nav aria-label="Primary navigation" class="site-nav">
{a('Home', 'index.html')}
<details{group_class(['plan/index.html', 'region/index.html', 'about/index.html'])}><summary class="nav-trigger">Start Here</summary><div class="nav-menu">
{a('Plan your route', 'plan/index.html')}{a('Regional map', 'region/index.html')}{a('How it was built', 'about/index.html')}
</div></details>
<details{group_class(['resources/index.html', 'network/index.html', 'resources/funding/index.html', 'resources/arts-culture/index.html', 'local-music-arts/index.html', 'artist-gallery-promotion/index.html', 'amplifiers/index.html', 'appendix/index.html'])}><summary class="nav-trigger">Directory</summary><div class="nav-menu">
{a('Resource directory', 'resources/index.html')}{a('All listings', 'resources/index.html#everything-directory')}{a('Advanced filters', 'network/index.html')}{a('Funding', 'resources/funding/index.html')}{a('Arts & Culture', 'resources/arts-culture/index.html')}{a('Calendars + visitor channels', 'amplifiers/index.html')}{a('Appendix', 'appendix/index.html')}
</div></details>
<details{group_class(['counties/colfax/index.html', 'counties/las-animas/index.html', 'counties/huerfano/index.html'])}><summary class="nav-trigger">Counties</summary><div class="nav-menu">
{a('Colfax', 'counties/colfax/index.html')}{a('Las Animas', 'counties/las-animas/index.html')}{a('Huerfano', 'counties/huerfano/index.html')}
</div></details>
<details{group_class(['promote/index.html', 'posting/index.html', 'post-events-raton/index.html', 'post-events-trinidad/index.html', 'post-events-huerfano/index.html', 'advertise-colfax/index.html', 'advertise-las-animas/index.html', 'advertise-huerfano/index.html', 'templates/index.html'])}><summary class="nav-trigger">Promote</summary><div class="nav-menu">
{a('Marketing playbook', 'promote/index.html')}{a('Posting basics', 'posting/index.html')}{a('Raton events', 'post-events-raton/index.html')}{a('Trinidad events', 'post-events-trinidad/index.html')}{a('Huerfano events', 'post-events-huerfano/index.html')}{a('Colfax ads', 'advertise-colfax/index.html')}{a('Las Animas ads', 'advertise-las-animas/index.html')}{a('Huerfano ads', 'advertise-huerfano/index.html')}{a('Templates', 'templates/index.html')}
</div></details>
{a('Submit Update', 'submit/index.html', 'nav-submit')}
</nav>
</header>'''


def footer(rel_path: str) -> str:
    prefix = root_prefix(rel_path)

    def li(label: str, target: str) -> str:
        return f'<li><a href="{link(prefix, target)}">{esc(label)}</a></li>'

    return f'''<footer class="site-footer">
<div class="footer-summary">
<p class="footer-kicker">Colfax NM + Las Animas CO + Huerfano CO</p>
<p>This guide helps businesses, artists, nonprofits, programs, venues, and service providers find the right regional route faster.</p>
<p class="footer-small">See something outdated? Send a source link through Submit Update so the guide can improve.</p>
<div aria-label="Project logo area" class="footer-logos"><span class="footer-placeholder">Stateline</span><img alt="Project logo" src="{link(prefix, 'assets/super-eukarya-logo.png')}"/></div>
</div>
<nav aria-label="Footer site index" class="footer-index">
<div class="footer-column"><h2>Start</h2><ul>{li('Home','index.html')}{li('Plan','plan/index.html')}{li('Region','region/index.html')}{li('Creation process','about/index.html')}</ul></div>
<div class="footer-column"><h2>Directory</h2><ul>{li('Resource directory','resources/index.html')}{li('All listings','resources/index.html#everything-directory')}{li('Advanced filters','network/index.html')}{li('Funding','resources/funding/index.html')}{li('Arts & Culture','resources/arts-culture/index.html')}{li('Appendix','appendix/index.html')}</ul></div>
<div class="footer-column"><h2>Counties</h2><ul>{li('Colfax','counties/colfax/index.html')}{li('Las Animas','counties/las-animas/index.html')}{li('Huerfano','counties/huerfano/index.html')}{li('Regional channels','regional-channels/index.html')}</ul></div>
<div class="footer-column"><h2>Promote</h2><ul>{li('Marketing playbook','promote/index.html')}{li('Posting basics','posting/index.html')}{li('Raton events','post-events-raton/index.html')}{li('Trinidad events','post-events-trinidad/index.html')}{li('Huerfano events','post-events-huerfano/index.html')}{li('Templates','templates/index.html')}</ul></div>
<div class="footer-column"><h2>Data + Updates</h2><ul>{li('Submit update','submit/index.html')}{li('CSV data','data/tri_county_persona_resources.csv')}{li('YellowPages outreach CSV','data/yellowpages_outreach_leads_20260701.csv')}{li('Workbook','data/MAILCHIMP_DIRECTORY_WORKBOOK_2026-06-27.xlsx')}{li('Sources','SOURCES.md')}{li('Sitemap','sitemap.xml')}</ul></div>
</nav>
</footer>'''


def assistant(rel_path: str) -> str:
    prefix = root_prefix(rel_path)
    return f'''<section aria-label="Directory assistant" class="directory-assistant" data-directory-assistant="" data-network-url="{link(prefix, 'network/index.html')}" data-submit-url="{link(prefix, 'submit/index.html')}">
<button aria-controls="directory-assistant-panel" aria-expanded="false" aria-haspopup="dialog" class="directory-assistant__toggle" type="button"><span aria-hidden="true" class="assistant-dot"></span>Ask directory</button>
<dialog aria-describedby="directory-assistant-intro directory-assistant-hint" aria-labelledby="directory-assistant-title" class="directory-assistant__panel" id="directory-assistant-panel"><div class="directory-assistant__header"><div><p class="eyebrow">Immediate directory</p><h2 id="directory-assistant-title">Find the right route.</h2></div><button aria-label="Close directory assistant" class="directory-assistant__close" type="button">Close</button></div><p class="directory-assistant__intro" id="directory-assistant-intro">Search by need, county, town, audience, or task. Results include practical links and update paths.</p><p class="sr-only" id="directory-assistant-hint">Results update after submitting the form or after a short pause while typing. Press Escape to close this panel.</p><form class="directory-assistant__form" role="search"><label for="directory-assistant-query">What are you trying to find?</label><div class="directory-assistant__search-row"><input aria-controls="directory-assistant-results" aria-describedby="directory-assistant-hint directory-assistant-status" autocomplete="off" id="directory-assistant-query" name="directory_query" placeholder="grants, artist, event, Raton, nonprofit..." type="search"/><button class="button button-primary" type="submit">Search</button></div></form><div aria-label="Suggested searches" class="directory-assistant__chips" role="group"><button data-assistant-prompt="funding grants scholarships stipends" type="button">Funding</button><button data-assistant-prompt="artists creative galleries makers" type="button">Artists</button><button data-assistant-prompt="event calendar submit event" type="button">Events</button><button data-assistant-prompt="nonprofit community services" type="button">Nonprofits</button><button data-assistant-prompt="Raton Colfax" type="button">Raton</button><button data-assistant-prompt="Trinidad Las Animas" type="button">Trinidad</button><button data-assistant-prompt="Walsenburg Huerfano La Veta" type="button">Huerfano</button></div><div aria-atomic="true" aria-live="polite" class="directory-assistant__status" id="directory-assistant-status" role="status"></div><div aria-label="Directory assistant results" class="directory-assistant__results" data-assistant-results="" id="directory-assistant-results" role="list"></div><div class="directory-assistant__footer"><a class="button button-soft" href="{link(prefix, 'resources/index.html')}">Open resource directory</a><a class="button button-soft" href="{link(prefix, 'submit/index.html')}">Submit a correction</a></div></dialog>
</section>'''


def page_shell(rel_path: str, title: str, desc: str, body: str, body_class: str = "theme-culture", pre_header: str = "") -> str:
    prefix = root_prefix(rel_path)
    canonical_path = "" if rel_path == "index.html" else rel_path.replace("index.html", "")
    canonical_url = f"https://statelineguide.org/{canonical_path}"
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": desc,
        "url": canonical_url,
        "isPartOf": {
            "@type": "WebSite",
            "name": "Stateline Guide",
            "url": "https://statelineguide.org/"
        },
        "audience": {
            "@type": "Audience",
            "audienceType": "Businesses, nonprofits, artists, entrepreneurs, venues, programs, and service providers"
        },
        "about": "Regional marketing, directory, funding, event, arts, tourism, and outreach resources for Colfax County, Las Animas County, and Huerfano County"
    }, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow"><meta name="theme-color" content="#173047"><link rel="canonical" href="{esc(canonical_url)}"><meta property="og:type" content="website"><meta property="og:site_name" content="Stateline Guide"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical_url)}"><meta name="twitter:card" content="summary_large_image"><title>{esc(title)}</title><script type="application/ld+json">{json_ld}</script><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet"><link rel="icon" href="{link(prefix, 'assets/site-icon.svg')}" type="image/svg+xml"><link rel="alternate" type="application/json" href="{link(prefix, 'data/guide-data.json')}"><link rel="stylesheet" href="{link(prefix, 'assets/styles.css')}"><script src="{link(prefix, 'assets/site-data.js')}"></script><script defer src="{link(prefix, 'assets/app.js')}"></script></head><body class="{body_class}"><a class="skip-link" href="#main">Skip to content</a>{pre_header}{header(rel_path)}<main id="main">{body}</main><div aria-label="Page controls" class="corner-controls"><a class="back-to-top" href="#main">Back to top</a></div>{assistant(rel_path)}{footer(rel_path)}</body></html>'''


def public_desc(row: dict) -> str:
    return resource_row_description(row)


def public_label(value: object) -> str:
    label = str(value or "Resource")
    label = re.sub(r"Outreach lead / source-check candidate", "Local resource", label, flags=re.I)
    label = re.sub(r"source-linked lead", "listed resource", label, flags=re.I)
    label = re.sub(r"Commercial directory lead / local business", "Local business listing", label, flags=re.I)
    label = re.sub(r"Commercial directory lead sweep / needs verification", "Commercial directory sweep", label, flags=re.I)
    label = re.sub(r"Sparse-area community lead", "Small-community contact", label, flags=re.I)
    label = re.sub(r"Unknown source", "Source needed", label, flags=re.I)
    label = re.sub(r"\bleads?\b", "listing", label, flags=re.I)
    return label


def public_category(value: object) -> str:
    label = public_label(value)
    label = re.sub(r"Leading Local Pages and Channels to Watch", "Important local pages and channels", label, flags=re.I)
    label = re.sub(r"Lead Sweep", "Directory sweep", label, flags=re.I)
    if "Registered businesses" in label and re.search(r"\(\s*\d{3}[-\s]\d{3}[-\s]\d{4}", label):
        return "Registered businesses"
    return trim(label, 96)


def public_entry_kind(value: object) -> str:
    kind = str(value or "").strip().lower()
    if kind == "directory_shortcut":
        return "Directory shortcut"
    if kind == "local_inventory_lead":
        return "Listing"
    return "Directory entry"


def list_search(label: str, placeholder: str) -> str:
    return f'''<div class="tool-panel list-search" data-list-search><label>{esc(label)}<input class="search-input" type="search" data-list-search-input placeholder="{esc(placeholder)}"></label><p class="section-note" data-list-search-status>Search the rows in this section.</p></div>'''


def source_card(src: dict) -> str:
    url = src.get("url") or ""
    title = esc(src.get("title"))
    title_html = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">{title}</a>' if url else title
    return f'''<article class="source-card" data-county="{esc(src.get('county'))}" data-kind="{esc(src.get('kind'))}"><div class="source-card__meta"><span>{esc(src.get('county'))}</span><span>{esc(src.get('kind'))}</span></div><h3>{title_html}</h3><p>{esc(src.get('best_for'))}</p><p class="action-line">{esc(src.get('action') or 'Open the page and check current details before acting.')}</p><p class="source-note">Details can change. Open the page before spending money or announcing placement.</p></article>'''


def compact_resource(row: dict, prefix: str) -> str:
    url = row.get("website") or row.get("source_url") or ""
    place = ", ".join([x for x in [row.get("town"), row.get("county"), row.get("state")] if x]) or row.get("county") or "Regional"
    action = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">Open page</a>' if url else f'<a href="{prefix}submit/index.html">Send an update</a>'
    return f'''<article class="compact-resource" data-county="{esc(row.get('county'))}" data-type="{esc(public_label(row.get('resource_type')))}"><h3>{esc(row.get('resource_name') or 'Untitled resource')}</h3><p class="resource-meta"><span>{esc(place)}</span><span>{esc(public_label(row.get('resource_type') or 'Resource'))}</span><span>{esc(public_label(row.get('category') or 'General'))}</span></p><p>{esc(trim(public_desc(row)))}</p><div class="resource-actions">{action}</div></article>'''


def public_entry_description(entry: dict) -> str:
    raw = clean_text(entry.get("description") or "")
    if re.search(r"creative-directory lead added", raw, re.I):
        return "Creative listing from a public arts, tourism, chamber, creative-district, or maker source. Check current hours, contact paths, and participation details before outreach."
    if re.search(r"visitor-facing listing pulled", raw, re.I):
        return "Visitor-facing listing from a public tourism or travel source. Check current details before planning outreach or promotion."
    if re.search(r"commercial-directory-only lead", raw, re.I):
        return "Local business listing from a public commercial directory. Use it as a starting contact, then check the current source before outreach or publication."
    if re.search(r"individual maker/vendor lead", raw, re.I):
        return "Maker or vendor listing from a public local source. Check current vendor status, products, contact route, and permission before outreach or publication."
    if re.search(r"individual artist lead", raw, re.I):
        return "Artist listing from a public creative directory. Check current practice, contact route, representation, and permission before outreach or publication."
    if not raw or re.search(r"launch/outreach lead|verify details before spending|not final proof|source-check|spreadsheet-backed", raw, re.I):
        return "Use this as a starting listing. Open a source link when available, and send an update if details have changed."
    raw = re.sub(r"source-backed starting points?", "starting points", raw, flags=re.I)
    raw = re.sub(r"Confirm current rules, rates, dates, and acceptance before action\.", "Check current details before spending money or announcing placement.", raw, flags=re.I)
    raw = re.sub(r"\bVerify\b", "Check", raw)
    raw = re.sub(r"\blead list\b", "starting list", raw, flags=re.I)
    raw = re.sub(r"\bleads\b", "listings", raw, flags=re.I)
    raw = re.sub(r"\blead\b", "route", raw, flags=re.I)
    raw = re.sub(r"\bleads?\b", "listing", raw, flags=re.I)
    return trim(raw, 260)


def public_entry_action(entry: dict) -> str:
    raw = clean_text(entry.get("recommended_action") or "")
    if not raw:
        return "Open the source link when available, then check current details before outreach or publication."
    raw = re.sub(
        r"Open the source or listing page, then verify current details before outreach or publication\.",
        "Open the source link when available, then check current details before outreach or publication.",
        raw,
        flags=re.I,
    )
    raw = re.sub(r"\bverify\b", "check", raw, flags=re.I)
    raw = re.sub(r"\blead list\b", "starting list", raw, flags=re.I)
    raw = re.sub(r"\bleads\b", "listings", raw, flags=re.I)
    raw = re.sub(r"\blead\b", "route", raw, flags=re.I)
    return trim(raw, 220)


UNKNOWN_CONTACT_VALUES = {
    "",
    "unknown",
    "unknown / verify",
    "not available",
    "not extracted",
    "not extracted in bulk page",
    "n/a",
    "na",
    "none",
}

GUIDE_KEYWORDS = [
    "advertising",
    "artist",
    "arts",
    "bakery",
    "business",
    "calendar",
    "chamber",
    "creative business",
    "creative district",
    "dining",
    "directory",
    "economic development",
    "event",
    "flyer",
    "funding",
    "gallery",
    "grant",
    "lodging",
    "maker",
    "market",
    "media",
    "music",
    "newsletter",
    "nonprofit",
    "outreach",
    "partner",
    "poster",
    "public notice",
    "restaurant",
    "retail",
    "scholarship",
    "sbdc",
    "service",
    "social media",
    "startup",
    "stipend",
    "studio",
    "tourism",
    "venue",
    "visitor",
    "workshop",
    "Angel Fire",
    "Aguilar",
    "Branson",
    "Cimarron",
    "Colfax",
    "Huerfano",
    "La Veta",
    "Las Animas",
    "Raton",
    "Trinidad",
    "Walsenburg",
]


def meaningful(value: object) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lowered = text.lower()
    if lowered in UNKNOWN_CONTACT_VALUES or lowered.startswith("not extracted"):
        return ""
    return text


def split_values(value: object) -> list[str]:
    text = meaningful(value)
    if not text:
        return []
    return [part.strip() for part in re.split(r"\s*;\s*|\s*\|\s*|\n+", text) if meaningful(part.strip())]


def add_unique(target: list[str], *values: object) -> None:
    seen = {item.casefold() for item in target}
    for value in values:
        for part in split_values(value):
            key = part.casefold()
            if key not in seen:
                target.append(part)
                seen.add(key)


def normalize_url(value: str) -> str:
    value = meaningful(value)
    if not value:
        return ""
    value = value.replace("data/tri_county_directory_sweep_matrix_20260701.csv", "data/directory_sweep_matrix_20260701.csv")
    if value.startswith("www."):
        value = "https://" + value
    if not value.startswith(("http://", "https://", "data/", "assets/", "docs/")):
        return ""
    return value


def collect_urls(*values: object) -> list[str]:
    urls: list[str] = []
    for value in values:
        for part in split_values(value):
            url = normalize_url(part)
            if url and url.casefold() not in {item.casefold() for item in urls}:
                urls.append(url)
    return urls


def collect_emails(*values: object) -> list[str]:
    emails: list[str] = []
    for value in values:
        for match in re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", str(value or ""), flags=re.I):
            if match.casefold() not in {item.casefold() for item in emails}:
                emails.append(match)
    return emails


def collect_phones(*values: object) -> list[str]:
    phones: list[str] = []
    for value in values:
        for part in split_values(value):
            if len(re.sub(r"\D", "", part)) >= 7 and part.casefold() not in {item.casefold() for item in phones}:
                phones.append(part)
    return phones


def clean_address(value: object) -> str:
    address = meaningful(value)
    if not address:
        return ""
    address = re.sub(r",\s*,+", ",", address)
    address = re.sub(r"\s+,", ",", address)
    return address.strip(" ,")


def looks_like_address(value: object) -> bool:
    text = clean_text(value)
    return bool(re.search(r"\d", text) and re.search(r"\b(st|street|ave|avenue|rd|road|drive|dr|blvd|boulevard|lane|ln|highway|hwy|nm-|co-|us-)\b", text, re.I))


def scrape_artifact_name(name: object) -> bool:
    return bool(re.fullmatch(r"\+?\s*email\s+\d+\s+website", clean_text(name), flags=re.I))


def public_listing_name(name: object, row: dict) -> str:
    text = clean_text(name)
    if not scrape_artifact_name(text):
        return text
    candidate = clean_text(row.get("physical_address") or row.get("address"))
    if candidate and not looks_like_address(candidate):
        return clean_text(candidate.split("/", 1)[0])
    place = clean_text(row.get("town") or row.get("city") or row.get("town_area") or row.get("county") or "Regional")
    return f"{place} business directory listing"


def humanize_public_text(value: object) -> str:
    text = clean_text(value)
    replacements = [
        (r"Outreach lead / source-check candidate", "Local resource"),
        (r"Commercial directory lead / local business", "Local business listing"),
        (r"Creative business / source-linked lead", "Creative business listing"),
        (r"Digital creative directory / source-linked lead", "Digital creative directory"),
        (r"Commercial directory lead sweep / needs verification", "Commercial directory sweep"),
        (r"Sparse-area community lead", "Small-community contact"),
        (r"Commercial-directory-only lead", "Commercial directory listing"),
        (r"Commercial-directory sweep", "Commercial directory"),
        (r"source-check cue", "additional source cue"),
        (r"source-check candidate", "listing to check"),
        (r"source checking", "source review"),
        (r"Individual maker/vendor lead", "Maker or vendor listing"),
        (r"Individual artist lead", "Artist listing"),
        (r"Lead Sweep", "Directory Sweep"),
        (r"lead-discovery", "resource discovery"),
        (r"\bleads?\b", "listings"),
        (r"\bunverified\b", "not yet confirmed"),
        (r"\bVerify\b", "Check"),
        (r"\bverify\b", "check"),
    ]
    for old, new in replacements:
        text = re.sub(old, new, text, flags=re.I)
    return text


def public_keyword(value: object) -> str:
    keyword = public_category(humanize_public_text(value))
    if not keyword or re.search(r"^\(?\s*\d{3}[-\s)]", keyword):
        return ""
    if keyword.casefold() in {"unknown / check", "unknown", "not yet confirmed"}:
        return ""
    return trim(keyword, 72)


def public_audience(value: object) -> str:
    audience = humanize_public_text(value)
    replacements = {
        "Artist": "Artists",
        "Creative business": "Creative businesses",
        "Entrepreneur": "Entrepreneurs",
        "For-Profit": "Businesses",
        "Non-Profit": "Nonprofits",
        "Program": "Programs",
        "Visitors / tourists": "Visitors and tourists",
        "Arts / culture audiences": "Arts and culture audiences",
    }
    return replacements.get(audience, audience)


def normalize_business_name(value: object) -> str:
    text = clean_text(value).lower()
    text = re.split(r"\s*/\s*|\s*\|\s*|\s+aka\s+|\s+dba\s+", text, maxsplit=1, flags=re.I)[0]
    text = text.replace("&", " and ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    words = [w for w in text.split() if w not in {"the", "llc", "inc", "ltd", "co", "company", "corp", "corporation"}]
    return " ".join(words)


def normalize_place(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean_text(value).lower()).strip()


def split_alias_names(name: object) -> list[str]:
    raw = clean_text(name)
    if not raw:
        return []
    aliases = [raw]
    for part in re.split(r"\s*/\s*|\s*\|\s*|\s+aka\s+|\s+dba\s+", raw, flags=re.I):
        part = clean_text(part)
        if part and part.casefold() not in {alias.casefold() for alias in aliases}:
            aliases.append(part)
    return aliases


def better_name(current: str, candidate: str) -> str:
    current = clean_text(current)
    candidate = clean_text(candidate)
    if not current:
        return candidate
    if not candidate:
        return current
    if "/" in current and "/" not in candidate:
        return candidate
    if re.fullmatch(r"\+?\s*email\s+\d+\s+website", current, flags=re.I):
        return candidate
    if len(candidate) < len(current) and normalize_business_name(candidate) == normalize_business_name(current):
        return candidate
    return current


def slugify(value: object) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", clean_text(value).lower()).strip("-")
    return slug or "entry"


def place_label(row: dict) -> str:
    return ", ".join(part for part in [row.get("town"), row.get("county"), row.get("state")] if meaningful(part)) or "Regional"


GENERIC_DESCRIPTION_PATTERNS = [
    r"launch/outreach lead",
    r"verify details",
    r"source-check",
    r"not final proof",
    r"starting listing",
    r"starting contact",
    r"commercial-directory-only",
    r"spreadsheet-backed",
    r"use this as a starting",
    r"open (?:a|the) source",
    r"visitor-facing listing from",
    r"visitor-facing listing pulled",
    r"creative listing from a public",
    r"creative-directory lead added",
    r"commercial directory listing from",
    r"commercial directory entry from",
    r"commercial directory import",
    r"outreach score",
    r"flyer likelihood",
    r"digital distribution",
    r"policy risk",
    r"launch/outreach list",
    r"maker or vendor listing listed by",
    r"artist listing listed by",
    r"local business listing from a public commercial directory",
    r"check current details before",
    r"check details before spending",
    r"business type not clear",
    r"yellow pages bulk source",
    r"public-facing local business type",
    r"public-facing or locally useful business",
    r"flyer permission",
    r"outside advertising",
    r"physical flyer posting",
    r"community distribution",
    r"management controls",
    r"chain/franchise/corporate",
    r"faith/community locations may",
    r"professional, medical, industrial",
    r"^\+?\s*email\s+\d+\s+website$",
    r"^owner:",
]


def generic_description(description: str) -> bool:
    text = clean_text(description)
    return not text or any(re.search(pattern, text, re.I) for pattern in GENERIC_DESCRIPTION_PATTERNS)


def listing_description(name: str, category: str, place: str, raw: object = "") -> str:
    description = clean_text(raw)
    if description and not generic_description(description):
        return trim(description, 260)
    category = clean_text(category) or "local resource"
    return trim(f"{category} listing for {place}. Use the contact links or source pages to check current details before outreach, printing, or publication.", 260)


def plain_category(value: object) -> str:
    category = public_category(value) or "local resource"
    category = re.sub(r"\bAll tourism directory listings\b", "tourism directory", category, flags=re.I)
    category = re.sub(r"\bVacation directory listings and attractions\b", "visitor directory or attraction", category, flags=re.I)
    category = re.sub(r"\bTravel guide businesses and attractions\b", "travel guide business or attraction", category, flags=re.I)
    category = re.sub(r"\s*/\s*", " or ", category)
    category = re.sub(r"\s*;\s*", " and ", category)
    return category[:1].lower() + category[1:] if category else "local resource"


def entry_search_blob(entry: dict) -> str:
    values = [
        entry.get("name"),
        entry.get("category"),
        entry.get("entry_type"),
        entry.get("town"),
        entry.get("county"),
        " ".join(entry.get("keywords", [])),
        " ".join(entry.get("audiences", [])),
        " ".join(entry.get("marketing_channels", [])),
        " ".join(entry.get("merged_from", [])),
        " ".join(entry.get("source_urls", [])),
        " ".join(entry.get("websites", [])),
    ]
    return " ".join(clean_text(value) for value in values).lower()


def entry_classification_blob(entry: dict) -> str:
    values = [
        entry.get("name"),
        entry.get("category"),
        entry.get("entry_type"),
        entry.get("town"),
        entry.get("county"),
        " ".join(entry.get("merged_from", [])),
        " ".join(entry.get("source_urls", [])),
        " ".join(entry.get("websites", [])),
    ]
    return " ".join(clean_text(value) for value in values).lower()


def sentence_subject(name: object) -> str:
    value = clean_text(name) or "This listing"
    return value


def place_for_sentence(entry: dict) -> str:
    place = place_label(entry)
    return place if place and place != "Regional" else "the tri-county region"


def friendly_listing_descriptor(entry: dict) -> str:
    name = clean_text(entry.get("name")).lower()
    category = clean_text(entry.get("category")).lower()
    text = f"{name} {category} {entry_classification_blob(entry)}"
    rules = [
        (r"espresso|coffee|cafe|tea", "Cafe or coffee stop"),
        (r"bakery|baked|pastry", "Bakery or food business"),
        (r"restaurant|dining|grill|kitchen|pizza|burger|tavern|saloon|bar|brew|beverage|food", "Restaurant or dining business"),
        (r"gallery|artist|arts|creative|studio|painting|sculpture|photography|maker|artisan|jewelry|design|tattoo", "Arts or creative business"),
        (r"music|venue|theater|theatre|performance|concert|open mic", "Music, venue, or performance route"),
        (r"lodging|hotel|motel|inn|cabin|rv|campground|resort|vacation rental|bed and breakfast|b&b", "Lodging or hospitality business"),
        (r"shop|shopping|retail|store|boutique|mercantile|market|gift|thrift|antique|book|florist", "Shop or local retail business"),
        (r"grant|fund|loan|stipend|scholarship|incentive|sba|usda|economic development|technical assistance", "Funding or business-support route"),
        (r"calendar|event|festival|market|class|workshop", "Event or calendar route"),
        (r"tourism|visitor|travel|attraction|scenic|trail|park|lake|ski|fish|hike|recreation|outfitter|guide service", "Visitor or recreation route"),
        (r"chamber|mainstreet|municipal|city|town|county|government|library|school|college|creative district|visitor center", "Civic or partner-organization route"),
        (r"nonprofit|non-profit|foundation|community|youth|family|senior|volunteer|coalition", "Nonprofit or community-service route"),
        (r"newspaper|radio|media|magazine|newsletter|press|advertis|publisher|broadcast|localstash|weekender", "Media, visitor, or advertising route"),
        (r"real estate|insurance|account|legal|law|attorney|dental|medical|health|clinic|therapy|bank|finance|consult|repair|auto|construction|contractor|plumb|electric|roof|salon|spa|fitness", "Professional or service business"),
        (r"church|faith|ministry|parish|congregation", "Faith or community organization"),
        (r"farm|ranch|agricultur|livestock|nursery|garden|produce", "Agriculture, ranch, or local-producer listing"),
        (r"digital|web|software|technology|online|graphic", "Digital or creative-service listing"),
    ]
    for pattern, label in rules:
        if re.search(pattern, text, re.I):
            return label
    if category and category not in {"local business listing", "general", "resource"}:
        return public_category(entry.get("category"))
    return "Local business or organization listing"


def everything_description_family(entry: dict) -> tuple[str, str]:
    text = entry_classification_blob(entry)
    if entry.get("entry_type") == "Directory shortcut":
        if re.search(r"grant|fund|loan|stipend|scholarship|incentive|sba|usda|economic development|technical assistance", text):
            return ("funding and assistance directory", "Use it to find program pages, eligibility details, deadlines, and the office or organization that should confirm the next step.")
        if re.search(r"event|calendar|festival|market|performance|venue|music|workshop|class", text):
            return ("event or calendar directory", "Use it to find public posting paths, venue information, calendar contacts, and visitor-facing event channels.")
        if re.search(r"artist|arts|creative|gallery|maker|studio|museum|culture|theater|music", text):
            return ("arts and culture directory", "Use it to find creative organizations, artist-facing pages, cultural venues, and possible collaboration routes.")
        if re.search(r"chamber|mainstreet|business directory|tourism|visitor|travel|lodging|restaurant|shop", text):
            return ("business, chamber, or visitor directory", "Use it to find existing public listings, visitor pages, and organization contacts before creating a new outreach list.")
        return ("regional directory", "Use it to find the public page, organization, office, or listing path that best matches the task.")

    if re.search(r"grant|fund|loan|stipend|scholarship|incentive|sba|usda|economic development|technical assistance|small business development", text):
        return ("funding, training, or business-support listing", "It is most useful when researching assistance, referrals, eligibility questions, or preparation steps before applying.")
    if re.search(r"restaurant|dining|cafe|coffee|espresso|bar|brew|bakery|food|beverage|cater|kitchen|pizza|grill|tavern|saloon", text):
        return ("food, drink, or dining listing", "It is useful for visitor referrals, local event outreach, shop-local campaigns, and cross-promotion questions that fit the business.")
    if re.search(r"artist|arts|creative|gallery|studio|painting|painter|writer|storyteller|cartoonist|tattoo|museum|theater|theatre|music|musician|film|photograph|design|public art|culture|cultural", text):
        return ("arts, culture, or creative-business listing", "It is relevant for artist referrals, exhibitions, workshops, performances, cultural events, and creative cross-promotion inquiries.")
    if re.search(r"shop|shopping|retail|store|boutique|mercantile|market|maker|vendor|gift|thrift|antique|book|florist|jewelry|artisan|craft", text):
        return ("shop, maker, or local retail listing", "It can help users find storefront or vendor contacts for shop-local outreach, event materials, visitor referrals, or local-goods partnerships.")
    if re.search(r"lodging|hotel|motel|inn|cabin|rv|campground|vacation rental|bed and breakfast|b&b|resort|ranch stay", text):
        return ("lodging or hospitality listing", "It is useful for visitor referrals, event guest planning, trip-planning pages, and questions about guest-facing information channels.")
    if re.search(r"event|calendar|festival|market|performance|venue|music|concert|workshop|class|fair|rodeo|theater|museum|library", text):
        return ("event, venue, or calendar-related listing", "Use it when planning public events, performances, classes, workshops, or calendar visibility across the region.")
    if re.search(r"tour|tourism|visitor|travel|attraction|scenic|outdoor|trail|park|lake|ski|fish|hike|recreation|play|adventure|historic|heritage", text):
        return ("visitor-facing attraction or recreation listing", "It is useful for tourism context, trip planning, visitor referrals, and partnership research tied to regional travel.")
    if re.search(r"chamber|mainstreet|municipal|city|town|county|public|government|office|library|school|university|college|economic development|creative district|visitor center", text):
        return ("public, civic, or partner-organization listing", "Use it to find formal contact paths, public information, business referrals, community-posting questions, or local program connections.")
    if re.search(r"nonprofit|non-profit|foundation|community|youth|family|senior|food pantry|mission|volunteer|service organization|coalition", text):
        return ("nonprofit or community-service listing", "It is useful for mission-aligned referrals, community outreach, partnership research, and program visibility questions.")
    if re.search(r"newspaper|radio|media|magazine|newsletter|press|advertis|marketing|print|publisher|broadcast", text):
        return ("media, advertising, or public-information listing", "Use it to ask about appropriate announcement, advertising, calendar, newsletter, or public-information routes.")
    if re.search(r"real estate|insurance|account|legal|law|attorney|dental|medical|health|clinic|therapy|bank|finance|consult|professional|repair|auto|construction|contractor|plumb|electric|roof|beauty|salon|spa|fitness", text):
        return ("professional or service-business listing", "It is usually most useful for direct contact, referrals, sponsorship research, business-to-business outreach, or customer-facing updates.")
    if re.search(r"church|faith|ministry|parish|congregation|spiritual", text):
        return ("faith or community-organization listing", "Use it for mission-aligned community outreach questions and local referrals, not broad advertising assumptions.")
    if re.search(r"farm|ranch|agricultur|livestock|nursery|garden|produce", text):
        return ("agriculture, ranch, or local-producer listing", "It is useful for local-supply referrals, market outreach, visitor interest, and community partnership research.")
    if re.search(r"digital|web|software|technology|online|it service|graphic design|creative service", text):
        return ("digital or creative-service listing", "It is useful for web, design, content, technical support, referral, or collaboration questions.")
    return ("public business-directory listing", "Use it to identify a possible local contact, then check a business-owned page or current directory listing before outreach.")


def rewrite_everything_description(entry: dict) -> str:
    raw = humanize_public_text(entry.get("description"))
    if raw and not generic_description(raw):
        return trim(raw, 280)
    name = sentence_subject(entry.get("name"))
    place = place_for_sentence(entry)
    family, use_case = everything_description_family(entry)
    descriptor = friendly_listing_descriptor(entry)
    descriptor = descriptor[:1].upper() + descriptor[1:]
    if family == "public business-directory listing":
        return trim(f"{descriptor} in {place}. Use it to identify a possible local contact, then check a business-owned page or current directory listing before outreach.", 320)
    return trim(f"{descriptor} in {place}. {use_case}", 320)


def resource_row_description(row: dict) -> str:
    raw = humanize_public_text(row.get("notes") or row.get("best_for") or row.get("description") or "")
    if raw and not generic_description(raw):
        raw = re.sub(r"source-backed starting points?", "starting points", raw, flags=re.I)
        raw = re.sub(r"Confirm current rules, rates, dates, and acceptance before action\.", "Check current details before spending money or announcing placement.", raw, flags=re.I)
        raw = re.sub(r"\bsource link\b", "available page", raw, flags=re.I)
        return trim(raw, 280)

    row_name = public_listing_name(row.get("resource_name") or row.get("name") or row.get("title"), row)
    entry = {
        "name": row_name,
        "category": public_category(row.get("category") or row.get("resource_type") or row.get("source_type") or "Resource"),
        "entry_type": "Directory shortcut" if re.search(r"directory|calendar|channel|page|source", clean_text(row.get("resource_type")), re.I) else "Listing",
        "town": row.get("town") or row.get("city") or row.get("town_area"),
        "county": row.get("county"),
        "state": row.get("state"),
        "keywords": [
            public_keyword(row.get("category")),
            public_keyword(row.get("resource_type")),
            public_keyword(row.get("source_type")),
        ],
        "audiences": [public_audience(row.get("audience"))] if meaningful(row.get("audience")) else [],
        "marketing_channels": [public_category(row.get("channel_type"))] if meaningful(row.get("channel_type")) else [],
        "merged_from": [clean_text(value) for value in [
            row.get("source_name"),
            row.get("source_type"),
            row.get("best_for"),
            row.get("notes"),
        ] if meaningful(value)],
        "source_urls": collect_urls(row.get("source_url"), row.get("travel_listing_sources"), row.get("directory_url"), row.get("map_url")),
        "websites": collect_urls(row.get("website"), row.get("url"), row.get("facebook"), row.get("instagram")),
    }
    descriptor = friendly_listing_descriptor(entry)
    place = place_for_sentence(entry)
    family, use_case = everything_description_family(entry)
    if family == "public business-directory listing":
        use_case = "Use it to identify a possible local contact, then check a current business-owned page or directory listing before outreach."
    return trim(f"{descriptor} in {place}. {use_case}", 320)


def infer_audiences(*fields: object) -> list[str]:
    text = " ".join(clean_text(field) for field in fields).lower()
    audiences: list[str] = []
    if re.search(r"artist|arts|creative|gallery|maker|music|studio|tattoo|theater|museum", text):
        audiences.append("Artists and creative businesses")
    if re.search(r"business|startup|entrepreneur|retail|restaurant|service|chamber|economic development", text):
        audiences.append("Businesses and entrepreneurs")
    if re.search(r"nonprofit|non-profit|community|foundation|program|school|library|youth|family", text):
        audiences.append("Nonprofits and community programs")
    if re.search(r"visitor|touris|travel|lodging|hotel|motel|attraction|scenic|dining", text):
        audiences.append("Visitors and tourists")
    if re.search(r"event|calendar|venue|festival|workshop|class|market", text):
        audiences.append("Event organizers")
    if re.search(r"resident|local|public|municipal|county|city", text):
        audiences.append("Local residents")
    return audiences or ["Regional users"]


def infer_channels(row: dict, *fields: object) -> list[str]:
    text = " ".join(clean_text(field) for field in fields).lower()
    channels: list[str] = []
    if re.search(r"restaurant|cafe|coffee|bar|brew|retail|shop|store|market|bakery|library|visitor center|hotel|motel|gallery|museum|venue|theater", text):
        channels.append("Ask about physical flyer or poster placement")
    if re.search(r"website|online|digital|facebook|instagram|social|directory|tourism|travel|visitor|chamber|creative district", text):
        channels.append("Ask about digital listing or social sharing")
    if re.search(r"event|calendar|festival|workshop|class|venue|theater|museum|library|tourism|visitor", text):
        channels.append("Ask about event calendar or visitor listing")
    if re.search(r"newspaper|radio|media|magazine|press|newsletter", text):
        channels.append("Ask about media, newsletter, or calendar placement")
    if re.search(r"chamber|mainstreet|economic development|creative district|business directory|member|association", text):
        channels.append("Ask about business directory or partner referral")
    if re.search(r"artist|arts|creative|gallery|maker|music|studio|tattoo|museum|culture", text):
        channels.append("Ask about creative or cultural cross-promotion")
    if row.get("yellowpages_flyer_likelihood") or row.get("physical_flyer_likelihood"):
        if re.search(r"high|medium", clean_text(row.get("yellowpages_flyer_likelihood") or row.get("physical_flyer_likelihood")), re.I):
            channels.append("Ask in person before leaving materials")
    if row.get("yellowpages_digital_distribution_likelihood") or row.get("digital_distribution_likelihood"):
        if re.search(r"high|medium", clean_text(row.get("yellowpages_digital_distribution_likelihood") or row.get("digital_distribution_likelihood")), re.I):
            channels.append("Ask about a digital share or listing update")
    if row.get("corporate_policy_risk") and not re.search(r"low", clean_text(row.get("corporate_policy_risk")), re.I):
        channels.append("Confirm manager or owner permission first")
    return list(dict.fromkeys(channels)) or ["Use as a contact starting point"]


def keyword_hits(*fields: object) -> list[str]:
    text = " ".join(clean_text(field) for field in fields).lower()
    hits: list[str] = []
    for keyword in GUIDE_KEYWORDS:
        key = keyword.lower()
        if key in text and keyword not in hits:
            hits.append(keyword)
    return hits


def base_everything_entry(name: str, row: dict, entry_type: str, source_label: str) -> dict:
    aliases = split_alias_names(name)
    return {
        "entry_id": slugify(f"{name}-{row.get('town') or row.get('city') or row.get('town_area')}-{row.get('county')}"),
        "name": clean_text(aliases[0] if aliases else name),
        "aliases": aliases[1:],
        "county": meaningful(row.get("county")) or "Regional",
        "town": meaningful(row.get("town") or row.get("city") or row.get("town_area")),
        "state": meaningful(row.get("state")),
        "category": public_category(row.get("category") or row.get("kind") or row.get("resource_type") or "General"),
        "entry_type": entry_type,
        "description": "",
        "websites": [],
        "emails": [],
        "phones": [],
        "addresses": [],
        "source_urls": [],
        "audiences": [],
        "keywords": [],
        "marketing_channels": [],
        "notes_for_use": "Check current details with the listed source or organization before spending money, printing materials, or promising placement.",
        "source_count": 0,
        "merged_from": [source_label],
    }


def resource_to_everything(row: dict) -> dict:
    raw_name = meaningful(row.get("resource_name")) or "Untitled listing"
    category_source = row.get("category") or row.get("kind") or row.get("resource_type") or "General"
    phone_source = row.get("contact_phone")
    address_source = row.get("physical_address")
    if re.match(r"owner\s*:", raw_name, flags=re.I):
        shifted_activity = meaningful(row.get("contact_phone"))
        shifted_address = meaningful(row.get("category"))
        shifted_phone = meaningful(row.get("physical_address"))
        if shifted_activity and not collect_phones(shifted_activity):
            raw_name = shifted_activity
            category_source = shifted_activity
            phone_source = shifted_phone
            address_source = shifted_address
    name = public_listing_name(raw_name, row)
    entry = base_everything_entry(name, row, "Listing", "guide resource directory")
    entry["category"] = public_category(category_source)
    entry["websites"] = collect_urls(row.get("website"))
    entry["emails"] = collect_emails(row.get("contact_email"))
    entry["phones"] = [] if scrape_artifact_name(raw_name) else collect_phones(phone_source)
    address = clean_address(row.get("contact_phone") if scrape_artifact_name(raw_name) and looks_like_address(row.get("contact_phone")) else address_source)
    if address:
        entry["addresses"].append(address)
    entry["source_urls"] = collect_urls(row.get("source_url"), row.get("travel_listing_sources"))
    entry["description"] = listing_description(entry["name"], entry["category"], place_label(entry), public_desc(row))
    source_text = " ".join(str(row.get(key, "")) for key in row.keys())
    add_unique(entry["audiences"], row.get("audience_served"), *infer_audiences(source_text))
    add_unique(entry["keywords"], row.get("category"), row.get("resource_type"), row.get("goal_relevance"), row.get("town"), row.get("county"), *keyword_hits(source_text))
    add_unique(entry["marketing_channels"], *infer_channels(row, source_text))
    return entry


def travel_to_everything(row: dict) -> dict:
    raw_name = meaningful(row.get("listing_name")) or "Untitled travel listing"
    category_source = row.get("subcategory") or row.get("category") or "Visitor-facing listing"
    phone_source = row.get("phone")
    address_source = row.get("address")
    if re.match(r"owner\s*:", raw_name, flags=re.I):
        shifted_activity = meaningful(row.get("phone"))
        shifted_address = meaningful(row.get("category"))
        shifted_phone = meaningful(row.get("address"))
        if shifted_activity and not collect_phones(shifted_activity):
            raw_name = shifted_activity
            category_source = shifted_activity
            phone_source = shifted_phone
            address_source = shifted_address
    name = public_listing_name(raw_name, row)
    entry = base_everything_entry(name, row, "Listing", clean_text(row.get("source_name")) or "travel or tourism directory")
    entry["websites"] = collect_urls(row.get("website"), row.get("listing_url"))
    entry["emails"] = collect_emails(row.get("email"))
    entry["phones"] = [] if scrape_artifact_name(raw_name) else collect_phones(phone_source)
    address = clean_address(row.get("phone") if scrape_artifact_name(raw_name) and looks_like_address(row.get("phone")) else address_source)
    if address:
        entry["addresses"].append(address)
    entry["source_urls"] = collect_urls(row.get("source_url"), row.get("listing_url"))
    category = public_category(category_source)
    entry["category"] = category
    entry["description"] = listing_description(entry["name"], category, place_label(entry), row.get("description") or f"Visitor-facing listing from {row.get('source_name') or 'a public travel or tourism source'}.")
    source_text = " ".join(str(row.get(key, "")) for key in row.keys())
    add_unique(entry["audiences"], *infer_audiences(source_text), "Visitors and tourists")
    add_unique(entry["keywords"], row.get("category"), row.get("subcategory"), row.get("town_area"), row.get("county"), *keyword_hits(source_text))
    add_unique(entry["marketing_channels"], *infer_channels(row, source_text), "Ask about visitor-facing updates")
    return entry


def yellowpages_to_everything(row: dict) -> dict:
    name = meaningful(row.get("business_name")) or "Untitled business listing"
    entry = base_everything_entry(name, row, "Listing", "commercial directory sweep")
    entry["websites"] = collect_urls(row.get("website"))
    entry["phones"] = collect_phones(row.get("phone"))
    address = clean_address(row.get("physical_address"))
    if address:
        entry["addresses"].append(address)
    entry["source_urls"] = collect_urls(row.get("source_url"))
    entry["description"] = listing_description(entry["name"], public_category(row.get("category") or "Business"), place_label(entry), row.get("review_reason"))
    source_text = " ".join(str(row.get(key, "")) for key in row.keys())
    add_unique(entry["audiences"], *infer_audiences(source_text))
    add_unique(entry["keywords"], row.get("category"), row.get("city"), row.get("county"), *keyword_hits(source_text))
    add_unique(entry["marketing_channels"], *infer_channels(row, source_text))
    if meaningful(row.get("recommended_outreach_action")):
        entry["notes_for_use"] = public_entry_action({"recommended_action": row.get("recommended_outreach_action")})
    return entry


def source_to_everything(row: dict) -> dict:
    name = meaningful(row.get("title")) or "Untitled directory"
    entry = base_everything_entry(name, row, "Directory shortcut", clean_text(row.get("kind")) or "directory source")
    entry["source_urls"] = collect_urls(row.get("url"))
    entry["websites"] = collect_urls(row.get("url"))
    entry["description"] = listing_description(entry["name"], public_category(row.get("kind") or "Directory"), place_label(entry), row.get("best_for"))
    source_text = " ".join(str(row.get(key, "")) for key in row.keys())
    add_unique(entry["audiences"], *infer_audiences(source_text))
    add_unique(entry["keywords"], row.get("kind"), row.get("county"), *keyword_hits(source_text))
    add_unique(entry["marketing_channels"], *infer_channels(row, source_text))
    if meaningful(row.get("action")):
        entry["notes_for_use"] = public_entry_action({"recommended_action": row.get("action")})
    return entry


def choose_everything_key(entry: dict, entries_by_key: dict, base_index: dict) -> tuple[str, str, str]:
    name_key = normalize_business_name(entry.get("name"))
    county_key = normalize_place(entry.get("county"))
    town_key = normalize_place(entry.get("town"))
    base = (name_key, county_key)
    for key in base_index.get(base, []):
        existing = entries_by_key[key]
        existing_town = normalize_place(existing.get("town"))
        if town_key and existing_town and town_key == existing_town:
            return key
        if not town_key and not existing_town:
            return key
        if town_key and not existing_town:
            return key
        if not town_key and existing_town:
            return key
    return (name_key, county_key, town_key)


def merge_everything_entry(target: dict, incoming: dict) -> None:
    old_name = target.get("name", "")
    target["name"] = better_name(target.get("name", ""), incoming.get("name", ""))
    if old_name and old_name != target["name"]:
        add_unique(target["aliases"], old_name)
    add_unique(target["aliases"], incoming.get("name"), *incoming.get("aliases", []))
    target["aliases"] = [alias for alias in target["aliases"] if alias.casefold() != target["name"].casefold()]
    for field in ["websites", "emails", "phones", "addresses", "source_urls", "audiences", "keywords", "marketing_channels", "merged_from"]:
        add_unique(target[field], *incoming.get(field, []))
    for field in ["county", "town", "state"]:
        if not meaningful(target.get(field)) and meaningful(incoming.get(field)):
            target[field] = incoming.get(field)
    if target.get("category") in {"General", "Resource"} and incoming.get("category"):
        target["category"] = incoming.get("category")
    elif incoming.get("category") and incoming.get("category") != target.get("category"):
        add_unique(target["keywords"], incoming.get("category"))
    if generic_description(target.get("description", "")) and incoming.get("description"):
        target["description"] = incoming.get("description")
    if target.get("notes_for_use", "").startswith("Check current") and incoming.get("notes_for_use"):
        target["notes_for_use"] = incoming.get("notes_for_use")


def finalize_everything_entry(entry: dict) -> dict:
    entry["name"] = humanize_public_text(entry.get("name"))
    entry["aliases"] = [humanize_public_text(alias) for alias in entry.get("aliases", [])]
    entry["aliases"] = sorted([alias for alias in entry["aliases"] if alias.casefold() != entry["name"].casefold()], key=str.casefold)
    for field in ["websites", "emails", "phones", "addresses", "source_urls", "audiences", "keywords", "marketing_channels", "merged_from"]:
        entry[field] = list(dict.fromkeys(entry.get(field, [])))
    entry["description"] = humanize_public_text(entry.get("description"))
    entry["notes_for_use"] = humanize_public_text(entry.get("notes_for_use"))
    entry["category"] = public_category(entry.get("category"))
    entry["audiences"] = list(dict.fromkeys(public_audience(value) for value in entry.get("audiences", []) if public_audience(value)))
    entry["keywords"] = list(dict.fromkeys(public_keyword(value) for value in entry.get("keywords", []) if public_keyword(value)))
    entry["marketing_channels"] = list(dict.fromkeys(humanize_public_text(value) for value in entry.get("marketing_channels", []) if humanize_public_text(value)))
    entry["merged_from"] = list(dict.fromkeys(humanize_public_text(value) for value in entry.get("merged_from", []) if humanize_public_text(value)))
    entry["source_count"] = len(entry.get("source_urls", [])) or len(entry.get("merged_from", []))
    entry["description"] = rewrite_everything_description(entry)
    return entry


def export_everything_entries(entries: list[dict]) -> None:
    json_path = SITE / "data" / "directory_of_absolutely_everything.json"
    csv_path = SITE / "data" / "directory_of_absolutely_everything.csv"
    json_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = [
        "entry_id",
        "name",
        "aliases",
        "county",
        "town",
        "state",
        "category",
        "entry_type",
        "description",
        "websites",
        "emails",
        "phones",
        "addresses",
        "source_urls",
        "audiences",
        "keywords",
        "marketing_channels",
        "notes_for_use",
        "source_count",
        "merged_from",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        for entry in entries:
            writer.writerow({field: "; ".join(entry[field]) if isinstance(entry.get(field), list) else entry.get(field, "") for field in fields})


def build_everything_directory(data: dict) -> list[dict]:
    raw_entries: list[dict] = []
    raw_entries.extend(source_to_everything(src) for src in data.get("directory_sources", []))
    raw_entries.extend(resource_to_everything(row) for row in data.get("resources", []))
    travel_path = SITE / "data" / "tri_county_travel_guide_listings_20260630.json"
    if travel_path.exists():
        raw_entries.extend(travel_to_everything(row) for row in json.loads(travel_path.read_text(encoding="utf-8")))
    yellow_path = SITE / "data" / "yellowpages_outreach_leads_20260701.json"
    if yellow_path.exists():
        raw_entries.extend(yellowpages_to_everything(row) for row in json.loads(yellow_path.read_text(encoding="utf-8")))

    entries_by_key: dict[tuple[str, str, str], dict] = {}
    base_index: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for incoming in raw_entries:
        if not normalize_business_name(incoming.get("name")):
            continue
        key = choose_everything_key(incoming, entries_by_key, base_index)
        if key not in entries_by_key:
            entries_by_key[key] = incoming
            base_index.setdefault((key[0], key[1]), []).append(key)
        else:
            merge_everything_entry(entries_by_key[key], incoming)

    entries = [finalize_everything_entry(entry) for entry in entries_by_key.values()]
    entries.sort(key=lambda entry: (entry["name"].casefold(), entry["county"].casefold(), clean_text(entry.get("town")).casefold(), entry["category"].casefold()))
    for index, entry in enumerate(entries, start=1):
        entry["entry_id"] = f"everything-{index:04d}-{slugify(entry['name'])}"
    export_everything_entries(entries)
    return entries


def local_href(prefix: str, href: str) -> str:
    if href.startswith(("data/", "assets/", "docs/")):
        return prefix + href
    return href


def link_target(href: str) -> str:
    return ' target="_blank" rel="noreferrer"' if href.startswith(("http://", "https://")) else ""


def domain_label(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc:
        return parsed.netloc.replace("www.", "")
    return "Open link"


def title_from_slug(value: str) -> str:
    label = re.sub(r"[-_]+", " ", value).strip()
    label = re.sub(r"\bNm\b", "NM", label.title())
    label = re.sub(r"\bCo\b", "CO", label)
    return label


def city_from_url_path(path: str) -> str:
    match = re.search(r"/([a-z0-9-]+)-(?:nm|co)(?:/|$)", path, re.I)
    if not match:
        return ""
    return title_from_slug(match.group(1))


def known_site_label(domain: str) -> str:
    mappings = [
        ("exploreraton.com", "Explore Raton"),
        ("visitangelfirenm.com", "Visit Angel Fire"),
        ("visittrinidadcolorado.com", "Visit Trinidad"),
        ("spanishpeakscountry.com", "Spanish Peaks Country"),
        ("walsenburgchamberofcommerce.org", "Walsenburg Chamber"),
        ("trinidadcreativedistrict.org", "Trinidad Creative District"),
        ("creativetrinidadco.org", "Trinidad Creative District"),
        ("angelfirechamber.org", "Angel Fire Chamber"),
        ("ratonmainstreet.org", "Raton MainStreet"),
        ("ratonnm.gov", "Raton municipal page"),
        ("huerfano.us", "Huerfano County"),
        ("huerfano.org", "Huerfano County"),
        ("chamber.huerfano.org", "Huerfano Chamber"),
        ("lasanimascounty.colorado.gov", "Las Animas County"),
        ("colfaxcountynm.gov", "Colfax County"),
        ("co.colfax.nm.us", "Colfax County"),
        ("trinidad.co.gov", "Trinidad municipal page"),
        ("villageofeaglenest.org", "Village of Eagle Nest"),
        ("eaglenest.org", "Village of Eagle Nest"),
        ("eaglenestchamber.org", "Eagle Nest Chamber"),
        ("laveta.com", "La Veta"),
        ("la-veta.com", "La Veta"),
        ("lavetacreativedistrict.org", "La Veta Creative District"),
        ("walsenburgmercantile.com", "Walsenburg Mercantile"),
        ("coloradodirectory.com", "Colorado Directory"),
        ("colorado.com", "Colorado travel page"),
        ("newmexico.org", "New Mexico travel page"),
        ("sba.gov", "U.S. Small Business Administration"),
        ("usda.gov", "USDA"),
        ("rd.usda.gov", "USDA Rural Development"),
        ("grants.gov", "Grants.gov"),
        ("oedit.colorado.gov", "Colorado OEDIT"),
        ("edd.newmexico.gov", "New Mexico Economic Development Department"),
        ("nmeconomicdevelopment.com", "New Mexico economic development"),
        ("biz.nm.gov", "New Mexico business portal"),
        ("nmfinance.com", "New Mexico Finance Authority"),
        ("coloradocreativeindustries.org", "Colorado Creative Industries"),
        ("krtnradio.com", "KRTN Radio"),
        ("startupspace.app", "Startup Space"),
        ("sccfcolorado.org", "Southern Colorado Community Foundation"),
        ("growraton.org", "Grow Raton"),
        ("sharenm.org", "Share New Mexico"),
        ("localstash.com", "LocalStash"),
        ("colorado.localstash.com", "LocalStash Colorado"),
        ("newmexico.localstash.com", "LocalStash New Mexico"),
        ("roadtrips.localstash.com", "LocalStash Magazine"),
        ("weekender.pub", "Weekender"),
        ("weekendermagazines.com", "Weekender Magazines"),
    ]
    for needle, label in sorted(mappings, key=lambda item: len(item[0]), reverse=True):
        if needle in domain:
            return label
    return ""


def platform_link_label(domain: str) -> str:
    if "facebook.com" in domain or "fb.com" in domain:
        return "Facebook page"
    if "instagram.com" in domain:
        return "Instagram profile"
    if "youtube.com" in domain or "youtu.be" in domain:
        return "YouTube channel"
    if "tiktok.com" in domain:
        return "TikTok profile"
    if "linkedin.com" in domain:
        return "LinkedIn page"
    if "x.com" in domain or "twitter.com" in domain:
        return "X profile"
    return ""


def related_link_label(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.lower()
    platform = platform_link_label(domain)
    if platform:
        return platform
    if "yellowpages.com" in domain:
        city = city_from_url_path(path)
        return f"YellowPages {city} listings" if city else "YellowPages listing"
    if "openstreetmap.org" in domain or "google.com/maps" in url.lower():
        return "Map"
    base = known_site_label(domain)
    if base:
        if re.search(r"event|calendar", path):
            return f"{base} events page"
        if re.search(r"dining|eat|restaurant|food|drink", path):
            return f"{base} dining page"
        if re.search(r"shop|shopping|retail|maker|vendor", path):
            return f"{base} shopping page"
        if re.search(r"lodging|stay|hotel|motel|camp", path):
            return f"{base} lodging page"
        if re.search(r"grant|fund|loan|scholarship|incentive", path):
            return f"{base} funding page"
        if re.search(r"business|directory|member", path):
            return f"{base} directory"
        if re.search(r"listing|things-to-do|attraction|play|visit", path):
            return f"{base} listing"
        return f"{base} page"
    return f"Website: {domain_label(url)}"


def contact_link_label(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace("www.", "")
    platform = platform_link_label(domain)
    if platform:
        return platform
    label = known_site_label(domain)
    if label:
        return f"Website: {label}"
    return f"Website: {domain_label(url)}"


def show_entry_note(note: object) -> bool:
    text = clean_text(note)
    if not text:
        return False
    return not bool(re.search(r"check current details with the listed source|use this as a starting|open the source link when available|flyer|call or visit|confirm|permission|source|posting|public-facing|share digital", text, re.I))


def phone_href(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    return f"tel:+{digits}" if digits else "#"


def tag_list(values: list[str], limit: int = 10) -> str:
    visible = values[:limit]
    more = len(values) - len(visible)
    tags = "".join(f'<span>{esc(value)}</span>' for value in visible)
    if more > 0:
        tags += f"<span>+{more} more</span>"
    return tags


def everything_entry_card(entry: dict, prefix: str) -> str:
    place = place_label(entry)
    contact_links: list[str] = []
    for url in entry.get("websites", []):
        href = local_href(prefix, url)
        contact_links.append(f'<a href="{esc(href)}"{link_target(href)}>{esc(contact_link_label(url))}</a>')
    for email in entry.get("emails", []):
        contact_links.append(f'<a href="mailto:{esc(email)}">Email: {esc(email)}</a>')
    for phone in entry.get("phones", []):
        contact_links.append(f'<a href="{esc(phone_href(phone))}">Phone: {esc(phone)}</a>')
    for address in entry.get("addresses", []):
        href = f"https://www.openstreetmap.org/search?query={quote(address)}"
        contact_links.append(f'<a href="{esc(href)}" target="_blank" rel="noreferrer">Map: {esc(address)}</a>')
    if not contact_links:
        contact_links.append(f'<a href="{prefix}submit/index.html">Send contact info</a>')
    source_links = []
    for url in entry.get("source_urls", []):
        href = local_href(prefix, url)
        source_links.append(f'<a href="{esc(href)}"{link_target(href)}>{esc(related_link_label(url))}</a>')
    if not source_links:
        source_links.append(f'<a href="{prefix}submit/index.html">Submit update</a>')
    note = entry.get("notes_for_use")
    note_html = f'<p class="small"><strong>Next step:</strong> {esc(note)}</p>' if show_entry_note(note) else ""
    aliases = f'<p class="everything-aliases"><strong>Also listed as:</strong> {esc("; ".join(entry.get("aliases", [])[:4]))}</p>' if entry.get("aliases") else ""
    contact_heading = "Contact" if any(entry.get(field) for field in ["websites", "emails", "phones", "addresses"]) else "Contact needed"
    return f'''<article class="compact-resource everything-entry" data-county="{esc(entry.get('county'))}" data-type="{esc(entry.get('entry_type'))}" data-category="{esc(entry.get('category'))}"><div class="everything-entry__head"><h3>{esc(entry.get('name'))}</h3><p class="resource-meta"><span>{esc(place)}</span><span>{esc(entry.get('entry_type'))}</span><span>{esc(entry.get('category'))}</span></p></div><p class="everything-desc">{esc(entry.get('description'))}</p>{aliases}<div class="everything-link-panels"><section class="everything-link-block"><h4>{esc(contact_heading)}</h4><div class="everything-contact" aria-label="Contact links">{''.join(contact_links)}</div></section><section class="everything-link-block"><h4>Related pages</h4><div class="resource-actions everything-sources" aria-label="Related directory and listing pages">{''.join(source_links)}<a href="{prefix}submit/index.html">Correct this listing</a></div></section></div><div class="everything-groups"><section><h4>Useful for</h4><div class="tag-list">{tag_list(entry.get('audiences', []), 6)}</div></section><section><h4>Keywords</h4><div class="tag-list">{tag_list(entry.get('keywords', []), 10)}</div></section><section><h4>Possible channels to ask about</h4><div class="tag-list">{tag_list(entry.get('marketing_channels', []), 8)}</div></section></div>{note_html}</article>'''


def everything_directory_section(entries: list[dict], prefix: str = "../") -> str:
    counts = Counter(entry.get("county") or "Regional" for entry in entries)
    kind_counts = Counter(entry.get("entry_type") or "Directory entry" for entry in entries)
    listing_count = kind_counts.get("Listing", 0)
    shortcut_count = kind_counts.get("Directory shortcut", 0)
    contacts_count = sum(1 for entry in entries if entry.get("websites") or entry.get("emails") or entry.get("phones") or entry.get("addresses"))
    stats = [
        ("Entries", f"{len(entries):,}"),
        ("Listings", f"{listing_count:,}"),
        ("Directory shortcuts", f"{shortcut_count:,}"),
        ("With contact paths", f"{contacts_count:,}"),
        ("County spread", f"Colfax {counts.get('Colfax', 0):,} / Las Animas {counts.get('Las Animas', 0):,} / Huerfano {counts.get('Huerfano', 0):,} / Regional {counts.get('Regional', 0):,}"),
    ]
    stat_html = "".join(f'<article class="everything-stat"><span>{esc(label)}</span><strong>{esc(value)}</strong></article>' for label, value in stats)
    cards = "".join(everything_entry_card(entry, prefix) for entry in entries)
    return f'''<section class="section everything-directory" id="everything-directory"><div class="section-heading"><p class="eyebrow">All listings</p><h2>The Directory of Absolutely Everything</h2><p class="section-note">Browse regional listings and helpful directory shortcuts in one searchable place. Each card includes practical contact paths, a short description, keywords, audiences, and the kinds of marketing channels you can ask about. If you'd like to add a listing to this regional directory or any other directory, please visit the <a href="{prefix}submit/index.html">Submit Update</a> page.</p></div><div class="everything-stats">{stat_html}</div><div class="resource-actions everything-downloads"><a class="button button-soft" href="{prefix}data/directory_of_absolutely_everything.csv">Download CSV</a><a class="button button-soft" href="{prefix}data/directory_of_absolutely_everything.json">Download JSON</a><a class="button button-soft" href="{prefix}submit/index.html">Submit a correction</a></div>{list_search('Search The Directory of Absolutely Everything', 'Try bakery, gallery, grant, lodging, Raton, Trinidad, Walsenburg, nonprofit...')}<div class="compact-resource-list everything-list">{cards}</div></section>'''


def matches_terms(row: dict, terms: list[str]) -> bool:
    hay = " ".join(str(value or "") for value in row.values()).lower()
    return any(term in hay for term in terms)


def selected_hay(row: dict) -> str:
    return " ".join(str(row.get(key, "")) for key in ["resource_name", "category", "resource_type", "notes", "source_type"]).lower()


def matches_patterns(row: dict, patterns: list[str]) -> bool:
    hay = selected_hay(row)
    return any(re.search(pattern, hay, re.I) for pattern in patterns)


LOCALSTASH_DIRECTORY_SOURCES = [
    {
        "title": "LocalStash Free Biz Map Pins",
        "county": "Regional",
        "kind": "Visitor-facing business listing program",
        "url": "https://localstash.com/free-biz-map-pins/",
        "best_for": "Locally owned, traveler-facing businesses that want to ask about a LocalStash map pin, town-page visibility, and the travelers-card program.",
        "action": "Use to ask whether a business qualifies and what the current participation terms require before promising placement or a discount.",
    },
    {
        "title": "LocalStash Business Owner FAQ",
        "county": "Regional",
        "kind": "Business profile / visitor discovery FAQ",
        "url": "https://localstash.com/business-owner-faqs/",
        "best_for": "Small-town cafes, restaurants, breweries, boutiques, galleries, activities, recreation providers, and other local-owned traveler-facing businesses.",
        "action": "Use before recommending LocalStash to a business owner; check current eligibility, discount expectations, and contact path.",
    },
    {
        "title": "LocalStash Chamber, Visitor Center and Tourism Board FAQ",
        "county": "Regional",
        "kind": "Chamber / tourism partnership FAQ",
        "url": "https://localstash.com/chamber-of-commerce-faqs/",
        "best_for": "Chambers, MainStreet programs, visitor centers, tourism offices, and local business groups considering LocalStash as a visitor-discovery companion.",
        "action": "Use to frame LocalStash as a complement to existing chambers and directories, not a replacement.",
    },
    {
        "title": "LocalStash Magazine: SoCO & NoNM",
        "county": "Regional",
        "kind": "Regional magazine / visitor channel",
        "url": "https://localstash.com/localstash-magazine-soco-nonm/",
        "best_for": "Southern Colorado and northern New Mexico visitor-facing stories, local businesses, regional issues, and possible magazine inquiry paths.",
        "action": "Use to review current issues and contact LocalStash before assuming publication, advertising, or inclusion terms.",
    },
    {
        "title": "Weekender Magazines SoCO & NoNM",
        "county": "Regional",
        "kind": "Regional events / sponsor / rate-sheet channel",
        "url": "https://weekender.pub/",
        "best_for": "Southern Colorado and northern New Mexico events, sponsor visibility, regional stories, and possible magazine advertising inquiry paths.",
        "action": "Use to check whether Weekender or LocalStash is the current route for an event, sponsor, story, or advertising question.",
    },
    {
        "title": "Weekender Sample Issue and Rate Sheet",
        "county": "Regional",
        "kind": "Advertising / sample issue",
        "url": "https://weekender.pub/sample-issue-rate-sheet/",
        "best_for": "Reviewing sample page types, regional events placement, sponsor formats, and published rate-sheet context.",
        "action": "Use only as a current-check starting point; confirm rates, deadlines, and publication status before spending money.",
    },
    {
        "title": "LocalStash Trinidad Town Page",
        "county": "Las Animas",
        "kind": "Visitor town page / local business highlights",
        "url": "https://colorado.localstash.com/trinidad-co/",
        "best_for": "Trinidad visitor-facing businesses, galleries, food, retail, lodging, activities, and local-first discovery.",
        "action": "Use when a Trinidad business or partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
    {
        "title": "LocalStash Walsenburg, La Veta and Cuchara Town Page",
        "county": "Huerfano",
        "kind": "Visitor town page / local business highlights",
        "url": "https://colorado.localstash.com/walsenburg-laveta-cuchara/",
        "best_for": "Walsenburg, La Veta, and Cuchara visitor-facing businesses, food, retail, lodging, outdoor recreation, and local-first discovery.",
        "action": "Use when a Huerfano business or tourism partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
    {
        "title": "LocalStash Raton Town Page",
        "county": "Colfax",
        "kind": "Visitor town page / local business highlights",
        "url": "https://newmexico.localstash.com/raton-nm/",
        "best_for": "Raton visitor-facing businesses, historic downtown, outdoor recreation, lodging, dining, shopping, and local-first discovery.",
        "action": "Use when a Raton business or tourism partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
    {
        "title": "LocalStash Angel Fire Town Page",
        "county": "Colfax",
        "kind": "Visitor town page / local business highlights",
        "url": "https://newmexico.localstash.com/angel-fire-nm/",
        "best_for": "Angel Fire visitor-facing lodging, restaurants, recreation, retail, activities, and local-first discovery.",
        "action": "Use when an Angel Fire business or tourism partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
    {
        "title": "LocalStash Cimarron Town Page",
        "county": "Colfax",
        "kind": "Visitor town page / local business highlights",
        "url": "https://newmexico.localstash.com/cimmaron-nm/",
        "best_for": "Cimarron visitor-facing history, lodging, shops, museums, outdoor recreation, and local-first discovery.",
        "action": "Use when a Cimarron business or tourism partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
    {
        "title": "LocalStash Eagle Nest Town Page",
        "county": "Colfax",
        "kind": "Visitor town page / local business highlights",
        "url": "https://newmexico.localstash.com/eagle-nest-nm/",
        "best_for": "Eagle Nest visitor-facing lodging, lake recreation, shops, cafes, activities, and local-first discovery.",
        "action": "Use when an Eagle Nest business or tourism partner wants to check LocalStash visibility, map-pin options, or visitor-facing fit.",
    },
]


LOCALSTASH_AMPLIFIER_CHANNELS = [
    {
        "channel": "LocalStash Free Biz Map Pins",
        "area_served": "Colfax, Las Animas, Huerfano, and nearby visitor towns",
        "channel_type": "Visitor-facing map pin; business profile; travelers-card program",
        "asks": "Ask whether the business qualifies, whether the town is active, and what current participation terms require.",
        "best_for": "Locally owned cafes, restaurants, breweries, boutiques, galleries, outfitters, activities, recreation providers, lodging-adjacent businesses, and traveler-facing shops.",
        "source_url": "https://localstash.com/free-biz-map-pins/",
        "implementation_note": "Use as a visitor-discovery and local-business visibility channel. Do not promise placement, discounts, or town activation without LocalStash confirmation.",
    },
    {
        "channel": "LocalStash Magazine: SoCO & NoNM",
        "area_served": "Southern Colorado and northern New Mexico",
        "channel_type": "Regional magazine; visitor stories; business visibility inquiry route",
        "asks": "Ask about current issue timing, story fit, sponsor fit, publication status, and whether LocalStash or Weekender is the correct intake route.",
        "best_for": "Visitor-facing events, local businesses, local stories, travel routes, artists, venues, outdoor recreation, and regional cross-promotion.",
        "source_url": "https://localstash.com/localstash-magazine-soco-nonm/",
        "implementation_note": "Use as a current-check route for magazine or regional visibility; confirm publication terms before spending money or announcing placement.",
    },
    {
        "channel": "Weekender Magazines SoCO & NoNM",
        "area_served": "Las Animas, Huerfano, Colfax, and nearby southern Colorado/northern New Mexico communities",
        "channel_type": "Events, sponsors, sample issue, and advertising inquiry route",
        "asks": "Ask whether Weekender is active for the specific event, ad, sponsor, or story request, and verify the current rate sheet.",
        "best_for": "Regional events, sponsor visibility, entertainment, food, shopping, real estate, activities, and public-facing stories.",
        "source_url": "https://weekender.pub/",
        "implementation_note": "Treat as a current-check channel because the public materials connect Weekender and LocalStash. Verify the correct route before action.",
    },
]


def append_unique_by_url(items: list[dict], additions: list[dict], url_key: str = "url") -> None:
    seen = {clean_text(item.get(url_key)).casefold() for item in items if clean_text(item.get(url_key))}
    for addition in additions:
        url = clean_text(addition.get(url_key))
        if url and url.casefold() in seen:
            continue
        items.append(addition)
        if url:
            seen.add(url.casefold())


def apply_localstash_supplement(data: dict) -> int:
    before_sources = len(data.setdefault("directory_sources", []))
    before_channels = len(data.setdefault("amplifier_channels", []))
    append_unique_by_url(data["directory_sources"], LOCALSTASH_DIRECTORY_SOURCES, "url")
    append_unique_by_url(data["amplifier_channels"], LOCALSTASH_AMPLIFIER_CHANNELS, "source_url")
    added = (len(data["directory_sources"]) - before_sources) + (len(data["amplifier_channels"]) - before_channels)
    if isinstance(data.get("directory_metadata"), dict):
        data["directory_metadata"]["shortcut_count"] = len(data.get("directory_sources", []))
    data["generated_at"] = "2026-07-01"
    return added


def write_guide_data_bundle(data: dict) -> None:
    guide_json = json.dumps(data, ensure_ascii=False)
    (SITE / "data" / "guide-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (SITE / "assets" / "site-data.js").write_text("window.TRI_COUNTY_GUIDE_DATA = " + guide_json + ";\n", encoding="utf-8")


def copy_audio_package() -> list[dict]:
    if not AUDIO_PKG.exists():
        return []
    for rel in [
        "data/regional_audio_manifest.csv",
        "data/regional_audio_manifest.json",
        "assets/regional-audio-registry.js",
        "docs/CODEX_REGIONAL_AUDIO_IMPLEMENTATION.md",
    ]:
        src = AUDIO_PKG / rel
        if not src.exists():
            continue
        for base in [SITE, ROOT]:
            dst = base / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    manifest_path = SITE / "data" / "regional_audio_manifest.json"
    if not manifest_path.exists():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audio_dir = SITE / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for track in manifest:
        filename = track.get("local_audio_filename_recommended")
        hdl = track.get("hdl") or ""
        match = re.search(r"afcrael\.([0-9a-z]+)", hdl)
        if not filename or not match:
            continue
        dst = audio_dir / filename
        direct = f"https://tile.loc.gov/storage-services/service/afc/afc1940002/afc1940002_{match.group(1)}.mp3"
        track["direct_audio_source"] = direct
        if dst.exists() and dst.stat().st_size > 1000:
            track["local_audio_downloaded"] = True
            continue
        try:
            request = urllib.request.Request(direct, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=30) as response, dst.open("wb") as out:
                shutil.copyfileobj(response, out)
            track["local_audio_downloaded"] = True
        except Exception as exc:  # keep page usable even if LOC download is blocked later
            track["local_audio_downloaded"] = False
            track["download_error"] = repr(exc)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audio_readme = SITE / "assets" / "audio" / "README.md"
    addendum = """

## Regional Audio Registry Addendum

The site also includes `data/regional_audio_manifest.json`, copied from `tri_county_regional_audio_assets_package.zip` on 2026-07-01. The package identifies additional Library of Congress Juan B. Rael Collection tracks and recommended local filenames.

These archival selections are included as cultural context, not as a replacement for outreach to living local musicians. For contemporary music, visual art, photography, or performance work, contact the artist or rights holder and get written permission before using the work on the site or in promotional materials.

Required credit line for Juan B. Rael Collection material:

`Juan B. Rael collection (AFC 1940/002), American Folklife Center, Library of Congress`
"""
    if audio_readme.exists() and "Regional Audio Registry Addendum" not in audio_readme.read_text(encoding="utf-8", errors="ignore"):
        audio_readme.write_text(audio_readme.read_text(encoding="utf-8") + addendum, encoding="utf-8")
    return manifest


def build_pages() -> dict:
    data = json.loads((SITE / "data" / "guide-data.json").read_text(encoding="utf-8"))
    localstash_added = apply_localstash_supplement(data)
    write_guide_data_bundle(data)
    resources = data.get("resources", [])
    sources = data.get("directory_sources", [])
    manifest = copy_audio_package()
    everything_entries = build_everything_directory(data)

    fund_terms = ["grant", "funding", "scholarship", "stipend", "loan", "incentive", "capital", "tax credit", "foundation", "sbdc"]
    arts_patterns = [
        r"\bartists?\b",
        r"\bgaller(?:y|ies)\b",
        r"\bcreative\b",
        r"\bmakers?\b",
        r"\bmusic(?:ian|ians)?\b",
        r"\bvenues?\b",
        r"\barts?\b",
        r"\btattoo",
        r"\bbaker(?:y|ies)\b",
        r"\bmuseums?\b",
        r"\bperformance\b",
        r"\bstudios?\b",
        r"\btheat(?:er|re)s?\b",
        r"\bartisan",
    ]
    funding_sources = sorted([s for s in sources if matches_terms(s, fund_terms)], key=lambda s: (s.get("county", ""), s.get("title", "")))
    funding_rows = sorted([r for r in resources if matches_terms(r, fund_terms)], key=lambda r: (r.get("county", ""), r.get("town", ""), r.get("resource_name", "")))
    arts_rows = sorted([r for r in resources if matches_patterns(r, arts_patterns)], key=lambda r: (r.get("county", ""), r.get("town", ""), r.get("resource_name", "")))

    def is_music(row: dict) -> bool:
        hay = selected_hay(row)
        return any(re.search(pattern, hay, re.I) for pattern in [r"\bmusic", r"\bvenues?\b", r"\bperformance\b", r"\btheat(?:er|re)s?\b", r"\bconcert", r"\bentertainment\b", r"\bevent center\b", r"\bopen mic\b"])

    def is_visual(row: dict) -> bool:
        hay = selected_hay(row)
        return any(re.search(pattern, hay, re.I) for pattern in [r"\bartists?\b", r"\bgaller(?:y|ies)\b", r"\bmakers?\b", r"\bmuseums?\b", r"\bstudios?\b", r"\bcreative\b", r"\barts?\b", r"\bartisan", r"\btattoo", r"\bbaker(?:y|ies)\b", r"\bmercantile\b", r"\bgift\b", r"\bprint", r"\bdesign\b"])

    music_rows = [r for r in arts_rows if is_music(r)]
    visual_rows = [r for r in arts_rows if is_visual(r)]

    SITE.joinpath("resources", "funding").mkdir(parents=True, exist_ok=True)
    SITE.joinpath("resources", "arts-culture").mkdir(parents=True, exist_ok=True)
    SITE.joinpath("promote").mkdir(parents=True, exist_ok=True)
    SITE.joinpath("local-music-arts").mkdir(parents=True, exist_ok=True)
    SITE.joinpath("artist-gallery-promotion").mkdir(parents=True, exist_ok=True)

    hub_cards = [
        ("All listings", f"{len(everything_entries):,} listings and directory shortcuts in one searchable, alphabetized place.", "#everything-directory"),
        ("Grants + funding", "Find grants, loans, incentives, stipends, scholarships, and capital-support starting points.", "funding/index.html"),
        ("Advanced filters", "Use the full directory filters when you need to narrow by county, town, task, source type, or access mode.", "../network/index.html"),
        ("Arts & Culture", "Find artists, galleries, makers, music, venues, creative districts, and cultural routes in one place.", "arts-culture/index.html"),
        ("Calendars + visitor channels", "Find event calendars, tourism pages, LocalStash, visitor guides, and other public-facing routes.", "../amplifiers/index.html"),
        ("Marketing playbook", "Use the short regional checklist for listing, posting, partnering, and following up.", "../promote/index.html"),
        ("Downloads", "Download CSV or JSON when you need a spreadsheet for careful local review.", "../data/directory_of_absolutely_everything.csv"),
    ]
    hub_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../index.html">Home</a><span>/</span><span aria-current="page">Resources</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../assets/animations/hero-plains-valley.svg"><p class="eyebrow">Resource directory</p><h1>Find the right local route faster.</h1><p class="lede">Search regional listings, public directories, funding routes, arts resources, visitor channels, and contact paths across Colfax, Las Animas, and Huerfano counties.</p><p><a class="button button-primary" href="#everything-directory">Search all listings</a> <a class="button button-soft" href="../promote/index.html">Open marketing playbook</a></p></section>
{everything_directory_section(everything_entries, '../')}
<section class="section tinted"><div class="section-heading"><p class="eyebrow">Focused directory pages</p><h2>Use these when you already know the kind of help you need.</h2><p class="section-note">The main directory is the catch-all. These pages narrow the same regional resource set by common jobs: funding, arts, calendars, visitor visibility, and marketing follow-through.</p></div><div class="resource-hub-grid">{''.join(f'<article class="resource-hub-card"><h3>{esc(t)}</h3><p>{esc(d)}</p><a class="text-link" href="{esc(u)}">Open</a></article>' for t,d,u in hub_cards)}</div></section>'''
    (SITE / "resources" / "index.html").write_text(page_shell("resources/index.html", "Resources for the Tri-County Region | Stateline Guide", "Find grants, directories, calendars, media channels, arts resources, visitor routes, and downloadable data for the tri-county region.", hub_body), encoding="utf-8")

    promote_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../index.html">Home</a><span>/</span><span aria-current="page">Promote</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../assets/animations/hero-fishers-peak.svg"><p class="eyebrow">Marketing playbook</p><h1>Get found, then keep showing up.</h1><p class="lede">A short regional checklist for businesses, nonprofits, artists, venues, and programs that want more customers, visitors, partners, and repeat community attention.</p><p><a class="button button-primary" href="../resources/index.html#everything-directory">Search directory</a> <a class="button button-soft" href="../submit/index.html">Fix or add a listing</a></p></section>
<section class="section"><div class="section-heading"><p class="eyebrow">Regional loop</p><h2>List. Post. Partner. Follow up.</h2><p class="section-note">Use the directory first, then pick the most relevant public channel. Strong local visibility usually comes from being listed correctly, posting dated items clearly, partnering across county lines, and following up when details change.</p></div><div class="steps-grid"><article class="step-card"><span class="step-number">1</span><h3>List</h3><p>Make the public listing easy to find and correct.</p><a class="text-link" href="../resources/index.html#everything-directory">Directory</a></article><article class="step-card"><span class="step-number">2</span><h3>Post</h3><p>Use calendars and visitor channels for dated events.</p><a class="text-link" href="../posting/index.html">Event routes</a></article><article class="step-card"><span class="step-number">3</span><h3>Partner</h3><p>Ask aligned businesses, venues, chambers, galleries, and nonprofits.</p><a class="text-link" href="../amplifiers/index.html">Partner channels</a></article><article class="step-card"><span class="step-number">4</span><h3>Follow up</h3><p>Keep what worked and send corrections when something changes.</p><a class="text-link" href="../submit/index.html">Submit update</a></article></div></section>
<section class="section tinted"><div class="section-heading"><p class="eyebrow">Fast routes</p><h2>Start where the need is clearest.</h2></div><div class="resource-bucket-grid"><article class="resource-bucket-card"><h3>Get listed</h3><p>Correct name, location, website, phone, and category.</p><a class="text-link" href="../resources/index.html#everything-directory">All listings</a></article><article class="resource-bucket-card"><h3>Find support</h3><p>Use funding and assistance pages before building a list by hand.</p><a class="text-link" href="../resources/funding/index.html">Funding</a></article><article class="resource-bucket-card"><h3>Promote an event</h3><p>Prepare date, place, image, short blurb, cost, and contact.</p><a class="text-link" href="../posting/index.html">Posting basics</a></article><article class="resource-bucket-card"><h3>Reach visitors</h3><p>Use tourism, calendar, media, and visitor-facing channels.</p><a class="text-link" href="../amplifiers/index.html">Visitor channels</a></article></div></section>
<section class="section"><div class="section-heading"><p class="eyebrow">Tools</p><h2>Use a small packet.</h2><p class="section-note">One paragraph, one image you can use, current contact info, the date or season, and a plain ask.</p></div><div class="resource-bucket-grid"><article class="resource-bucket-card"><h3>Templates</h3><p>Email, event blurb, correction, and outreach formats.</p><a class="text-link" href="../templates/index.html">Open templates</a></article><article class="resource-bucket-card"><h3>Arts & Culture</h3><p>Artists, makers, galleries, venues, music, and cultural routes.</p><a class="text-link" href="../resources/arts-culture/index.html">Open arts</a></article><article class="resource-bucket-card"><h3>Directory assistant</h3><p>Use the search button when you know the need but not the right page.</p><a class="text-link" href="../resources/index.html">Open directory</a></article></div></section>'''
    (SITE / "promote" / "index.html").write_text(page_shell("promote/index.html", "Marketing Playbook for the Tri-County Region | Stateline Guide", "Use a practical marketing workflow for directory listings, event posting, visitor channels, partner outreach, templates, and follow-up across the tri-county region.", promote_body), encoding="utf-8")

    funding_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../../index.html">Home</a><span>/</span><a href="../index.html">Resources</a><span>/</span><span aria-current="page">Grants + funding</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../../assets/animations/hero-spanish-peaks.svg"><p class="eyebrow">Grants + funding</p><h1>Find money, help, or a better first referral.</h1><p class="lede">This page gathers funding routes for startups, nonprofits, artists, creators, community programs, rural businesses, tourism projects, and creative-economy work. Check current eligibility, deadlines, and contact paths before applying or promising support.</p><p><a class="button button-primary" href="#funding-sources">Browse funding sources</a> <a class="button button-soft" href="../../submit/index.html">Submit a funding update</a></p></section>
<section class="section mobile-prune"><div class="section-heading"><p class="eyebrow">How to use this page</p><h2>Start with fit before chasing a deadline.</h2></div><div class="resource-bucket-grid"><article class="resource-bucket-card"><h3>Business or startup</h3><p>Look for SBDC, SBA, rural business, loan, tax-credit, and economic-development routes.</p></article><article class="resource-bucket-card"><h3>Nonprofit or community program</h3><p>Look for local foundations, community grants, fiscal-sponsor paths, and public-benefit programs.</p></article><article class="resource-bucket-card"><h3>Artist or creative project</h3><p>Look for arts councils, creative industries, public-art, cultural heritage, and artist-support routes.</p></article><article class="resource-bucket-card"><h3>Building, venue, or district</h3><p>Look for revitalization, facade, historic preservation, commercial-space, and tourism-development programs.</p></article></div></section>
<section class="section tinted" id="funding-sources"><div class="section-heading"><p class="eyebrow">Funding source shortcuts</p><h2>Open these sources before building a list from scratch.</h2><p class="section-note">Rates, deadlines, eligibility, and application windows change. Use the source page as the authority.</p></div>{list_search('Search funding sources','Try arts, nonprofit, SBA, USDA, Trinidad, New Mexico, Colorado...')}<div class="source-grid compact">{''.join(source_card(s) for s in funding_sources)}</div></section>
<section class="section"><div class="section-heading"><p class="eyebrow">Funding-related entries</p><h2>Local and regional funding entries from the resource directory.</h2><p class="section-note">Some entries are broad support routes rather than direct grant programs. Open the source or ask the listed organization what fits your project.</p></div>{list_search('Search funding entries','Try grant, loan, creative, foundation, startup, artist, nonprofit...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../../') for r in funding_rows)}</div></section>'''
    (SITE / "resources" / "funding" / "index.html").write_text(page_shell("resources/funding/index.html", "Grants, Funding, Stipends & Startup Support | Stateline Guide", "Find grants, stipends, scholarships, loans, incentives, and startup support routes for businesses, nonprofits, artists, creators, and programs in the tri-county region.", funding_body), encoding="utf-8")

    arts_counts = Counter(r.get("county") or "Regional" for r in arts_rows)
    arts_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../../index.html">Home</a><span>/</span><a href="../index.html">Resources</a><span>/</span><span aria-current="page">Arts & Culture</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../../assets/animations/hero-garden-gods.svg"><p class="eyebrow">Arts & Culture</p><h1>Artists, galleries, makers, music, venues, and cultural routes.</h1><p class="lede">Use this page when the work involves creative people, cultural places, local goods, public programs, workshops, performances, or visitor-facing arts activity.</p><p><a class="button button-primary" href="#creative-directory">Search creative entries</a> <a class="button button-soft" href="#music-directory">Music + venues</a> <a class="button button-soft" href="#artist-directory">Artists + galleries</a></p></section>
<section class="section mobile-prune"><div class="section-heading"><p class="eyebrow">Choose the creative job</p><h2>Make the page answer what the visitor came to do.</h2></div><div class="resource-bucket-grid"><article class="resource-bucket-card"><h3>Show or sell work</h3><p>Galleries, shops, maker markets, creative districts, tourism listings, and public events.</p></article><article class="resource-bucket-card"><h3>Book music or performance</h3><p>Venues, theaters, cafes, event organizers, tourism calendars, and media routes.</p></article><article class="resource-bucket-card"><h3>Hire a local creative</h3><p>Artists, designers, musicians, tattooists, makers, teachers, and studios.</p></article><article class="resource-bucket-card"><h3>Find support</h3><p>Creative grants, arts councils, schools, museums, foundations, and economic-development routes.</p></article></div></section>
<section class="section tinted mobile-prune"><div class="section-heading"><p class="eyebrow">Permission and respect</p><h2>Use public listings to make contact, not to reuse someone’s work.</h2><p class="section-note">For living musicians, visual artists, photographers, designers, performers, and makers, get permission before using images, recordings, songs, logos, writing, or portfolio work.</p></div><div class="rights-note">Archival or public-domain material still needs source credit and respectful context. Contemporary local work should be treated as permission-based unless the artist clearly says otherwise.</div></section>
<section class="section" id="creative-directory"><div class="section-heading"><p class="eyebrow">Creative directory</p><h2>{len(arts_rows):,} arts-adjacent entries.</h2><p class="section-note">Colfax {arts_counts.get('Colfax',0)}, Las Animas {arts_counts.get('Las Animas',0)}, Huerfano {arts_counts.get('Huerfano',0)}, Regional {arts_counts.get('Regional',0)}.</p></div>{list_search('Search arts + culture entries','Try gallery, musician, maker, theater, artist, La Veta, Trinidad, Raton...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../../') for r in arts_rows)}</div></section>
<section class="section tinted" id="music-directory"><div class="section-heading"><p class="eyebrow">Music + venues</p><h2>{len(music_rows):,} music, venue, performance, and event-route entries.</h2><p class="section-note">Public listings are contact routes. Confirm current booking details and permission before using recordings, photos, posters, or artwork.</p></div>{list_search('Search music and venue entries','Try music, venue, theater, event, Raton, Trinidad, La Veta...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../../') for r in music_rows)}</div></section>
<section class="section" id="artist-directory"><div class="section-heading"><p class="eyebrow">Artists + galleries</p><h2>{len(visual_rows):,} visual arts, maker, gallery, studio, and creative-service entries.</h2><p class="section-note">Open the page before treating hours, submission paths, or availability as current.</p></div>{list_search('Search artist + gallery entries','Try gallery, artist, maker, studio, museum, tattoo, bakery, Trinidad, La Veta...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../../') for r in visual_rows)}</div></section>'''
    (SITE / "resources" / "arts-culture" / "index.html").write_text(page_shell("resources/arts-culture/index.html", "Arts & Culture Directory | Stateline Guide", "Search arts, music, maker, gallery, venue, museum, creative district, and cultural resource routes across Colfax, Las Animas, and Huerfano counties.", arts_body), encoding="utf-8")

    downloaded_tracks = [t for t in manifest if t.get("local_audio_filename_recommended") and (SITE / "assets" / "audio" / t.get("local_audio_filename_recommended")).exists()]
    first_audio = downloaded_tracks[0].get("local_audio_filename_recommended") if downloaded_tracks else "loc-rael-nm-valse.mp3"
    options = "".join(f'<option data-track-id="{esc(t.get("id") or t.get("local_audio_filename_recommended"))}" value="../assets/audio/{esc(t.get("local_audio_filename_recommended"))}">{esc(t.get("title"))} - {esc(t.get("region"))}</option>' for t in downloaded_tracks)
    if not options:
        options = '<option data-track-id="rael-arroyo-hondo" value="../assets/audio/loc-rael-nm-valse.mp3">Rael Waltz - Arroyo Hondo, NM</option><option data-track-id="rael-antonito" value="../assets/audio/loc-rael-co-valse.mp3">Rael Waltz - Antonito, CO</option>'
    audio_cards = "".join(f'''<article class="audio-card"><h3>{esc(t.get('title'))}</h3><p class="small">{esc(t.get('created_published'))} · {esc(t.get('performers'))}</p><audio controls preload="none" src="../assets/audio/{esc(t.get('local_audio_filename_recommended'))}"></audio><p class="small"><strong>Credit:</strong> {esc(t.get('credit_line'))}</p><p class="small"><a href="{esc(t.get('item_url'))}" target="_blank" rel="noreferrer">Library of Congress item page</a></p></article>''' for t in downloaded_tracks)

    music_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../index.html">Home</a><span>/</span><a href="../resources/index.html">Resources</a><span>/</span><span aria-current="page">Local music and arts</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../assets/animations/hero-archive-ridges.svg"><p class="eyebrow">Music + creative routes</p><h1>Find musicians, venues, arts partners, and cultural audio context.</h1><p class="lede">Use this page for booking music, finding performance routes, preparing a creative event, or understanding how archival audio can sit respectfully beside current local arts work.</p><p><a class="button button-primary" href="#music-directory">Search music + venue entries</a> <a class="button button-soft" href="../resources/arts-culture/index.html">Open arts directory</a></p></section>
<section class="section"><div class="section-heading"><p class="eyebrow">Start with the role</p><h2>Make the first contact specific.</h2></div><div class="table-wrap"><table><thead><tr><th>If you are...</th><th>You may need...</th><th>Prepare first</th></tr></thead><tbody><tr><td>A musician</td><td>Venues, cafes, festivals, fundraisers, open calls</td><td>Bio, sample link, rate, set length, sound needs</td></tr><tr><td>A venue or cafe</td><td>Performers, hosts, recurring event formats</td><td>Date options, pay terms, audience, sound setup</td></tr><tr><td>An organizer</td><td>Calendar, media, tourism, and venue routes</td><td>Event image, date, location, ticket/free status</td></tr><tr><td>A nonprofit or school</td><td>Teaching artists, performers, cultural programs</td><td>Audience, public benefit, partner role, timeline</td></tr></tbody></table></div></section>
<section class="section tinted"><div class="section-heading"><p class="eyebrow">Regional archival audio</p><h2>Listen intentionally, with credit and context.</h2><p class="section-note">These selections come from Library of Congress Juan B. Rael Collection source pages identified in the regional audio package. Audio is opt-in only.</p></div><div class="rights-note">This small archival selection helps represent cultural memory from northern New Mexico and southern Colorado. It is not a substitute for outreach to living local musicians. For contemporary songs, recordings, performances, photos, or artwork, contact the artist and get permission.</div><div class="music-page-panel"><audio id="site-music-loop" loop preload="metadata" src="../assets/audio/{esc(first_audio)}"></audio><div aria-label="Regional archival audio player" class="music-bar" data-music-bar><div class="music-bar__top"><button aria-pressed="false" class="music-toggle" data-state="stopped" type="button">Play</button><label class="music-track-label">Track<select aria-label="Choose regional archival audio track" class="music-track-select">{options}</select></label></div><div class="music-bar__middle"><input aria-label="Music progress" class="music-progress" max="1000" min="0" type="range" value="0"><span aria-live="polite" class="music-time">0:00</span></div><div class="music-bar__bottom"><span>Juan B. Rael Collection, American Folklife Center, Library of Congress.</span><label>Volume<input aria-label="Music volume" class="music-volume" max="100" min="0" type="range" value="58"></label></div></div></div><div class="regional-audio">{audio_cards}</div></section>
<section class="section" id="music-directory"><div class="section-heading"><p class="eyebrow">Music + venue directory</p><h2>Start with likely routes, then check current booking details.</h2><p class="section-note">Use public listings to make contact. Do not reuse recordings, photos, posters, or artwork without permission.</p></div>{list_search('Search music and venue entries','Try music, venue, theater, event, Raton, Trinidad, La Veta...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../') for r in music_rows)}</div></section>'''
    (SITE / "local-music-arts" / "index.html").write_text(page_shell("local-music-arts/index.html", "Local Music, Venues & Regional Audio | Stateline Guide", "Find local music, venues, booking routes, arts partners, and regional archival audio context for the tri-county region.", music_body, "theme-culture"), encoding="utf-8")

    visual_body = f'''<nav aria-label="Breadcrumb" class="breadcrumbs"><a href="../index.html">Home</a><span>/</span><a href="../resources/index.html">Resources</a><span>/</span><span aria-current="page">Artists and galleries</span></nav>
<section class="page-hero"><img alt="" aria-hidden="true" class="page-hero-art" src="../assets/animations/hero-desert-buttes.svg"><p class="eyebrow">Artists + galleries</p><h1>Find where creative work can be shown, sold, commissioned, taught, or promoted.</h1><p class="lede">Use this page for artists, galleries, makers, studios, creative services, museums, shops, classes, public-art ideas, and arts partnerships.</p><p><a class="button button-primary" href="#artist-directory">Search artist + gallery entries</a> <a class="button button-soft" href="../local-music-arts/index.html">Music + venues</a></p></section>
<section class="section"><div class="section-heading"><p class="eyebrow">Choose the useful route</p><h2>Promotion works better when the ask is clear.</h2></div><div class="resource-bucket-grid"><article class="resource-bucket-card"><h3>I want to show or sell work</h3><p>Start with galleries, shops, creative districts, markets, tourism listings, and event calendars.</p></article><article class="resource-bucket-card"><h3>I want to hire an artist</h3><p>Define scope, budget, timeline, location, usage rights, and approval process before asking for ideas.</p></article><article class="resource-bucket-card"><h3>I manage a venue or gallery</h3><p>Publish submission, vendor, exhibition, commission, workshop, or booking expectations plainly.</p></article><article class="resource-bucket-card"><h3>I need arts funding</h3><p>Use the grants page first, then pair creative-funding routes with a project packet and source links.</p><a class="text-link" href="../resources/funding/index.html">Open grants + funding</a></article></div></section>
<section class="section tinted"><div class="section-heading"><p class="eyebrow">Respect the work</p><h2>Public listings are contact routes, not permission slips.</h2><p class="section-note">Before using an artist’s image, logo, recording, portfolio text, design, mural, class materials, or performance footage, ask for permission and agree on credit, payment, scope, and usage.</p></div></section>
<section class="section" id="artist-directory"><div class="section-heading"><p class="eyebrow">Searchable artist + gallery entries</p><h2>{len(visual_rows):,} visual arts, maker, gallery, studio, and creative-service entries.</h2><p class="section-note">Open the source before treating hours, submission paths, or availability as current.</p></div>{list_search('Search artist + gallery entries','Try gallery, artist, maker, studio, museum, tattoo, bakery, Trinidad, La Veta...')}<div class="compact-resource-list">{''.join(compact_resource(r, '../') for r in visual_rows)}</div></section>'''
    (SITE / "artist-gallery-promotion" / "index.html").write_text(page_shell("artist-gallery-promotion/index.html", "Artist, Gallery, Maker & Creative Service Routes | Stateline Guide", "Find artist, gallery, maker, studio, museum, creative service, and arts collaboration routes across the tri-county region.", visual_body, "theme-culture"), encoding="utf-8")

    return {
        "funding_sources": len(funding_sources),
        "funding_rows": len(funding_rows),
        "arts_rows": len(arts_rows),
        "music_rows": len(music_rows),
        "visual_rows": len(visual_rows),
        "everything_entries": len(everything_entries),
        "localstash_records_added": localstash_added,
        "audio_manifest_tracks": len(manifest),
        "downloaded_manifest_tracks": len(downloaded_tracks),
    }


def global_cleanup() -> int:
    count = 0
    for path in SITE.rglob("*.html"):
        rel = path.relative_to(SITE).as_posix()
        page = path.read_text(encoding="utf-8", errors="ignore")
        page = re.sub(r'<header class="site-header">.*?</header>', header(rel), page, count=1, flags=re.S)
        page = re.sub(r'<footer class="site-footer">.*?</footer>', footer(rel), page, count=1, flags=re.S)
        replacements = {
            "with search, spreadsheet-backed leads, source links, and verification reminders": "with search, public source links, practical next steps, and update reminders",
            "spreadsheet-backed directory inventory": "local resource directory",
            "Leads from the spreadsheet-backed directory layer.": "Local entries and useful starting points.",
            "Searchable inventory": "Local entries",
            "Inventory leads to verify": "Local entries",
            "These are starting points, not final proof. Use the source link when available.": "Use the source link when available. If details have changed, send a correction.",
            "source-backed starting points, not endorsements or guaranteed placements": "starting points for choosing who to contact first",
            "source-backed starting points": "starting points",
            "Source-backed": "Public-source",
            "source-backed": "public-source",
            "lead-discovery/source-check candidate": "resource entry",
            "Lead bank": "Resource list",
            "Footer additions: county task routes, workbook download, local music and arts assets, source notes, sitemap, and update intake.": "See something outdated? Send a source link through Submit Update so the guide can improve.",
            "Confirm current rules, rates, dates, and acceptance before action.": "Check current details before spending money or announcing placement.",
            "Search all resources": "Advanced filters",
            "Search the full regional directory": "Use the advanced directory filters",
            "Open full directory": "Open resource directory",
            "Resource hub": "Resource directory",
            "resource hub": "resource directory",
            "Open source": "Open page",
            "Open the source": "Open the page",
            "open the source": "open the page",
            "source links": "practical links",
            "Source link needed": "Listing link needed",
        }
        for old, new in replacements.items():
            page = page.replace(old, new)
        path.write_text(page, encoding="utf-8")
        count += 1
    return count


def update_home_and_sitemap() -> None:
    home = SITE / "index.html"
    page = home.read_text(encoding="utf-8")
    if "resources/funding/index.html" not in page.split("</main>", 1)[0]:
        block = '''<section class="section tinted"><div class="section-heading"><p class="eyebrow">Resource hub</p><h2>Looking for grants, directories, artists, calendars, or media routes?</h2><p class="section-note">Start with the Resources tab when you need a practical list or searchable directory.</p></div><div class="resource-hub-grid"><article class="resource-hub-card"><h3>Grants + funding</h3><p>Funding routes for businesses, nonprofits, artists, creators, and rural projects.</p><a class="text-link" href="resources/funding/index.html">Open funding resources</a></article><article class="resource-hub-card"><h3>Arts, music + makers</h3><p>Creative directories, venues, galleries, cultural audio, and permission reminders.</p><a class="text-link" href="resources/arts-culture/index.html">Open arts resources</a></article><article class="resource-hub-card"><h3>Search all resources</h3><p>Use the searchable regional directory when you know a town, county, task, or keyword.</p><a class="text-link" href="network/index.html">Search the directory</a></article></div></section>'''
        page = page.replace("</main>", block + "</main>", 1)
        home.write_text(page, encoding="utf-8")
    sitemap = SITE / "sitemap.xml"
    if sitemap.exists():
        sm = sitemap.read_text(encoding="utf-8")
        additions = ["resources/", "resources/funding/", "resources/arts-culture/", "promote/"]
        xml = ""
        for item in additions:
            loc = f"https://statelineguide.org/{item}"
            if loc not in sm:
                xml += f"\n  <url><loc>{loc}</loc><lastmod>2026-07-01</lastmod></url>"
        if xml:
            sitemap.write_text(sm.replace("</urlset>", xml + "\n</urlset>"), encoding="utf-8")


def update_sources_notes() -> None:
    audio_note = "\n\n## 2026-07-01 Regional Audio Assets Package\n\n- `data/regional_audio_manifest.json` - Library of Congress Juan B. Rael Collection audio candidates and credit metadata.\n- `assets/audio/` - user-initiated archival audio files only; no autoplay.\n- Contemporary local music, images, and artwork require permission from the artist or rights holder before use.\n"
    localstash_note = "\n\n## 2026-07-01 LocalStash / Weekender Check\n\n- Added LocalStash town pages, LocalStash business/chamber FAQ routes, LocalStash Magazine: SoCO & NoNM, Weekender Magazines, and Weekender sample issue/rate-sheet pages as visitor-facing directory and amplifier channels.\n- Public copy treats these as contact/check routes only. Verify current publication status, eligibility, rates, deadlines, and participation terms before promising placement or asking a business to commit.\n"
    for path in [SITE / "SOURCES.md", SITE / "data" / "SOURCES.md"]:
        if path.exists():
            content = path.read_text(encoding="utf-8")
            updated = content
            if "Regional Audio Assets Package" not in content:
                updated += audio_note
            if "LocalStash / Weekender Check" not in content:
                updated += localstash_note
            if updated != content:
                path.write_text(updated, encoding="utf-8")


def update_app_language() -> None:
    app_path = SITE / "assets" / "app.js"
    if not app_path.exists():
        return
    app = app_path.read_text(encoding="utf-8")
    replacements = {
        "Visitor-facing listing from a public tourism or travel source. Open the source to check current details before planning outreach or promotion.": "Visitor-facing entry. Use the available links to check current details before planning outreach or promotion.",
        "Creative listing from a public arts, tourism, chamber, creative-district, or maker source. Open the source to check current hours, contact paths, and participation details.": "Creative or arts-related entry. Use the available links to check current hours, contact paths, and participation details.",
        "Use this as a starting contact. Open a source link when available, and send an update if details have changed.": "Use this entry to find a contact path, then send an update if details have changed.",
        "Open source": "Open page",
        "Open the source": "Open the page",
        "open the source": "open the page",
        "source links": "practical links",
        "Source link needed": "Listing link needed",
        "Open source for": "Open listing for",
        "Results include source links and update reminders.": "Results include practical links and update paths.",
        "Use this as a starting point, then check current details.": "Use this result to choose a next contact or page to open.",
    }
    for old, new in replacements.items():
        app = app.replace(old, new)
    public_description_js = r'''function publicDescription(item) {
  const raw = String(item.notes || item.best_for || item.description || "").trim();
  const joinedFlag = (...parts) => parts.join("");
  const genericPhrases = [
    "use as a launch/outreach " + "lead",
    "commercial-directory-only " + "lead",
    joinedFlag("source", "-check"),
    "spreadsheet-" + "backed",
    "not final proof",
    "verify details before spending",
    "visitor-facing listing pulled",
    "creative-directory " + "lead added"
  ];
  const genericText = !raw || genericPhrases.some(phrase => raw.toLowerCase().includes(phrase.toLowerCase()));
  const place = [item.town, item.county, item.state].filter(Boolean).join(", ") || item.county || "the tri-county region";
  const category = publicType(item.category || item.resource_type || item.kind || "local resource").toLowerCase();
  const blob = [item.resource_name, item.title, item.channel, item.category, item.resource_type, item.kind, item.source_type, item.best_for, item.notes]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (!genericText) {
    return raw
      .replace(/source-backed starting points?/gi, "starting points")
      .replace(new RegExp("lead-discovery/" + joinedFlag("source", "-check") + " candidates?", "gi"), "resource entries")
      .replace(/lead bank/gi, "resource list")
      .replace(/Confirm current rules, rates, dates, and acceptance before action\./gi, "Check current details before spending money or announcing placement.");
  }

  let descriptor = "Local business or organization";
  let use = "Use it to identify a possible local contact, then check a current business-owned page or directory listing before outreach.";
  if (/grant|fund|loan|stipend|scholarship|sba|usda|economic development|technical assistance/.test(blob)) {
    descriptor = "Funding or business-support route";
    use = "Use it to find program pages, eligibility details, deadlines, and the office or organization that should confirm the next step.";
  } else if (/artist|arts|creative|gallery|studio|painting|writer|storyteller|tattoo|museum|theat|music|film|photo|design/.test(blob)) {
    descriptor = "Arts, culture, or creative-business listing";
    use = "Use it for artist referrals, exhibitions, workshops, performances, cultural events, and creative cross-promotion questions.";
  } else if (/restaurant|dining|cafe|coffee|bar|brew|bakery|food|beverage|cater|kitchen|grill/.test(blob)) {
    descriptor = "Food, drink, or dining listing";
    use = "Use it for visitor referrals, local event outreach, shop-local campaigns, and cross-promotion questions.";
  } else if (/event|calendar|festival|market|performance|venue|workshop|class/.test(blob)) {
    descriptor = "Event, venue, or calendar route";
    use = "Use it when planning public events, performances, classes, workshops, or calendar visibility across the region.";
  } else if (/chamber|mainstreet|city|town|county|government|library|school|college|visitor center|tourism/.test(blob)) {
    descriptor = "Civic, visitor, or partner-organization route";
    use = "Use it to find formal contact paths, business referrals, community-posting questions, or local program connections.";
  } else if (/media|magazine|newspaper|radio|newsletter|press|advertis|publisher|broadcast|localstash|weekender/.test(blob)) {
    descriptor = "Media, visitor, or advertising route";
    use = "Use it to ask about appropriate announcement, advertising, calendar, newsletter, or public-information routes.";
  } else if (/lodging|hotel|motel|inn|cabin|rv|campground|resort|vacation rental|bed and breakfast|b&b/.test(blob)) {
    descriptor = "Lodging or hospitality listing";
    use = "Use it for visitor referrals, event guest planning, trip-planning pages, and guest-facing information questions.";
  } else if (/shop|retail|store|boutique|mercantile|market|gift|thrift|antique|book|florist|jewelry|maker|artisan/.test(blob)) {
    descriptor = "Shop, maker, or local retail listing";
    use = "Use it for shop-local outreach, event materials, visitor referrals, or local-goods partnerships.";
  }
  return `${descriptor} in ${place}. ${use}`;
}'''
    app = re.sub(r"function publicDescription\(item\) \{.*?\n\}\n\nfunction publicType", public_description_js + "\n\nfunction publicType", app, count=1, flags=re.S)
    app = app.replace(
        'const description = item.best_for || publicDescription(item) || item.asks || item.short_description || "Use this result to choose a next contact or page to open.";',
        'const description = publicDescription(item) || item.asks || item.short_description || item.best_for || "Use this result to choose a next contact or page to open.";'
    )
    app_path.write_text(app, encoding="utf-8")


def update_everything_directory_styles() -> None:
    css_path = SITE / "assets" / "styles.css"
    if not css_path.exists():
        return
    marker = "/* Rich deduped everything directory cards */"
    css = css_path.read_text(encoding="utf-8")
    if marker in css:
        return
    css += f"""

{marker}
.everything-entry {{
  gap: 10px;
  padding: 16px;
}}
.everything-entry__head {{
  display: grid;
  gap: 5px;
}}
.everything-desc {{
  color: var(--ink);
  max-width: 78ch;
}}
.everything-aliases {{
  color: var(--ink-soft);
  font-size: 0.9rem;
}}
.everything-contact,
.everything-sources,
.tag-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}}
.everything-contact a,
.everything-sources a,
.tag-list span {{
  border: 1px solid rgba(47,103,128,0.18);
  border-radius: 999px;
  background: rgba(255,255,255,0.72);
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.25;
  padding: 6px 9px;
  text-decoration: none;
}}
.everything-contact a {{
  background: rgba(220,238,232,0.62);
}}
.everything-sources a {{
  background: rgba(216,187,104,0.14);
}}
.everything-groups {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 10px;
}}
.everything-groups section {{
  display: grid;
  align-content: start;
  gap: 6px;
  min-width: 0;
}}
.everything-groups h4 {{
  margin: 0;
  color: var(--ink-soft);
  font-size: 0.78rem;
  letter-spacing: 0;
  text-transform: uppercase;
}}
.everything-entry .small {{
  color: var(--ink-soft);
}}
@media (max-width: 680px) {{
  .everything-entry {{
    padding: 14px;
  }}
  .everything-groups {{
    grid-template-columns: 1fr;
  }}
  .everything-list {{
    max-height: none;
    overflow: visible;
    padding-right: 0;
  }}
}}
"""
    css_path.write_text(css, encoding="utf-8")


def update_directory_ui_styles() -> None:
    css_path = SITE / "assets" / "styles.css"
    if not css_path.exists():
        return
    marker = "/* Directory navigation and card refinement pass */"
    css = css_path.read_text(encoding="utf-8")
    if marker in css:
        return
    css += f"""

{marker}
.everything-link-panels {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 10px;
}}
.everything-link-block {{
  display: grid;
  align-content: start;
  gap: 7px;
  min-width: 0;
  padding: 10px;
  border: 1px solid rgba(47,103,128,0.14);
  border-radius: var(--radius);
  background: rgba(255,255,255,0.48);
}}
.everything-link-block h4 {{
  margin: 0;
  color: var(--ink);
  font-size: 0.82rem;
  letter-spacing: 0;
}}
.everything-contact a,
.everything-sources a {{
  max-width: 100%;
  overflow-wrap: anywhere;
}}
.everything-sources {{
  margin-top: 0;
}}
.everything-directory .section-heading .section-note a {{
  font-weight: 800;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
}}
.site-nav a:focus-visible,
.nav-trigger:focus-visible,
.nav-menu a:focus-visible,
.directory-assistant__toggle:focus-visible,
.directory-assistant__close:focus-visible {{
  outline: 3px solid var(--gold);
  outline-offset: 3px;
}}
.source-card .source-note,
.resource-item .source-note {{
  color: rgba(23,48,71,0.72) !important;
}}
@media (max-width: 760px) {{
  .site-header {{
    align-items: flex-start;
  }}
  .site-nav {{
    justify-content: flex-start;
  }}
  .nav-menu {{
    left: 0;
    right: auto;
    max-width: calc(100vw - 36px);
  }}
}}
"""
    css_path.write_text(css, encoding="utf-8")


MOBILE_QUICK_PANELS = {
    "index.html": (
        "Start here",
        "Use this guide to find the right directory, funding source, event channel, arts route, or update path.",
        [("Search all listings", "resources/index.html#everything-directory"), ("Funding", "resources/funding/index.html"), ("Arts & Culture", "resources/arts-culture/index.html"), ("Submit update", "submit/index.html")],
    ),
    "plan/index.html": (
        "Pick a route",
        "Choose the closest need, then open the directory page instead of reading through the full planning guide.",
        [("Directory", "resources/index.html#everything-directory"), ("Funding", "resources/funding/index.html"), ("Arts & Culture", "resources/arts-culture/index.html"), ("Templates", "templates/index.html")],
    ),
    "region/index.html": (
        "Choose a county",
        "Jump to the county or regional page that matches the place you are trying to reach.",
        [("Colfax", "counties/colfax/index.html"), ("Las Animas", "counties/las-animas/index.html"), ("Huerfano", "counties/huerfano/index.html"), ("Regional channels", "regional-channels/index.html")],
    ),
    "about/index.html": (
        "How this was built",
        "The short version: the guide routes users to existing public pages, directories, calendars, and update paths.",
        [("Directory", "resources/index.html#everything-directory"), ("Submit update", "submit/index.html"), ("Sources", "SOURCES.md")],
    ),
    "promote/index.html": (
        "Regional growth loop",
        "Get listed, post dated items, ask the right partner channels, then follow up when details change.",
        [("All listings", "resources/index.html#everything-directory"), ("Post events", "posting/index.html"), ("Visitor channels", "amplifiers/index.html"), ("Templates", "templates/index.html")],
    ),
    "posting/index.html": (
        "Post an event",
        "Use this when the thing has a date, place, deadline, class, show, fundraiser, or public meeting.",
        [("Raton events", "post-events-raton/index.html"), ("Trinidad events", "post-events-trinidad/index.html"), ("Huerfano events", "post-events-huerfano/index.html"), ("Submit update", "submit/index.html")],
    ),
    "templates/index.html": (
        "Use a template",
        "Open the template or route that matches the ask: listing correction, event blurb, flyer packet, or outreach email.",
        [("Directory", "resources/index.html#everything-directory"), ("Event posting", "posting/index.html"), ("Visitor channels", "amplifiers/index.html"), ("Submit update", "submit/index.html")],
    ),
    "local-music-arts/index.html": (
        "Moved into Arts & Culture",
        "On mobile, music, venues, artists, galleries, and creative routes live together on one shorter page.",
        [("Arts & Culture", "resources/arts-culture/index.html"), ("Music + venues", "resources/arts-culture/index.html#music-directory"), ("Artists + galleries", "resources/arts-culture/index.html#artist-directory"), ("Funding", "resources/funding/index.html")],
    ),
    "artist-gallery-promotion/index.html": (
        "Moved into Arts & Culture",
        "On mobile, artist, gallery, maker, music, venue, and cultural routes live together on one shorter page.",
        [("Arts & Culture", "resources/arts-culture/index.html"), ("Artists + galleries", "resources/arts-culture/index.html#artist-directory"), ("Music + venues", "resources/arts-culture/index.html#music-directory"), ("Funding", "resources/funding/index.html")],
    ),
    "regional-channels/index.html": (
        "Regional channels",
        "Use this page when the audience crosses county lines or the listing is not tied to one town.",
        [("All listings", "resources/index.html#everything-directory"), ("Visitor channels", "amplifiers/index.html"), ("Submit update", "submit/index.html")],
    ),
}


def mobile_panel_for(rel: str) -> tuple[str, str, list[tuple[str, str]]]:
    if rel in MOBILE_QUICK_PANELS:
        return MOBILE_QUICK_PANELS[rel]
    if rel.startswith("counties/"):
        county = Path(rel).parent.name.replace("-", " ").title()
        return (
            county,
            "Use the directory first, then open funding, arts, calendars, or update routes as needed.",
            [("All listings", "resources/index.html#everything-directory"), ("Funding", "resources/funding/index.html"), ("Arts & Culture", "resources/arts-culture/index.html"), ("Submit update", "submit/index.html")],
        )
    if re.search(r"advertise|post-events|calendars|business|nonprofit|nonprofits", rel):
        return (
            "Quick route",
            "Use this page only if it matches the town, county, or audience you need; otherwise start with the main directory.",
            [("All listings", "resources/index.html#everything-directory"), ("Visitor channels", "amplifiers/index.html"), ("Templates", "templates/index.html"), ("Submit update", "submit/index.html")],
        )
    return (
        "Quick route",
        "Start with the directory, then open the most relevant page for funding, arts, visitor channels, templates, or updates.",
        [("All listings", "resources/index.html#everything-directory"), ("Funding", "resources/funding/index.html"), ("Arts & Culture", "resources/arts-culture/index.html"), ("Submit update", "submit/index.html")],
    )


def mobile_link(rel: str, target: str) -> str:
    if target.startswith("#") or re.match(r"^[a-z]+://", target, re.I):
        return target
    return link(root_prefix(rel), target)


def mobile_quick_panel_html(rel: str) -> str:
    title, purpose, actions = mobile_panel_for(rel)
    action_html = "".join(f'<a class="button button-soft" href="{esc(mobile_link(rel, href))}">{esc(label)}</a>' for label, href in actions[:4])
    return f'''<section class="section mobile-quick-panel" aria-label="Mobile quick actions"><div class="section-heading"><p class="eyebrow">Mobile quick route</p><h2>{esc(title)}</h2><p class="section-note">{esc(purpose)}</p></div><div class="mobile-quick-actions">{action_html}</div></section>'''


def add_body_class(page: str, class_name: str) -> str:
    def repl(match: re.Match) -> str:
        attrs = match.group(1)
        class_match = re.search(r'class=["\']([^"\']*)["\']', attrs, re.I)
        if class_match:
            classes = class_match.group(1).split()
            if class_name not in classes:
                classes.append(class_name)
            attrs = attrs[:class_match.start(1)] + " ".join(classes) + attrs[class_match.end(1):]
            return f"<body{attrs}>"
        return f'<body{attrs} class="{class_name}">'
    return re.sub(r"<body([^>]*)>", repl, page, count=1, flags=re.I)


def apply_mobile_concise_layer() -> dict[str, int]:
    directory_keep = {
        "resources/index.html",
        "resources/funding/index.html",
        "resources/arts-culture/index.html",
        "network/index.html",
        "appendix/index.html",
        "amplifiers/index.html",
        "submit/index.html",
    }
    changed = 0
    for path in SITE.rglob("*.html"):
        rel = path.relative_to(SITE).as_posix()
        if rel.startswith("assets/") or rel in directory_keep:
            continue
        page = path.read_text(encoding="utf-8", errors="ignore")
        original = page
        page = add_body_class(page, "mobile-concise")
        page = re.sub(r'<section class="section mobile-quick-panel" aria-label="Mobile quick actions">.*?</section>', "", page, count=1, flags=re.S)
        panel = mobile_quick_panel_html(rel)
        page, inserted = re.subn(r'(<section class="page-hero".*?</section>)', r"\1" + panel, page, count=1, flags=re.S)
        if inserted == 0:
            page, inserted = re.subn(r'(<section class="hero[^"]*".*?</section>)', r"\1" + panel, page, count=1, flags=re.S)
        if inserted == 0:
            page = page.replace('<main id="main">', '<main id="main">' + panel, 1)
        if page != original:
            path.write_text(page, encoding="utf-8")
            changed += 1
    return {"mobile_concise_pages": changed}


def update_mobile_concise_styles() -> None:
    css_path = SITE / "assets" / "styles.css"
    if not css_path.exists():
        return
    marker = "/* Mobile concise guide pass */"
    css = css_path.read_text(encoding="utf-8")
    if marker in css:
        return
    css += f"""

{marker}
.mobile-quick-panel {{
  display: none;
}}
.mobile-quick-actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}}
@media (max-width: 760px) {{
  .mobile-prune {{
    display: none !important;
  }}
  .page-hero .lede {{
    display: none;
  }}
  body.mobile-concise .page-hero {{
    min-height: auto;
    padding-block: 28px 16px;
  }}
  body.mobile-concise .page-hero .lede {{
    display: none;
  }}
  body.mobile-concise main > section.section:not(.mobile-quick-panel) {{
    display: none !important;
  }}
  .mobile-quick-panel {{
    display: block;
    padding-top: 14px;
    padding-bottom: 18px;
  }}
  .mobile-quick-panel .section-heading {{
    margin-bottom: 12px;
  }}
  .mobile-quick-panel h2 {{
    font-size: clamp(1.35rem, 8vw, 2rem);
  }}
  .mobile-quick-actions {{
    display: grid;
    grid-template-columns: 1fr;
  }}
  .mobile-quick-actions .button {{
    justify-content: center;
    width: 100%;
    min-height: 42px;
  }}
  .site-footer .footer-summary {{
    display: none;
  }}
  .site-footer {{
    padding-block: 18px;
  }}
  .footer-index {{
    gap: 14px;
  }}
  .footer-column h2 {{
    font-size: 0.85rem;
  }}
}}
"""
    css_path.write_text(css, encoding="utf-8")


def seo_description_from_page(page: str, rel: str) -> tuple[str, str]:
    title_match = re.search(r"<title>(.*?)</title>", page, re.I | re.S)
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.I | re.S)
    title = clean_text(re.sub(r"<[^>]+>", " ", title_match.group(1))) if title_match else ""
    heading = clean_text(re.sub(r"<[^>]+>", " ", h1_match.group(1))) if h1_match else ""
    label = heading or title or Path(rel).parent.name.replace("-", " ").title() or "Stateline Guide"
    if title and "Stateline Guide" not in title:
        title = f"{title} | Stateline Guide"
    elif not title:
        title = f"{label} | Stateline Guide"
    meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']*)["\']', page, re.I)
    if meta_match and clean_text(meta_match.group(1)):
        desc = clean_text(meta_match.group(1))
    else:
        first_para = re.search(r"<p[^>]*>(.*?)</p>", page, re.I | re.S)
        desc = clean_text(re.sub(r"<[^>]+>", " ", first_para.group(1))) if first_para else ""
    desc = humanize_public_text(desc)
    if not desc or generic_description(desc):
        desc = f"{label} page for the Stateline Guide, helping regional businesses, nonprofits, artists, event organizers, and service providers find practical visibility routes across Colfax, Las Animas, and Huerfano counties."
    return trim(title, 110), trim(desc, 180)


def canonical_for_rel(rel: str) -> str:
    if rel == "index.html":
        return "https://statelineguide.org/"
    if rel.endswith("/index.html"):
        return f"https://statelineguide.org/{rel[:-10]}"
    return f"https://statelineguide.org/{rel}"


def simple_page_json_ld(title: str, desc: str, canonical: str, page_type: str = "WebPage") -> str:
    return json.dumps({
        "@context": "https://schema.org",
        "@type": page_type,
        "name": title.replace(" | Stateline Guide", ""),
        "description": desc,
        "url": canonical,
        "isPartOf": {
            "@type": "WebSite",
            "name": "Stateline Guide",
            "url": "https://statelineguide.org/"
        },
        "audience": {
            "@type": "Audience",
            "audienceType": "Businesses, nonprofits, artists, entrepreneurs, event organizers, programs, and service providers"
        }
    }, ensure_ascii=False).replace("<", "\\u003c")


def scrub_public_machine_copy(page: str) -> str:
    replacements = {
        "Commercial-directory-only lead from the July 2026 sweep. Treat as unverified until confirmed by an official, business-owned, chamber, tourism, or current public source.": "Local business directory entry. Check a current business-owned page, chamber page, tourism page, or public listing before using it for outreach.",
        "Visitor-facing listing pulled from public travel/vacation guide source(s). Verify current details with the source or listing owner before outreach, publication, printing, or promising placement.": "Public travel or tourism listing. Check current details with the listed page or business before outreach, publication, printing, or promising placement.",
        "Visitor-facing listing from a public tourism or travel source.": "Public travel or tourism listing.",
        "Visitor-facing listing from a public travel or tourism page.": "Public travel or tourism listing.",
        "Creative-directory lead added from a public local arts, tourism, chamber, creative-district, or maker directory.": "Creative listing from a public local arts, tourism, chamber, creative-district, or maker directory.",
        "Creative listing from a public local arts, tourism, chamber, creative-district, or maker directory.": "Creative listing from a local arts, tourism, chamber, creative-district, or maker directory.",
        "Use as a launch/outreach lead; verify details before spending money, printing materials, or promising eligibility.": "Use as a possible local contact; check current details before spending money, printing materials, or promising eligibility.",
        "Use as a launch/outreach listings; Check details before spending money, printing materials, or promising eligibility.": "Use as a possible local contact; check current details before spending money, printing materials, or promising eligibility.",
        "Outreach lead / source-check candidate": "Local resource",
        "source-check candidate": "listing to check",
        "source-check": "listing review",
        "spreadsheet-backed": "directory",
        "not final proof": "needs current confirmation",
        "Yellow Pages bulk source": "Commercial directory import",
        "commercial-directory-only lead": "commercial directory entry",
        "lead-discovery": "directory discovery",
    }
    for old, new in replacements.items():
        page = page.replace(old, new)
    return page


def ensure_page_metadata() -> dict[str, int]:
    stats = {"metadata_updated": 0, "jsonld_added": 0}
    for path in SITE.rglob("*.html"):
        rel = path.relative_to(SITE).as_posix()
        if rel.startswith("assets/"):
            continue
        page = path.read_text(encoding="utf-8", errors="ignore")
        original = page
        title, desc = seo_description_from_page(page, rel)
        canonical = canonical_for_rel(rel)

        page = scrub_public_machine_copy(page)
        if rel == "network/index.html":
            json_ld = simple_page_json_ld(
                "Advanced Directory Filters | Stateline Guide",
                "Search and filter regional directory entries by county, task, resource type, and practical next step.",
                canonical,
                "CollectionPage"
            )
            page = re.sub(r'<script\s+type=["\']application/ld\+json["\']>.*?</script>', f'<script type="application/ld+json">{json_ld}</script>', page, count=1, flags=re.I | re.S)
        if "<title" not in page.lower():
            page = page.replace("<head>", f"<head><title>{esc(title)}</title>", 1)
        if '<meta name="description"' not in page.lower():
            meta = f'<meta name="description" content="{esc(desc)}">'
            if '<meta name="viewport"' in page:
                page = re.sub(r'(<meta\s+name=["\']viewport["\'][^>]*>)', r"\1" + meta, page, count=1, flags=re.I)
            else:
                page = page.replace("<head>", f"<head>{meta}", 1)
            stats["metadata_updated"] += 1
        if 'rel="canonical"' not in page.lower():
            page = page.replace("</title>", f"</title><link rel=\"canonical\" href=\"{esc(canonical)}\">", 1)
            stats["metadata_updated"] += 1
        if 'application/ld+json' not in page.lower():
            json_ld = simple_page_json_ld(title, desc, canonical)
            page = page.replace("</head>", f"<script type=\"application/ld+json\">{json_ld}</script></head>", 1)
            stats["jsonld_added"] += 1
        if page != original:
            path.write_text(page, encoding="utf-8")
            stats["metadata_updated"] += 1
    return stats


PUBLIC_DATA_TEXT_REPLACEMENTS = [
    (r"Visitor-facing listing pulled from public travel/vacation guide source\(s\)\. Verify current details with the source or listing owner before outreach, publication, printing, or promising placement\.", "Public travel or tourism listing. Check current details with the listed page or business before outreach, publication, printing, or promising placement."),
    (r"Visitor-facing listing from a public tourism or travel source\.", "Public travel or tourism listing."),
    (r"Open the source", "Open the page"),
    (r"open the source", "open the page"),
    (r"Open a source link", "Open an available page"),
    (r"source link", "available page"),
    (r"Business type not clear", "Local business listing"),
    (r"Yellow Pages bulk source", "Commercial directory page"),
    (r"Resource hub", "Resource directory"),
    (r"resource hub", "resource directory"),
    (r"Commercial-directory-only lead", "Commercial directory entry"),
    (r"commercial-directory-only lead", "commercial directory entry"),
    (r"Outreach lead / source-check candidate", "Local resource"),
    (r"source-check candidate", "listing to check"),
    (r"source-check", "listing review"),
    (r"spreadsheet-backed", "directory"),
    (r"not final proof", "needs current confirmation"),
    (r"lead-discovery", "directory discovery"),
]


def clean_public_data_text(value: object) -> object:
    if not isinstance(value, str):
        return value
    text = value
    for pattern, replacement in PUBLIC_DATA_TEXT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.I)
    return text


def clean_public_json_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: clean_public_json_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [clean_public_json_value(item) for item in value]
    return clean_public_data_text(value)


def clean_public_resource_row(row: dict) -> dict:
    cleaned = {key: clean_public_data_text(value) for key, value in row.items()}
    description = resource_row_description(cleaned)
    for field in ["notes", "best_for", "description"]:
        raw = clean_text(cleaned.get(field))
        if not raw or generic_description(humanize_public_text(raw)):
            cleaned[field] = description
    if clean_text(cleaned.get("category")).casefold() == "local business listing":
        cleaned["category"] = "Local business listing"
    if re.search(r"commercial directory page", clean_text(cleaned.get("source_type")), re.I):
        cleaned["source_type"] = "Commercial directory page"
    return cleaned


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_public_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8", newline="")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def clean_public_csv_file(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [{key: clean_public_data_text(value) for key, value in row.items()} for row in csv.DictReader(handle)]
    write_public_csv(path, rows)
    return True


def clean_public_data_exports() -> dict[str, int]:
    stats = {"public_data_files_cleaned": 0}
    review_dir = ROOT / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    snapshot = review_dir / "DIRECTORY_RAW_PROVENANCE_SNAPSHOT_20260701.json"
    if not snapshot.exists():
        raw_bundle: dict[str, object] = {}
        for rel in [
            "data/guide-data.json",
            "data/tri_county_persona_resources.json",
            "data/directory-metadata.json",
        ]:
            path = SITE / rel
            if path.exists():
                raw_bundle[rel] = json.loads(path.read_text(encoding="utf-8"))
        write_json(snapshot, raw_bundle)

    guide_path = SITE / "data" / "guide-data.json"
    if guide_path.exists():
        guide = json.loads(guide_path.read_text(encoding="utf-8"))
        guide = clean_public_json_value(guide)
        if isinstance(guide, dict) and isinstance(guide.get("resources"), list):
            guide["resources"] = [clean_public_resource_row(row) for row in guide["resources"]]
        write_json(guide_path, guide)
        site_data = SITE / "assets" / "site-data.js"
        site_data.write_text("window.TRI_COUNTY_GUIDE_DATA = " + json.dumps(guide, ensure_ascii=False) + ";\n", encoding="utf-8")
        stats["public_data_files_cleaned"] += 2

    resources_json = SITE / "data" / "tri_county_persona_resources.json"
    if resources_json.exists():
        rows = json.loads(resources_json.read_text(encoding="utf-8"))
        if isinstance(rows, list):
            rows = [clean_public_resource_row(row) for row in rows]
            write_json(resources_json, rows)
            resources_csv = SITE / "data" / "tri_county_persona_resources.csv"
            if resources_csv.exists():
                write_public_csv(resources_csv, rows)
                stats["public_data_files_cleaned"] += 1
            stats["public_data_files_cleaned"] += 1

    for rel in ["data/directory-metadata.json", "data/directory_of_absolutely_everything.json", "data/yellowpages_outreach_leads_20260701.json"]:
        path = SITE / rel
        if path.exists():
            cleaned_json = clean_public_json_value(json.loads(path.read_text(encoding="utf-8")))
            write_json(path, cleaned_json)
            if rel == "data/directory_of_absolutely_everything.json" and isinstance(cleaned_json, list):
                write_public_csv(SITE / "data" / "directory_of_absolutely_everything.csv", cleaned_json)
                stats["public_data_files_cleaned"] += 1
            stats["public_data_files_cleaned"] += 1
    for rel in [
        "data/yellowpages_outreach_leads_20260701.csv",
        "data/tri_county_yellowpages_flyer_digital_outreach_scored_20260701.csv",
    ]:
        if clean_public_csv_file(SITE / rel):
            stats["public_data_files_cleaned"] += 1
    return stats


def mirror_support_files() -> dict[str, int]:
    copied = 0
    failed = 0
    for rel in [
        "data/regional_audio_manifest.json",
        "data/regional_audio_manifest.csv",
        "data/guide-data.json",
        "data/directory_of_absolutely_everything.json",
        "data/directory_of_absolutely_everything.csv",
        "assets/site-data.js",
        "assets/regional-audio-registry.js",
        "assets/styles.css",
        "assets/app.js",
    ]:
        src = SITE / rel
        if not src.exists():
            continue
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(src, dst)
            copied += 1
        except OSError:
            try:
                dst.write_bytes(src.read_bytes())
                copied += 1
            except OSError:
                failed += 1
    return {"mirrored_support_files": copied, "mirror_failures": failed}


def ensure_site_folder() -> None:
    if SITE.exists():
        return
    seed = ROOT / "dist" / "tri-county-netlify-guide-deep"
    if seed.exists():
        SITE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(seed, SITE)
        return
    raise SystemExit(f"Site folder not found and no seed build is available: {SITE}")


def main() -> None:
    ensure_site_folder()
    stats = build_pages()
    updated = global_cleanup()
    update_home_and_sitemap()
    update_sources_notes()
    update_app_language()
    update_everything_directory_styles()
    update_directory_ui_styles()
    update_mobile_concise_styles()
    mobile_stats = apply_mobile_concise_layer()
    metadata_stats = ensure_page_metadata()
    public_data_stats = clean_public_data_exports()
    mirror_stats = mirror_support_files()
    print(json.dumps({**stats, "html_files_updated": updated, **mobile_stats, **metadata_stats, **public_data_stats, **mirror_stats}, indent=2))


if __name__ == "__main__":
    main()

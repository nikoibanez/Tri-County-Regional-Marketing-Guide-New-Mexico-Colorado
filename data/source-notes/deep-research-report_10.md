# Executive Summary

This report analyzes the **current Stateline Guide site** (https://wonderful-kashata-6ed008.netlify.app/) and provides a detailed, step-by-step plan to align it with official branding and improve UX. We first inventory the site’s structure, pages, navigation, templates, and assets. We then gather **Super Eukarya** and **City of Raton** branding values and color palettes, mapping them against the site’s elements to identify mismatches (colors, typography, logos, tone, accessibility, legal use). Next, we present *Codex-ready* Markdown tasks and code snippets to implement the changes, complete with file paths and diff-style edits. These tasks cover navigation relabeling, task-based routing, UI components (stepper, search, CTA buttons), and progressive enhancement. We include ARIA roles for accessibility, SEO/meta updates, and content/UX refinements (e.g. “Why not Google?” explanation). We list required assets (logos, fonts, colors) with fallbacks. Finally, we provide a prioritized implementation plan (with estimated effort and acceptance criteria), tables of current vs. proposed navigation labels and appendix filters, and **mermaid** diagrams for site flow and a rollout timeline. 

- *Brand alignment:* Use Super Eukarya’s values (science-driven, clarity, sustainable design) and Raton’s “Your Pass” tourism brand (adventure-themed tagline and brown/orange/teal color palette).  
- *UX overhaul:* Replace the current information-architecture nav with a task-first “What are you trying to do?” router, clearer labels (e.g. “Start Here” instead of “Plan”), a persistent progress stepper, homepage search, and filtered views for the large Appendix.  
- *Accessibility/SEO:* Ensure semantic HTML, ARIA roles, alt text, meta tags, and mobile-friendly design.  
- *Technical implementation:* Provide code diffs for HTML/CSS/JS and Netlify config changes. Suggest progressive enhancement (e.g. working without JS, transparent data loading notices). 

All instructions are formatted as actionable Markdown tasks; sample code and diff snippets show precisely how to update files. The result will be a cohesive, branded, and navigable site that guides local users through regional promotion workflows rather than just listing links.

## 1. Current Site Inventory

- **Technology:** Static site (likely Eleventy or similar) hosted on Netlify. No CMS; content in HTML/JS files.  
- **Pages/Routes:**  
  - **Home:** Hero section with **role-cards** for user types (New business, Maker, Nonprofit, etc.), an overview statement, and a site-wide “Find” menu (Plan, Network, Amplify, Post) and “Use” menu (Templates, Submit, Appendix).  
  - **Plan (Start Here):** Introduction and a *Use-By-Need* table mapping user tasks (e.g. “Post an event”, “List a business”) to starting sections of the guide.  
  - **Network (Directories & Leads):** A filterable table of ~456 local listings and leads, grouped by county/region (Colfax, Las Animas, Huerfano, Tri-County). Filters include listing layer, resource type, access mode, confidence, county. Each row has contact info. (The site calls this page “Network” or “Directories”.)  
  - **Amplifiers (Where to Promote):** Explanations of channel types (calendars, newsletters, directories, visitor guides, etc.) and usage notes for each. Possibly “Amplifiers” in nav.  
  - **Post (Event Posting Map):** Likely a description or map of event calendars or “where to submit events.” (Nav label “Post” is unclear.)  
  - **Region:** (Should be renamed “Regional Overview”) Provides summary of Tri-County area or contains links to county pages.  
  - **County Pages (Colfax, Las Animas, Huerfano):** Each page lists local organizations, contacts, and resources specific to that county/region.  
  - **Templates (Copy Templates):** Ready-to-use email/call scripts for business listings, event submissions, media outreach, etc.  
  - **Submit (Suggest/Correct Listing):** A form/page for adding or correcting leads. (Currently has placeholder email and address.)  
  - **Appendix (Full Contact Table):** A master list of all 456 entries in one table, possibly requiring JS for filtering/search.  

- **Navigation Systems:** The main navigation is split into three groups: **Find** (Plan, Network, Amplify, Post), **Counties** (Regional Overview, Colfax, Las Animas, Huerfano), and **Use** (Templates, Submit, Appendix). A **role-based quickstart** (e.g. “New business owner?”) also links to relevant pages. This mixes **process-based**, **geography-based**, and **utility-based** navigation, which can confuse task-oriented users. 

- **Assets:** 
  - **Logo:** It’s unclear if a logo is used; likely no distinct logo beyond text. A small logo (possibly the Super Eukarya “gear” image) appears in Supereukarya’s site but not on this site.  
  - **Colors:** Presumably default text-on-white or light-gray scheme. No evidence of Raton’s brown/orange/teal palette yet.  
  - **Fonts:** Likely default web-safe fonts (sans-serif). No branding fonts applied.  
  - **Placeholder Contacts:** On the Submit page, the contact info uses placeholders (`updates@statelineguide.example`, fake phone) – these must be replaced or clearly labeled as draft.  

- **Templates:** Static copy templates (email/letter bodies) are provided in the Templates page. These are grouped by use-case. They include sample subject lines and bullet lists.

## 2. Branding Guidelines

### Super Eukarya (Niko Ibáñez / Your Studio)

- **Core Values (Brand Essence):** Scientifically rigorous, systems-driven, technically proficient, yet creative and community-focused. As the site says, it is “Scientifically-Minded. Technically-Driven. Creatively Built,” focusing on “systems thinking with editorial precision” to create “communication and design solutions that work in practice”. The tone is collaborative, precise, and oriented toward real-world impact. Emphasize clarity, evidence-based design, user-centered workflows.  
- **Logo/Name:** Uses an abstract cell-inspired logo (seen on [Supereukarya.com](https://www.supereukarya.com) and [Resources page](https://www.supereukarya.com/resources-and-press/)). The text “Super Eukarya” is often paired with “Design”. Color variations include purple (magenta) and dark blue versions (see [3] and [5]). If crediting Super Eukarya, consider using a small icon or text credit.  
- **Colors:** On the website, Supereukarya’s palette includes a **magenta (#c71585)** and a **dark blue (#004070?)** (from the logo images [3] and [5]). Text and UI currently use dark gray/black on white. As brand guidelines are not publicly published, defaults (dark text, white background) are acceptable. If desired, one might introduce a highlight color (e.g. magenta) for links/buttons to match the logo, but use sparingly for accessibility.  
- **Typography:** The Supereukarya site uses a simple sans-serif font (likely system UI or a web font). No specific typeface mandated. We should keep typography clean and legible (sans-serif headings/bodies) and match the minimal, technical style.  
- **Tone:** Professional, collaborative, and solution-oriented. Avoid casual or overly colloquial language. Use active voice, precise terms, and explain acronyms or local jargon for a broad audience.  

### City of Raton Branding

- **Brand Essence:** Raton’s tourism brand emphasizes the Raton Pass and outdoor adventure. The tagline “**Raton is your pass to adventures!**” (or simply “Your Pass to Adventure”) anchors the identity. This plays on the city’s unique Raton Pass (the highest point on the Santa Fe Trail) and invites visitors to explore (“the use of ‘your’ invites visitors to enjoy all we have to offer”). The brand promotes travel, motion, landscape, connection, and light (sunrise/sunset imagery). It reflects western mining history (underline as a “strike in the earth” for mining). The tone is friendly, adventurous, and community-proud.  
- **Logo:** The city commissioned a custom wordmark “RATON” with railroad-inspired typography and a circular graphic (sunset/landscape, steel rail motif). A companion city seal includes Raton Station illustration. If using the official logo, follow these rules: place on solid contrasting background, maintain clear space, don’t alter colors or proportions. However, official assets might not be readily available; at minimum, use the word “Raton” in a bold serif or slab font to suggest the brand (as a placeholder).  
- **Colors:** The brand palette (inspired by the ExploreRaton site) includes **brown (#772816)**, **orange (#D97345)**, and **turquoise (#7ED4D8)**. A light cream (#F3EEDD) background is also shown in designs. If we adopt Raton theming, we should introduce these colors in CSS variables: e.g. `--color-primary: #772816; --color-secondary: #D97345; --color-accent: #7ED4D8; --color-bg: #FFFFFF` (with a cream fallback). Use brown for headers/buttons, orange for highlights, teal for links/buttons (ensure sufficient contrast). Always verify WCAG AA contrast (brown on white is ~7:1).  
- **Fonts:** The official brand used a custom serif/Slab (for “RATON”). Absent that, choose a web font that feels sturdy/western. For example, [Libre Baskerville](https://fonts.google.com/specimen/Libre+Baskerville) or [Arvo](https://fonts.google.com/specimen/Arvo) (serif) or [Roboto Slab]. For body text, a readable sans-serif like [Open Sans] or [Lato].  
- **Tone/Content:** Emphasize collaboration with City of Raton and ExploreRaton. Use local references (Raton Pass, 1891 founding, Sangre de Cristo scenery). For example, page headers or a footer tagline could read: *“Stateline Guide – your pass to connecting rural Colorado and New Mexico communities.”* At minimum, include “Raton” and “Explore Raton” as entities when relevant, crediting The Center for Community Innovation where needed (as seen on [ExploreRaton](https://www.exploreraton.com/about) footer).

## 3. Brand Alignment and Gaps

We map current site elements to these brand rules:

- **Color:** The site currently uses no distinct palette. *Gap:* It lacks Raton’s brown-orange-teal palette. **Risk:** The site feels generic and not “of Raton.” *Action:* Introduce Raton palette via CSS. For example, set a warm brown for primary text/headings, orange for buttons, teal for links (with dark text fallback). Also consider Supereukarya’s magenta as an accent if needed (use sparingly for logos or highlights to reflect the design firm’s signature color).  
- **Typography:** The site likely uses default fonts. *Gap:* No branded typeface. **Risk:** Low brand recognition; might fail accessibility if fonts not optimized. *Action:* Choose web fonts consistent with brand (see above). Ensure base font is legible (>=16px) and headings have clear hierarchy.  
- **Logo/Images:** The site appears to have no distinctive logo. *Gap:* Missing Raton logo or Supereukarya credit. **Risk:** Unbranded appearance, missed legal attribution. *Action:* If possible, insert a small Raton wordmark or a placeholder (“[City of Raton logo]”) near the site title. Or add “Powered by Super Eukarya” in footer with their logo/icon. Replace generic “StatelineGuide.example” placeholders with real contact/email or remove them entirely.  
- **Tone & Content:** The site copy (“local promotion operating manual”) is neutral and procedural, which aligns with Super Eukarya’s straightforward style but currently lacks Raton-specific flavor. *Gap:* No mention of Raton’s tagline or local pride. **Risk:** Users may not realize this is a collaborative City project. *Action:* Add a tagline or header on the homepage like “Your Pass to Rural Promotion – Colfax · Las Animas · Huerfano” to hint at Raton’s theme. Include Raton or Explore Raton mentions in intro text. Use "we" and "you" addressing local promoters to be engaging.  
- **Accessibility:** The site’s design was not fully audited. *Gaps:* Potential missing alt text on images (e.g. hero images for roles), no skip-nav link (accessible on Raton.gov), color contrast unknown. **Risk:** Fails WCAG 2.1 AA. *Action:* Add `alt` to all images, `aria-labels` for icons, ensure keyboard focus styles, and add `<a href="#main-content">Skip to main content</a>` at top. Use semantic HTML5 landmarks (nav, main, header, footer).  
- **Legal/Attribution:** If using Raton’s brand assets (logo, seal, tagline), we must credit the city (e.g. “Official City of Raton mark™” and “© 2026 City of Raton”). *Gap:* The site has none. *Action:* In footer, add “City of Raton logo and tagline used with permission” if applicable, and “© 2026 City of Raton.”

## 4. Codex-Ready Implementation Tasks

Below we present detailed Markdown tasks with code snippets/diffs. Paths (e.g. `/src/layout.html`) are illustrative; adjust to your project structure (e.g. Eleventy includes, Handlebars, SvelteKit files). Each task includes a description, sample code diff, and a test/verification step.

### 4.1 Rename Navigation Labels 

**Goal:** Replace ambiguous labels with user-friendly terms (see table below). Ensure all navigation (top-level and internal links) use the new text and URLs if renamed.

| Current label | New label / URL            | Example path    |
| ------------- | -------------------------- | --------------- |
| Plan          | **Start Here**             | `/plan` → stays `/plan` (change text) |
| Network       | **Directories & Leads**    | `/network` or `/directories`       |
| Amplify       | **Where to Promote**       | `/amplifiers` → `/amplifiers` (text) |
| Post          | **Event Posting Map**      | `/post` → `/post` (text)         |
| Region        | **Regional Overview**      | `/region` or `/index`?             |
| Templates     | **Copy Templates**         | `/templates`         |
| Submit        | **Suggest / Correct Listing** | `/submit`   |
| Appendix      | **Full Contact Table**     | `/appendix`       |

> *Note:* If changing URLs for SEO (e.g. `/start` instead of `/plan`), create redirects in `_redirects` or Netlify config.

**File:** `src/layout.html` (or wherever the nav is defined)  
```diff
<!-- Top navigation (example) -->
<nav>
  <ul>
-   <li><a href="/plan">Plan</a></li>
+   <li><a href="/plan">Start Here</a></li>
-   <li><a href="/network">Network</a></li>
+   <li><a href="/network">Directories &amp; Leads</a></li>
-   <li><a href="/amplifiers">Amplify</a></li>
+   <li><a href="/amplifiers">Where to Promote</a></li>
-   <li><a href="/post">Post</a></li>
+   <li><a href="/post">Event Posting Map</a></li>
  </ul>
  <ul>
-   <li><a href="/region">Region</a></li>
+   <li><a href="/region">Regional Overview</a></li>
    <li><a href="/colfax">Colfax County</a></li>
    <li><a href="/las-animas">Las Animas County</a></li>
    <li><a href="/huerfano">Huerfano County</a></li>
  </ul>
  <ul>
-   <li><a href="/templates">Templates</a></li>
+   <li><a href="/templates">Copy Templates</a></li>
-   <li><a href="/submit">Submit</a></li>
+   <li><a href="/submit">Suggest / Correct Listing</a></li>
-   <li><a href="/appendix">Appendix</a></li>
+   <li><a href="/appendix">Full Contact Table</a></li>
  </ul>
</nav>
```
**Test:** Load each link; verify the header on each page shows the new label. The **browser’s title** and any internal headings should match (update `<title>` tags if needed for SEO).

### 4.2 Add “What Are You Trying to Do?” Router on Home 

**Goal:** Introduce a task-based “router” section on the homepage to funnel users by goals. Place it near top (under main intro) with large buttons/icons.

**File:** `src/index.html` or homepage template.  
```diff
@@
+<section id="task-router" aria-label="Quick task navigation">
+  <h2>What are you trying to do?</h2>
+  <div class="tasks-grid">
+    <a class="task-button" href="/amplifiers" role="button">Promote an event</a>
+    <a class="task-button" href="/network" role="button">Get listed somewhere</a>
+    <a class="task-button" href="/amplifiers" role="button">Find advertising/newsletter channels</a>
+    <a class="task-button" href="/submit" role="button">Fix or update a listing</a>
+    <a class="task-button" href="/templates" role="button">Prepare a promo packet</a>
+    <a class="task-button" href="/regional-overview" role="button">Find county contacts</a>
+  </div>
+</section>
```
You may create CSS `.tasks-grid` (e.g. `display: grid; grid-template-columns: repeat(auto-fit,minmax(200px,1fr)); gap:1em;`) for responsiveness, and style `.task-button` as large cards or buttons. 

**ARIA:** Buttons have `role="button"` and clear labels. Include `aria-label` if button text is not descriptive (here they are). 

**Test:** On homepage, the new section should appear with six clearly labeled buttons. Tab order should highlight each button. On click, each goes to the intended page. On small screens, verify the grid wraps nicely.

### 4.3 Add Persistent Progress Stepper

**Goal:** Show a horizontal stepper/progress indicator on every page, reflecting the user workflow: 1) Choose goal, 2) Prepare packet, 3) Pick channel, 4) Submit/contact, 5) Track result. Use semantic structure.

**File:** e.g. `src/_includes/stepper.html` (included in layout).  
```html
<nav aria-label="Steps" class="stepper">
  <ol>
    <li><a href="/plan" aria-current="step">1. Choose goal</a></li>
    <li><a href="/templates">2. Prepare packet</a></li>
    <li><a href="/network">3. Pick channel</a></li>
    <li><a href="/submit">4. Contact</a></li>
    <li><a href="/track">5. Track</a></li>
  </ol>
</nav>
```
- Use `aria-current="step"` on the current step (dynamically add class/attribute in templates). 
- Style `.stepper ol` with `display:flex; list-style:none;` and markers/lines via CSS. 

```css
/* Example CSS */
.stepper ol { display: flex; padding: 0; margin: 1em 0; }
.stepper li { flex: 1; text-align: center; position: relative; }
.stepper li + li:before {
  content: ""; width: 100%; height: 2px; background: #ccc; position: absolute; top: 50%; left: -50%;
}
.stepper a { display: inline-block; padding: 0.5em; color: #333; text-decoration: none; }
.stepper [aria-current="step"] a { font-weight: bold; color: #D97345; } /* highlight current */
```

**Test:** The stepper should appear on every page (usually at top under nav). On each page, one step should be highlighted (via `aria-current="step"` or a CSS class on the current list item). Verify with keyboard: the list should be read as steps. 

### 4.4 “Recommended Next Step” Buttons on Each Page

**Goal:** At the end of each main section/page, add one or two large CTA buttons guiding the user to the logical next page. 

**Example:** On **Plan** page, after content:
```html
<section class="next-step">
  <h3>Next Steps</h3>
  <a href="/network" class="button">Find Directories &amp; Leads</a>
  <a href="/templates" class="button">Use Copy Templates</a>
</section>
```
On **Network** page:
```html
<section class="next-step">
  <h3>Next Steps</h3>
  <a href="/amplifiers" class="button">Open Promotion Channels</a>
  <a href="/submit" class="button">Submit a Correction</a>
</section>
```
Repeat similar for Amplifiers, Templates, etc. Each button should have an ARIA role if styled as button (e.g. `role="button"`), and a clear label.

**Test:** Scroll to bottom of each page; ensure one or two buttons appear with descriptive text. They should stand out (colored background, padded). Clicking them goes to the intended section.

### 4.5 Add Homepage Search Field

**Goal:** Provide a search box on the homepage (and keep it on all pages, e.g. header) so users can quickly find a business, calendar, or keyword. Implement as progressive enhancement: works with JS if available, but degrade gracefully.

**File:** `src/layout.html` (header)  
```html
<form id="site-search-form" action="/search" method="get" class="search-form">
  <label for="site-search" class="visually-hidden">Search listings, calendars, or keywords</label>
  <input type="search" id="site-search" name="q"
         placeholder="Search businesses, calendars, media channels..."
         aria-label="Search listings and channels">
  <button type="submit">Search</button>
</form>
```
- The form posts to `/search` (or `/network` with query param; implement a simple search page or JS filter).  
- Add `.visually-hidden` CSS for screen-reader-only labels.  
- On the homepage, make this prominent (e.g. top bar or just under hero text). 

**Test:** Try searching a known term from the Appendix. If implemented server-side, results should filter; if client-side JS, test filtering. Without JS, the form still submits to a results page (implement or redirect to Appendix with query). Ensure search input has accessible label. 

### 4.6 Appendix Filters and Views

**Goal:** Split the 456-entry Appendix into filtered views by category (e.g. “Official Sources”, “Event Calendars”, “Media”, “Needs Verification”, etc.) to reduce information overload.

**Approach:** Add a toolbar above the table:
```html
<nav aria-label="Appendix filters" class="filter-toolbar">
  <button data-filter="all" class="filter-btn">Show All</button>
  <button data-filter="official" class="filter-btn">Official/Public Sources</button>
  <button data-filter="calendar" class="filter-btn">Event Calendars</button>
  <button data-filter="newsletters" class="filter-btn">Newsletters</button>
  <button data-filter="directories" class="filter-btn">Business Directories</button>
  <button data-filter="media" class="filter-btn">Media Outlets</button>
  <button data-filter="venues" class="filter-btn">Venues / Arts</button>
  <button data-filter="verify" class="filter-btn">Needs Verification</button>
</nav>
```
Each `button` when clicked should filter the table rows (via JavaScript, adding/removing `hidden` or using CSS classes). Use `aria-pressed` on toggle or simply normal buttons that re-render table view. 

**Test:** Click each filter button; only relevant rows should be visible. Verify that “Show All” resets filters. Use `aria-label` or visible text. Ensure the toolbar is keyboard accessible (buttons focusable, OR role="button" if using non-button elements).

### 4.7 Submission Flow Branching Form

**Goal:** Instead of showing a long form at once, first ask what type of submission the user is making to branch the form dynamically.

**File:** `src/submit.html`  
```html
<form id="submission-type-form">
  <fieldset>
    <legend>What are you submitting?</legend>
    <label><input type="radio" name="submitType" value="newListing"> New listing</label><br>
    <label><input type="radio" name="submitType" value="correction"> Correction</label><br>
    <label><input type="radio" name="submitType" value="eventCalendar"> Event calendar submission</label><br>
    <label><input type="radio" name="submitType" value="newsletter"> Newsletter / advertising</label><br>
    <label><input type="radio" name="submitType" value="mediaOutlet"> Media outlet</label><br>
    <label><input type="radio" name="submitType" value="venue"> Venue / Arts space</label><br>
    <label><input type="radio" name="submitType" value="remove"> Remove outdated listing</label>
  </fieldset>
</form>
<!-- Then separate fieldsets or divs for each form type -->
<div id="form-newListing" class="submit-section hidden">
  <!-- Fields for new listing -->
</div>
<div id="form-correction" class="submit-section hidden">
  <!-- Fields for correction -->
</div>
<!-- etc. -->
```
Add a script (or progressive HTML solution) that shows the relevant section when a radio is selected:
```js
document.getElementById('submission-type-form').addEventListener('change', function(e){
  const type = e.target.value;
  document.querySelectorAll('.submit-section').forEach(div => div.classList.add('hidden'));
  document.getElementById('form-' + type).classList.remove('hidden');
});
```
Ensure `hidden` class hides content (`display:none`) but remains accessible once revealed.

**Test:** Initially only the radio list shows. Selecting “New listing” unhides the new listing fields, etc. All inputs must have labels. If no JS, provide all fields in sequence or an anchor link to them.

### 4.8 Color and Logo Assets

**Goal:** Integrate official logos and colors. 

- **Assets to obtain:**  
  - Raton logo (“RATON” wordmark) and City seal (from City or tourism office). If unavailable, use a high-quality placeholder or the crest from [ExploreRaton (footer)](https://www.ratonnm.gov/_assets_/images/logo_white.svg?) or [Behance images].  
  - Explore Raton (“Your Pass”) vector or font.  
  - Super Eukarya icon (optional) for footer/credit.  
  - Font files or Google Fonts as chosen (e.g. Arvo, Open Sans).  

- **Fallbacks:** If official logos are unavailable, use text: e.g. `<div class="logo">RATON</div>` in the new font. For colors, define CSS custom properties with Raton hex codes:
  ```css
  :root {
    --color-raton-brown: #772816;
    --color-raton-orange: #D97345;
    --color-raton-teal: #7ED4D8;
  }
  header { background: var(--color-raton-brown); color: #fff; }
  a { color: var(--color-raton-teal); }
  button, .button { background: var(--color-raton-orange); color: #fff; }
  ```
- **Logo usage:** Insert Raton logo into the header (if available) with `width` no more than 150px, alt text “City of Raton logo”. Wrap in `<a href="https://ratonnm.gov" target="_blank">`. For Supereukarya credit, add small text in footer: “Site by Super Eukarya” linking to https://www.supereukarya.com.

**Test:** Verify logos display properly (with transparent backgrounds). Check color contrast (brown on white > AA, orange on white passes AA). If using brown background, ensure white text is AA (yes, #fff on #772816 is ~9:1). Ensure accessible fallback (if images fail, alt text shows).

### 4.9 Accessibility & SEO Checks

**Goal:** Ensure all new elements meet accessibility and SEO standards.

- **Landmarks & ARIA:** Add `<a href="#main" class="skip-nav">Skip to main content</a>` at top. Wrap main page content in `<main id="main">`. Ensure all `<nav>` have `aria-label`. All images use `alt`. Form elements have `label for`. Add `lang="en"` on `<html>`.  
- **Headings:** Only one `<h1>` per page. Use `<h2>`, `<h3>` in logical order. The homepage might have `<h1>` on the main title, and “What are you trying to do?” as `<h2>`.  
- **Meta Tags:** In `<head>`, include a `<title>` reflecting the new Start Here name (e.g. “Stateline Guide – Start Here”), and `<meta name="description" content="A rural marketing guide for Colfax, Las Animas, and Huerfano counties. Learn where to promote events, list businesses, find channels, and more.">`. Add `<meta name="viewport" content="width=device-width, initial-scale=1">`.  
- **Progressive Enhancement:** Ensure core functionality works with JS off. The site already loads without JS (table visible). Keep forms and links functional. Use `noscript` notices if necessary.  
- **SEO:** Add `<meta charset="UTF-8">`. Use meaningful page titles (e.g. “Copy Templates – Stateline Guide”). On images, use descriptive `alt` (e.g. `<img src="logo.png" alt="Stateline Guide logo">`).  
- **Accessibility Testing:** Use a tool like WAVE or Axe to scan pages. Check color contrast (WCAG AA), keyboard navigation, form labels, aria roles. Adjust as needed.  

**Test:** Run an accessibility audit (e.g. Chrome Lighthouse). All pages should be navigable via keyboard (Tab through). The search form and new buttons are reachable and announced. Verify SEO: Google’s Structured Data (if any), verify robots.txt exists (if needed), and that the site maps properly.

### 4.10 Content and Copy Updates

**Goal:** Revise site copy for clarity, user-centric language, and SEO keywords. 

- **Homepage Header:** Change generic title to something like “Stateline Promotion Guide” and tagline:  
  ```html
  <h1>Stateline Regional Promotion Guide</h1>
  <p class="tagline">A practical routing guide for getting listed, posted, promoted, and verified across Colfax, Las Animas, and Huerfano counties.</p>
  ```
- **"Why not Google?" Explanation:** Near top or bottom of homepage or “Start Here” page, add a short paragraph:  
  > *“Why not just Google it?* Because this guide goes beyond search results. It tells you **which channel to use first, what materials to prepare, and what to verify** at each step. Think of it as a local marketing *roadmap*, not another generic directory.”*

- **Role Cards:** If keeping role-based quick starts (e.g. New Business, Artist, etc.), consider combining with task router. At most, present tasks first, then role. Clarify labels (e.g. instead of “New Business Owner?”, say “I’m starting a business”). Ensure each card title is a plain `<h2>` or link, and paragraphs are short.

- **Footer:** Add links to Raton (“City of Raton official website”), Explore Raton, and Super Eukarya with appropriate text:  
  ```html
  <footer>
    <p>Content curated by the Center for Community Innovation and City of Raton. © 2026 City of Raton.</p>
    <p>Powered by <a href="https://www.supereukarya.com" target="_blank">Super Eukarya Design</a>.</p>
  </footer>
  ```

**Test:** Proofread all text for grammar, clarity. Titles reflect content. The “why not Google” line should be easily found. All links in footer should work. The main tagline should include county names for SEO (keywords: Colfax, Las Animas, Huerfano, tourism, event calendar).

### 4.11 Example Code Snippet: HTML + ARIA

Below is an annotated example of a homepage section with ARIA roles and tasks:

```html
<!-- Skip link for accessibility -->
<a href="#main" class="skip-nav">Skip to main content</a>

<header role="banner">
  <a href="/" aria-label="Stateline Guide home"><img src="/images/stateline-logo.svg" alt="Stateline Guide logo"></a>
  <!-- Navigation as updated above -->
  <nav aria-label="Primary Navigation">…</nav>
</header>

<main id="main" role="main">
  <section id="hero">
    <h1>Stateline Regional Promotion Guide</h1>
    <p class="tagline">A practical routing guide for promoting your business or event in the three-county area.</p>
    <!-- Task-based router inserted here -->
  </section>
</main>

<footer role="contentinfo">
  <p>© 2026 City of Raton. Content by <a href="https://centerci.org">Center for Community Innovation</a>.</p>
  <p>Powered by <a href="https://www.supereukarya.com" target="_blank">Super Eukarya</a>.</p>
</footer>
```

## 5. Implementation Plan and Roadmap

Below is a **prioritized task list**. Each item includes estimated effort (L=Low, M=Medium, H=High) and acceptance criteria (how we’ll know it’s done). The tasks should be executed in order:

| Priority | Task                                    | Effort | Acceptance Criteria                                           |
|----------|-----------------------------------------|--------|---------------------------------------------------------------|
| 1        | **Replace placeholder contact info:** Update email/phone on Submit page. (If not ready, add “Pilot version” note.) | L | Real contact/form in place. No “example” addresses remain.  |
| 2        | **Rename nav labels** (Sec 4.1)         | L      | All nav items updated. `find` in code shows no old labels.    |
| 3        | **“What are you trying to do?” router** (4.2) | M | Six buttons on home linking correctly. ARIA roles set.        |
| 4        | **Persistent stepper** (4.3)            | M      | Stepper visible on pages, highlights current step.           |
| 5        | **Next-step buttons** (4.4)             | M      | Each page has relevant CTA(s) at bottom. Buttons tested.      |
| 6        | **Homepage search** (4.5)               | M      | Search field appears and returns relevant results.           |
| 7        | **Appendix filters** (4.6)              | H      | Filter toolbar filters the table. All filter options function. |
| 8        | **Submit form branching** (4.7)         | M      | Only chosen section shows. All form fields labeled.           |
| 9        | **Color palette integration** (4.8)     | M      | CSS updated with brand colors. Contrast passes WCAG AA.       |
| 10       | **Add logos and branding** (4.8)        | M      | Raton logo and Supereukarya credit added.  Fonts loaded.      |
| 11       | **Accessibility fixes** (4.9)           | H      | No major A11y issues (Lighthouse score > 90).                |
| 12       | **Content copy updates** (4.10)         | L      | Taglines and text updated as per spec. Typo-free.            |
| 13       | **SEO/meta tags** (4.9)                 | L      | Titles/descriptions added. Structured data (if needed).       |
| 14       | **Testing & QA**                        | H      | Manual and automated tests passing. Cross-browser checks.     |

**Notes:** Items 2–8 can be done in parallel by splitting into smaller tasks per page. Filtering (8) is largest. Time estimates assume a single developer; adjust if working in team. 

## 6. Navigation and Component Diagrams

### Site Navigation Flow

```mermaid
graph LR
  A[Home (Start Here)] --> B[Plan (Start Here)]
  A --> C[Directories & Leads]
  A --> D[Where to Promote]
  A --> E[Event Posting Map]
  A --> F[Templates]
  A --> G[Suggest/Correct Listing]
  A --> H[Regional Overview]
  H --> I[Colfax County Page]
  H --> J[Las Animas County Page]
  H --> K[Huerfano County Page]
  C --> L[Appendix (Full Table)]
  subgraph TaskFlow ["User Tasks"]
    B --> G
    B --> F
    C --> D
    D --> G
  end
```

This flowchart shows the homepage (“Start Here”) linking to major sections. Shaded “TaskFlow” illustrates a typical user path: plan → search listings → choose channels → submit.

### Rollout Gantt Chart

```mermaid
gantt
    title Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Setup
    Replace placeholders:          done, after 2026-06-24, 1d
    Rename nav labels:            done, after 2026-06-25, 1d
    section Home & Navigation
    Task router & stepper:        active, 2026-06-26, 3d
    Next-step buttons:            after router, 2d
    Homepage search:              after router, 3d
    section Listings & Forms
    Appendix filters:             2026-06-29, 5d
    Submit form branching:        2026-07-05, 2d
    section Branding
    Add Raton colors/fonts:       2026-06-28, 2d
    Insert logos & credits:       after colors, 1d
    section QA & Launch
    Accessibility audit:          after all dev, 2d
    Content review & SEO:         parallel, 3d
    Final testing & deployment:   after all changes, 2d
```

## 7. References

- Super Eukarya “About” and “Marketing, Design & Web” pages for brand values (scientific, user-centered design).  
- Explore Raton official site for tagline and colors.  

Each of these tasks and guidelines ensures the site remains **user-friendly, accessible, and consistent with both Super Eukarya’s technical design philosophy and Raton’s adventure-branding**. The provided code samples and Mermaid diagrams should guide the development team to implement these changes methodically and test thoroughly.
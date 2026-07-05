# Super Eukarya Visual + UX Implementation Notes

## Visual assets
Copy the SVG files in `/assets` into the site repo, preferably `public/assets/super-eukarya/` or `src/assets/super-eukarya/`. Use them as section dividers, figure blocks, or decorative-but-semantic illustrations with `alt` text.

## Design/UI/UX changes to implement

1. Remove all “brochure” framing from intro copy. The site is a regional outreach/resource guide, not a brochure.
2. Use Super Eukarya color roles: navy for depth, cream for readability, gold for authority/accent, teal for identity/default, blue for structure, orange for activation, green for growth, red only for urgent warnings.
3. Replace long uninterrupted text blocks with modular section cards, numbered procedural labels, and gold divider rules.
4. Keep hierarchy left-aligned. Avoid center-heavy generic landing-page composition.
5. Add visual figures between dense sections: system map near introduction, visibility stack near marketing, accessibility figure near accessibility, funding pipeline near funding, cross-promotion loop near retail.
6. Use icons as systems: nodes, lines, grids, branching routes. Do not use generic stock icons.
7. Improve table usability: add horizontal scroll wrappers, sticky headers only if not disruptive, caption each table, and reduce cell crowding.
8. Improve nav: make sticky nav less tall on mobile, add “back to top,” and highlight active section with IntersectionObserver.
9. Keep Persona Finder, but add clearer empty state and loading/fallback text for JavaScript failure.
10. Add `noscript` fallback explaining that the long-form guide below remains usable without scripts.
11. Add accessible alt text or `aria-labelledby` to every SVG. Avoid baking text into purely decorative SVGs.
12. Make focus states visible using gold outline on navy/cream.
13. Avoid using color alone for status dots; include status text.
14. Reduce motion unless user has not requested reduced motion; honor `prefers-reduced-motion`.
15. Add source/update metadata near each inventory section: date, source type, verification confidence, and last reviewed.
16. Clean “null” text from visible data cards; suppress empty fields instead.
17. Add print CSS: hide nav/search controls, show URLs after links, preserve tables, and avoid splitting table rows across pages.
18. Add download/export affordances: HTML, CSV resources, PDF print view.
19. Ensure body text is clean sans-serif with generous leading; reserve bold condensed/all-caps for headlines only.
20. Keep one functional accent at a time per section; do not mix every accent color in one component.

## Suggested insertion map

- `se_system_map.svg`: below hero or after introduction.
- `se_persona_finder_diagram.svg`: beside/inside Persona Finder explanation.
- `se_tri_county_route_nodes.svg`: County Index & Community Directory.
- `se_visibility_stack.svg`: Marketing & Promotion Support.
- `se_accessibility_contrast.svg`: Accessibility Checklist.
- `se_bulletin_media_network.svg`: News, Advertising, and Bulletin Board sections.
- `se_funding_pipeline.svg`: Funding & Financing.
- `se_cross_promotion_loop.svg`: Retail & Entrepreneurship Strategy.

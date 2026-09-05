# Yucca Banner Animation

This folder contains a production-friendly animated SVG banner for the Tri-County Regional Marketing Guide.

## Files

- `yucca-banner.svg` - layered animated SVG with mountains, plains, yucca leaves, flower stalks, blossoms, wind lines, petals, and a CTA ribbon.
- `yucca-banner.css` - wrapper, preview, CTA hover, and reduced-motion styles.
- `yucca-banner.html` - standalone preview page.
- `yucca-cta-loop.svg` - reusable animated CTA marker.

## Why SVG/CSS

The banner is rebuilt as vector layers instead of animating the source PNGs. This keeps the Netlify page lightweight, sharp on high-resolution screens, and easy to pause for reduced-motion users.

## Recommended Use

Use `yucca-banner.svg` as the visual hero background or inline it when deeper control is needed. Use `yucca-cta-loop.svg` sparingly on forward-moving calls to action.

## Motion Layers

| Layer | Animation |
| --- | --- |
| Background mountains | Very slow parallax |
| Plains / desert floor | Very slow overscanned parallax |
| Yucca leaves | Tiny rotational sway |
| Yucca flower stalks | Gentle 6-8 second wind sway |
| Individual blossoms | Delayed micro-sway |
| Wind lines | Slow horizontal drift |
| CTA ribbon / marker | Subtle pulse |

## Raton Brand Palettes

The site and animation family use three separately documented color systems observed on the
current public websites for the City of Raton, Explore Raton, and GrowRaton. They are not collapsed
into a generic Southwest palette. City-led scenes use turquoise, teal, brick, brown, sand, and
cream; Explore-led scenes use turquoise, blue, rust, orange, pale aqua, and cream; GrowRaton-led
scenes use orange, deep green, burgundy, gray, and a limited bright blue.

This implementation reflects the organizations' public web presentation and does not claim formal
brand approval. Exact source colors, font-family observations, page mappings, and license-safe
fallbacks are recorded in `docs/raton-brand-system.md`.

## Edge Coverage

Every full-width moving landscape layer must remain wider than the `1600 x 720` view box at
both ends of its motion. Generated far and mid layers use at least `scaleX(1.014)` and plains
layers use at least `scaleX(1.012)`. Hand-drawn edge shapes must extend beyond the view box.
The `data-edge-overscan="true"` marker is enforced by the maintenance test.

## Reduced Motion

Both SVGs include reduced-motion handling. The CSS also includes the requested pattern:

```css
@media (prefers-reduced-motion: reduce) {
  .yucca-sway,
  .wind-line,
  .cta-pulse {
    animation: none !important;
  }
}
```

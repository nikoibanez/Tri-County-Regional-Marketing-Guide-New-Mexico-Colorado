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

## Brand Palettes

The animation family uses three complementary Raton identities. Landscape files declare their
assigned family with `data-brand-palette` so future revisions can preserve the system.

- **City of Raton:** turquoise `#21bdc5`, deep teal `#147176`, rust `#772816`, sand `#b3b078`, and cream `#eeedd6`.
- **Explore Raton:** blue `#2b5672`, deep blue `#22495a`, orange `#d97345`, pale aqua `#aae8ec`, warm brown `#775751`, and cream `#eeedd6`.
- **Raton MainStreet:** plum `#6c1c5b`, mauve `#a06393`, olive `#716c2c`, mist blue `#c8d5dc`, charcoal `#2a2a2a`, and near-white `#f3f5f8`.

Reference sites: [City of Raton](https://www.ratonnm.gov/), [Explore Raton](https://www.exploreraton.com/), and [Raton MainStreet](https://ratonmainstreet.org/).

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

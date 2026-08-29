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

## Raton-Inspired Palette

The site and animation family share a restrained high-desert palette inspired by the public
visual character of City of Raton, Explore Raton, Grow Raton, and Raton MainStreet. This is a
locally derived design system, not a claim of formal brand approval or an exact reproduction of
any organization's brand kit.

The shared core is civic brick `#772816`, warm orange `#d97345`, turquoise `#7ed4d8`, and pale
high-desert cream `#f3eedd`. Deep navy `#173047`, blue `#22495a`, and teal `#147176` provide
legible shadows, text-adjacent accents, and foreground plants. Each landscape varies the balance
of those colors while remaining visibly part of one family.

The palette decision is recorded in `data/source-notes/deep-research-report_10.md`. Reference
sites include [City of Raton](https://www.ratonnm.gov/), [Explore Raton](https://www.exploreraton.com/),
[Grow Raton](https://www.growraton.org/), and [Raton MainStreet](https://ratonmainstreet.org/).

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

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
| Plains / desert floor | Static |
| Yucca leaves | Tiny rotational sway |
| Yucca flower stalks | Gentle 6-8 second wind sway |
| Individual blossoms | Delayed micro-sway |
| Wind lines | Slow horizontal drift |
| CTA ribbon / marker | Subtle pulse |

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

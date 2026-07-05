# Codex Regional Audio Implementation

Integrate the regional archival audio package without rebuilding the whole site.

## Steps

1. Copy `data/regional_audio_manifest.json` into `/data/`.
2. Copy `assets/regional-audio-registry.js` into `/assets/`.
3. Merge `assets/regional-audio.css` into `/assets/styles.css` or include it separately.
4. Download MP3 files from each LOC item page in `regional_audio_manifest.csv`.
5. Save them in `/assets/audio/` using `local_audio_filename_recommended`.
6. Insert `snippets/regional-audio-section.html` where the regional audio feature should appear.
7. Keep the credit line visible.
8. Do not autoplay audio by default. If a user-initiated play button is used, provide a clear pause/stop button.

## Warning text to display

Regional archival audio is provided as cultural context. Rights statements are reviewed source-by-source; users should confirm reuse terms before redistribution, remixing, or commercial use.

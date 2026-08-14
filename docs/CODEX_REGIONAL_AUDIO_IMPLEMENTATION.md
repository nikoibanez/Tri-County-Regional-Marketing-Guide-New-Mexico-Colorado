# Regional Audio Implementation

The canonical site generator reads `data/regional_audio_manifest.json` directly. Do not maintain a second JavaScript or CSV track registry.

## Adding A Track

1. Confirm the item page names the recording, performers, place, source collection, and reuse status.
2. Add the source URL, rights note, credit line, player label, and final local filename to `data/regional_audio_manifest.json`.
3. Download the approved audio into `assets/audio/` using that exact filename.
4. Set `local_audio_downloaded` to `true` only after the local file exists.
5. Add the full source trail to `assets/audio/README.md`.
6. Run the canonical build and `python scripts/audit_ui_accessibility.py`.

The player is opt-in, includes play/stop and volume controls, and links the selected track to its source-and-rights page. Contemporary music requires written permission or an explicit compatible license before publication.

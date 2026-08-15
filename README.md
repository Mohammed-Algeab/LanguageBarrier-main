# LanguageBarrier

This is the core runtime component for Committee of Zero's MAGES engine game patches, hooking lots of game engine functions to enable asset access redirection at filesystem and higher levels, rendering changes and many more features.

As we try to support all games and any possible patches with a single binary, extensive external configuration is required (in particular, the hooks here make little sense the signatures pointing to their targets). See the root patch repositories (or patched game installations) for details.

LanguageBarrier source code is [MIT licensed](LanguageBarrier/LICENSE), but due to inclusion of xy-VSFilter, our binaries fall under GPLv2. If this is a problem for you, you must remove the xy-VSFilter dependency by hand.

## Currently supported games

- STEINS;GATE (Steam – 2016)
- STEINS;GATE 0 (Steam – 2018)
- CHAOS;CHILD (Steam – 2019, GOG – 2022)
- STEINS;GATE ELITE (Steam – 2019)
- STEINS;GATE: Linear Bounded Phenogram (Steam – 2019)
- STEINS;GATE: My Darling's Embrace (Steam – 2019)
- ROBOTICS;NOTES ELITE (Steam – 2020)
- ROBOTICS;NOTES DaSH (Steam – 2020)


## Experimental Arabic RTL dialogue mode

The source includes an opt-in `patch.rtlDialogue` mode for the classic dialogue-page renderer. Add the following property to the patch configuration used by the target game:

```json
{
  "patch": {
    "rtlDialogue": true,
    "rtlDialogueRightX": 1200,
    "rtlDialogueKeepNameLine": true,
    "rtlDialogueMirrorGlyphs": false
  }
}
```

When enabled, the main dialogue hook keeps the SC3 text stream and the page iteration order unchanged. With `rtlDialogueMirrorGlyphs: true`, it mirrors each glyph horizontally inside the complete line bounds, so the first logical glyph is placed at the right edge and later glyphs extend toward the left. With `rtlDialogueMirrorGlyphs: false`, it preserves the glyph order supplied by the script and shifts the whole line so its right edge reaches `rtlDialogueRightX`; this is the correct mode when the translated script has already been manually reversed for the Backlog.

`rtlDialogueRightX` is an optional coordinate in the game's logical coordinate system before `coordsMultiplier` is applied. Start with `1200` for STEINS;GATE HD; increase it gradually to `1220` or `1240` if the line still starts too far left, or decrease it if the text crosses the right edge. Omitting the key or setting it to `0` restores the automatic per-line mirror behavior. `rtlDialogueKeepNameLine` first requires the dialogue parser's `name_start` marker, then skips the last Y-line because that is where the speaker name is laid out in the tested STEINS;GATE page. When no name marker exists, no line is skipped and all dialogue lines remain RTL.

The mode is disabled by default and is applied only by the generic `DEF_DRAW_DIALOGUE_HOOK` path. For a script that is already prepared in the visual order required by the Backlog, use `rtlDialogueMirrorGlyphs: false` to avoid a second visual reversal. For a script kept in logical order, use `rtlDialogueMirrorGlyphs: true`.
 It does not alter auxiliary mail, backlog, phone, or newer RNE/RND text paths. It also does not provide Arabic contextual shaping by itself; the configured font must already be suitable for the current glyph pipeline. If Arabic joining forms are not rendered correctly, a separate shaping stage using Uniscribe or HarfBuzz will be required before glyph IDs reach the renderer.

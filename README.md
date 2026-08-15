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
    "rtlDialogueMirrorGlyphs": false,
    "rtlDialogueFlowRTL": true
  }
}
```

When enabled, the main dialogue hook keeps the SC3 text stream and page iteration order unchanged. The two placement controls are independent: `rtlDialogueMirrorGlyphs` decides whether glyph positions are mirrored, while `rtlDialogueFlowRTL` decides whether the renderer consumes the page glyphs from the configured right edge and advances toward the left.

The three useful combinations are:

| Settings | Rendering behavior | Use when |
|---|---|---|
| `rtlDialogueMirrorGlyphs: true` | Mirrors each glyph's position inside the line; the first page glyph is placed on the right and later glyphs extend left. | The script is still in logical, non-reversed order. |
| `rtlDialogueMirrorGlyphs: false` and `rtlDialogueFlowRTL: true` | Does not mirror glyph identities or their source order; it places the first page glyph at the right and advances left for each following glyph. | The script was already manually reversed for the Backlog. This is the recommended mode for the current Arabic workflow. |
| `rtlDialogueMirrorGlyphs: false` and `rtlDialogueFlowRTL: false` | Keeps the original left-to-right glyph positions and only shifts the complete line toward the configured right edge. | Compatibility/testing, or when only right alignment is wanted. |

The new flow mode changes only the X placement; it does not reverse the glyph code points a second time. `rtlDialogueKeepNameLine` still skips the speaker-name Y-line when `name_start` was detected, while nameless dialogue pages remain fully eligible for RTL placement.

`rtlDialogueRightX` is an optional coordinate in the game's logical coordinate system before `coordsMultiplier` is applied. Start with `1200` for STEINS;GATE HD; increase it gradually to `1220` or `1240` if the line still starts too far left, or decrease it if the text crosses the right edge. Omitting the key or setting it to `0` uses the line's current right edge instead of a fixed edge. `rtlDialogueKeepNameLine` first requires the dialogue parser's `name_start` marker, then skips the greatest-Y line for that confirmed named page. When no name marker exists, no line is skipped and all dialogue lines remain eligible for RTL placement.

The mode is disabled by default and is applied only by the generic `DEF_DRAW_DIALOGUE_HOOK` path. For a script that is already prepared in the visual order required by the Backlog, use `rtlDialogueMirrorGlyphs: false` together with `rtlDialogueFlowRTL: true` to avoid a second visual reversal while still drawing from right to left. For a script kept in logical order, use `rtlDialogueMirrorGlyphs: true`; `rtlDialogueFlowRTL` is then irrelevant because the mirrored-position path is selected.
 It does not alter auxiliary mail, backlog, phone, or newer RNE/RND text paths. It also does not provide Arabic contextual shaping by itself; the configured font must already be suitable for the current glyph pipeline. If Arabic joining forms are not rendered correctly, a separate shaping stage using Uniscribe or HarfBuzz will be required before glyph IDs reach the renderer.

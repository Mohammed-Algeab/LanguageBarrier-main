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
    "rtlDialogueFlowRTL": true,
    "rtlDialogueReverseGlyphOrder": false
  }
}
```

When enabled, the main dialogue hook keeps the SC3 text stream and page data unchanged. `rtlDialogueFlowRTL` is the explicit direction switch: when it is `true`, the renderer preserves the game's original glyph spacing but maps the line from its right edge toward the left. In that mode it takes precedence over the legacy mirror/align choice, so changing `rtlDialogueMirrorGlyphs` alone must not change the direction. If the source glyph order is not the visual order required by the Arabic text, `rtlDialogueReverseGlyphOrder` swaps the glyph identity used for each dialogue slot at draw time only; it does not modify the SC3 string, script files, or Backlog.

The useful combinations are:

| Settings | Rendering behavior | Use when |
|---|---|---|
| `rtlDialogueFlowRTL: true` + `rtlDialogueReverseGlyphOrder: false` | Preserves glyph identities and original spacing, then maps every glyph box from the configured right edge toward the left. `rtlDialogueMirrorGlyphs` is ignored for placement in this mode. | The dialogue page already contains the desired visual glyph order. |
| `rtlDialogueFlowRTL: true` + `rtlDialogueReverseGlyphOrder: true` | Maps the line from right to left and draws the glyph from the opposite slot on the same dialogue line. The swap exists only inside the dialogue hook. | The script/page order is opposite to the desired Arabic visual order, while Backlog must remain untouched. |
| `rtlDialogueFlowRTL: false` + `rtlDialogueMirrorGlyphs: true` | Mirrors each glyph's original X position inside the line; the first page glyph is placed on the right and later glyphs extend left. | The legacy mode for a script kept in logical order. |
| `rtlDialogueFlowRTL: false` + `rtlDialogueMirrorGlyphs: false` | Keeps original glyph positions and only shifts the complete line toward the configured right edge. | Compatibility/testing, or when only right alignment is wanted. |

The new flow mode changes only X placement and preserves the original per-glyph gaps. `rtlDialogueReverseGlyphOrder` is separate: it exchanges the glyph source slot used by the dialogue draw call, without changing the text stored in the script and without affecting Backlog, mail, phone, menus, or other paths. `rtlDialogueKeepNameLine` still skips the speaker-name Y-line when `name_start` was detected, while nameless dialogue pages remain fully eligible for RTL placement. The DLL writes the parsed values to `languagebarrier\\log.txt` using a line beginning with `RTL dialogue config:`; use that line to verify that the running DLL is reading the intended patchdef.

`rtlDialogueRightX` is an optional coordinate in the game's logical coordinate system before `coordsMultiplier` is applied. Start with `1200` for STEINS;GATE HD; increase it gradually to `1220` or `1240` if the line still starts too far left, or decrease it if the text crosses the right edge. Omitting the key or setting it to `0` uses the line's current right edge instead of a fixed edge. `rtlDialogueKeepNameLine` first requires the dialogue parser's `name_start` marker, then skips the greatest-Y line for that confirmed named page. When no name marker exists, no line is skipped and all dialogue lines remain eligible for RTL placement.

The mode is disabled by default and is applied only by the generic `DEF_DRAW_DIALOGUE_HOOK` path. For a script whose dialogue page order already matches the desired visual glyph order, use `rtlDialogueFlowRTL: true` with `rtlDialogueReverseGlyphOrder: false`. If the rendered dialogue content is still reversed while the direction is correct, keep `rtlDialogueFlowRTL: true` and set `rtlDialogueReverseGlyphOrder: true`; this is the recommended experiment for separating a source-order problem from an X-position problem. Backlog remains outside this swap.
 It does not alter auxiliary mail, backlog, phone, or newer RNE/RND text paths. It also does not provide Arabic contextual shaping by itself; the configured font must already be suitable for the current glyph pipeline. If Arabic joining forms are not rendered correctly, a separate shaping stage using Uniscribe or HarfBuzz will be required before glyph IDs reach the renderer.

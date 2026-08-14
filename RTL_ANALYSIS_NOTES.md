# LanguageBarrier RTL analysis

## Confirmed architecture

The Visual Studio project builds a Win32 DynamicLibrary. The `dinput8-*` configurations produce `dinput8.dll`; the `cryptbase-*` configurations produce `cryptbase.dll`. The build links MinHook, DirectXTex, FreeType, Cereal, ImGui, and xy-VSFilter.

## Text pipeline

`getStringFromScriptHook` and `TextReplace.cpp` provide content replacement only. SC3 text is represented as two-byte glyph IDs; replacement preserves logical byte order and control commands.

For non-RNE/RND games, including the original Steam Steins;Gate path, `gameTextInit()` installs the main dialogue hooks and `TextRendering::LoadCharset()` plus `widths.bin` are used. The main dialogue hook is the `DEF_DRAW_DIALOGUE_HOOK` macro in `GameText.cpp`. It loops through `page->pageLength` in logical order and sends each glyph to `gameExeDrawGlyph`, using the precomputed `charDisplayX/Y` and `glyphDisplayWidth/Height`.

The current main dialogue renderer is explicitly left-to-right at the final display-coordinate stage: `displayStartX = (charDisplayX[i] + xOffset) * COORDS_MULTIPLIER`. The progressive reveal order is not implemented in `TextReplace.cpp`; it is inherited from the dialogue page's logical order, page length, and/or per-character opacity. Therefore the safe first RTL change is to mirror each glyph box horizontally within its original line bounds, without reversing the SC3 string or the page iteration order. This makes the first logical Arabic character/word occupy the rightmost position while subsequent characters extend toward the left, preserving the desired reveal order.

`DialogueWordwrap.cpp` only creates the engine's word-break mask. It should not reverse characters; for Arabic it may later need RTL-specific wrapping, but it is not the first insertion point for display direction.

## Planned patch

Add an opt-in `patch.rtlDialogue` flag. In `GameText.cpp`, add a generic line-bound helper that finds the contiguous same-Y run in a dialogue page, computes the line's left and right bounds from `charDisplayX` and `glyphDisplayWidth`, and maps each glyph box to `lineLeft + lineRight - (x + width)`. The main `DEF_DRAW_DIALOGUE_HOOK` uses this mapped X only when the flag is enabled. The page order and opacity remain unchanged, so the source text is not reversed and reveal remains logical-order while visual growth is right-to-left.

This patch does not yet implement Arabic contextual shaping. The existing renderer sends one glyph ID/code point at a time to FreeType or the game's glyph atlas. If the supplied Arabic font is unshaped, a second phase will need HarfBuzz/Uniscribe shaping and cluster-aware glyph mapping. The present patch isolates direction and reveal from shaping so it can be tested independently.

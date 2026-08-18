#ifndef __TEXTREPLACE_H__
#define __TEXTREPLACE_H__

namespace lb {
// Set by processTextReplacements for the script string most recently returned
// to the game. SGHD uses this metadata to keep the phone call bubble on its
// original LTR dialogue path without changing ordinary dialogue RTL.
extern bool g_dialogueForceLTR;

void globalTextReplacementsInit();
const char* processTextReplacements(const char* base, int fileId, int stringId);
}  // namespace lb

#endif

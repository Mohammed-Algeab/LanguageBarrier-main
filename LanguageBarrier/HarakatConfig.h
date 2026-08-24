#ifndef __HARAKAT_CONFIG_H__
#define __HARAKAT_CONFIG_H__

#include <cstdint>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace lb {

enum class HarakatKind : uint8_t {
  None = 0,
  Upper = 1,
  Kasra = 2,
  Shadda = 3,
};

struct HarakatDefinition {
  std::unordered_set<uint16_t> glyphIds;
  std::vector<std::pair<uint16_t, uint16_t>> glyphRanges;
  std::vector<wchar_t> unicodeCharacters;

  bool matchesGlyphId(uint16_t glyphId) const;
  bool matchesUnicode(wchar_t character) const;
};

struct HarakatConfig {
  bool fileLoaded = false;
  std::string loadedPath;
  HarakatDefinition upper;
  HarakatDefinition kasra;
  HarakatDefinition shadda;

  HarakatKind classify(uint16_t glyphId, wchar_t unicodeCharacter) const;
  bool hasDefinitions() const;
};

// The sidecar is deliberately independent from patchdef.json. It is optional;
// when absent or malformed, the feature remains inactive and the old renderer
// is left untouched.
extern HarakatConfig ARABIC_HARAKAT_CONFIG;

void initArabicHarakatConfig();

}  // namespace lb

#endif  // !__HARAKAT_CONFIG_H__

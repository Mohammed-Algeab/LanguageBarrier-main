#include "HarakatConfig.h"

#include <algorithm>
#include <codecvt>
#include <fstream>
#include <locale>
#include <sstream>
#include <stdexcept>
#include <string>

#include "LanguageBarrier.h"
#include "lbjson.h"

namespace lb {

HarakatConfig ARABIC_HARAKAT_CONFIG;

namespace {

bool readGlyphId(const json& value, uint16_t& result) {
  if (!value.is_number_integer()) return false;
  const int id = value.get<int>();
  if (id < 0 || id > 0x7FFF) return false;
  result = static_cast<uint16_t>(id);
  return true;
}

void readGlyphIds(const json& source, HarakatDefinition& definition) {
  const json* ids = nullptr;
  if (source.is_object() && source.contains("glyphIds")) {
    ids = &source["glyphIds"];
  }
  if (ids == nullptr || !ids->is_array()) return;

  for (const auto& value : *ids) {
    uint16_t glyphId = 0;
    if (readGlyphId(value, glyphId)) definition.glyphIds.insert(glyphId);
  }
}

void readGlyphRanges(const json& source, HarakatDefinition& definition) {
  const json* ranges = nullptr;
  if (source.is_object() && source.contains("glyphRanges")) {
    ranges = &source["glyphRanges"];
  }
  if (ranges == nullptr || !ranges->is_array()) return;

  for (const auto& value : *ranges) {
    uint16_t first = 0;
    uint16_t last = 0;
    bool valid = false;
    if (value.is_array() && value.size() >= 2) {
      valid = readGlyphId(value[0], first) && readGlyphId(value[1], last);
    } else if (value.is_object() && value.contains("from") &&
               value.contains("to")) {
      valid = readGlyphId(value["from"], first) &&
              readGlyphId(value["to"], last);
    }
    if (valid) {
      if (first > last) std::swap(first, last);
      definition.glyphRanges.emplace_back(first, last);
    }
  }
}

void readUnicode(const json& source, HarakatDefinition& definition) {
  const json* characters = nullptr;
  if (source.is_object() && source.contains("unicode")) {
    characters = &source["unicode"];
  } else if (source.is_object() && source.contains("characters")) {
    characters = &source["characters"];
  }
  if (characters == nullptr || !characters->is_array()) return;

  std::wstring_convert<std::codecvt_utf8_utf16<wchar_t>> converter;
  for (const auto& value : *characters) {
    try {
      if (value.is_string()) {
        const std::wstring decoded = converter.from_bytes(value.get<std::string>());
        definition.unicodeCharacters.insert(definition.unicodeCharacters.end(),
                                            decoded.begin(), decoded.end());
      } else if (value.is_number_integer()) {
        const int codepoint = value.get<int>();
        if (codepoint >= 0 && codepoint <= 0xFFFF)
          definition.unicodeCharacters.push_back(
              static_cast<wchar_t>(codepoint));
      }
    } catch (...) {
      // A bad optional Unicode label must not disable glyph-ID matching.
    }
  }
}

void readDefinition(const json& source, HarakatDefinition& definition) {
  if (!source.is_object()) return;
  readGlyphIds(source, definition);
  readGlyphRanges(source, definition);
  readUnicode(source, definition);
}

size_t definitionCount(const HarakatDefinition& definition) {
  return definition.glyphIds.size() + definition.glyphRanges.size() +
         definition.unicodeCharacters.size();
}

}  // namespace

bool HarakatDefinition::matchesGlyphId(uint16_t glyphId) const {
  if (glyphIds.find(glyphId) != glyphIds.end()) return true;
  for (const auto& range : glyphRanges) {
    if (glyphId >= range.first && glyphId <= range.second) return true;
  }
  return false;
}

bool HarakatDefinition::matchesUnicode(wchar_t character) const {
  return std::find(unicodeCharacters.begin(), unicodeCharacters.end(),
                   character) != unicodeCharacters.end();
}

HarakatKind HarakatConfig::classify(uint16_t glyphId,
                                    wchar_t unicodeCharacter) const {
  // Glyph IDs are authoritative: this is the value carried by SC3 and used by
  // the bitmap width table. Unicode is only a deliberate fallback for the
  // replacement-font path, where fullCharMap supplies that bridge.
  if (shadda.matchesGlyphId(glyphId) ||
      shadda.matchesUnicode(unicodeCharacter))
    return HarakatKind::Shadda;
  if (kasra.matchesGlyphId(glyphId) ||
      kasra.matchesUnicode(unicodeCharacter))
    return HarakatKind::Kasra;
  if (upper.matchesGlyphId(glyphId) ||
      upper.matchesUnicode(unicodeCharacter))
    return HarakatKind::Upper;
  return HarakatKind::None;
}

bool HarakatConfig::hasDefinitions() const {
  return definitionCount(upper) != 0 || definitionCount(kasra) != 0 ||
         definitionCount(shadda) != 0;
}

void initArabicHarakatConfig() {
  ARABIC_HARAKAT_CONFIG = HarakatConfig{};
  const char* path = "languagebarrier\\harakat.json";
  std::ifstream input(path);
  if (!input.is_open()) {
    LanguageBarrierLog(
        "Arabic harakat sidecar not found; harakat support remains inactive");
    return;
  }

  try {
    json root;
    input >> root;
    if (!root.is_object()) throw std::runtime_error("root is not an object");
    const json& marks = root.contains("marks") ? root["marks"] : root;
    if (!marks.is_object()) throw std::runtime_error("marks is not an object");

    if (marks.contains("upper")) readDefinition(marks["upper"],
                                                  ARABIC_HARAKAT_CONFIG.upper);
    if (marks.contains("kasra")) readDefinition(marks["kasra"],
                                                  ARABIC_HARAKAT_CONFIG.kasra);
    if (marks.contains("shadda"))
      readDefinition(marks["shadda"], ARABIC_HARAKAT_CONFIG.shadda);

    // Allow explicit names for common marks without requiring users to put
    // every ID into one large category object. Kasra-tanwin remains lower.
    const char* upperNames[] = {"fatha", "damma", "sukun", "fathatan",
                                "dammatan"};
    for (const char* name : upperNames) {
      if (marks.contains(name)) readDefinition(marks[name],
                                                ARABIC_HARAKAT_CONFIG.upper);
    }
    const char* lowerNames[] = {"kasratan", "lower"};
    for (const char* name : lowerNames) {
      if (marks.contains(name)) readDefinition(marks[name],
                                                ARABIC_HARAKAT_CONFIG.kasra);
    }

    ARABIC_HARAKAT_CONFIG.fileLoaded = true;
    ARABIC_HARAKAT_CONFIG.loadedPath = path;

    std::stringstream log;
    log << "Arabic harakat sidecar loaded: upper="
        << definitionCount(ARABIC_HARAKAT_CONFIG.upper)
        << ", kasra=" << definitionCount(ARABIC_HARAKAT_CONFIG.kasra)
        << ", shadda=" << definitionCount(ARABIC_HARAKAT_CONFIG.shadda);
    LanguageBarrierLog(log.str());
  } catch (const std::exception& error) {
    ARABIC_HARAKAT_CONFIG = HarakatConfig{};
    LanguageBarrierLog(std::string("Arabic harakat sidecar ignored: ") +
                       error.what());
  }
}

}  // namespace lb

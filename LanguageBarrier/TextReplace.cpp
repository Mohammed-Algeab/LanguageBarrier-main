#include <string>
#include <set>
#include <vector>
#include "Config.h"
#include "TextReplace.h"

// global text replacement code and data
namespace {
enum class text_command_type {
  unknown = 0,
  single,
  extra_byte,
  extra_word,
  expr,
};
struct TextReplacement_t {
  std::string From;
  std::string To;
  std::set<std::pair<int, int>> Excludes;
} ;
struct ProcessedString_t {
  std::string replaced;
  bool useOriginal = false;
  bool forceLTR = false;
};

class LazyAllocatingProcessedString {
  ProcessedString_t& result;
  const char* processedBegin;
  const char* processedEnd;

 public:
  LazyAllocatingProcessedString(ProcessedString_t& result_, const char* base)
      : result(result_), processedBegin(base), processedEnd(base) {}
  void appendFragment(const char* fragmentBegin, const char* fragmentEnd) {
    if (processedEnd == fragmentBegin) {
      processedEnd = fragmentEnd;
    } else {
      if (result.useOriginal) {
        result.replaced.assign(processedBegin, processedEnd);
        result.useOriginal = false;
        processedBegin = nullptr;
        processedEnd = nullptr;
      }
      result.replaced.append(fragmentBegin, fragmentEnd);
    }
  }
};
}  // namespace
static text_command_type parseTextRules[128];

static bool parseTextReplacement(const json& val, std::string& result) {
  if (!val.is_array()) return false;
  result.reserve(val.size() * 2);
  for (size_t i = 0; i < val.size(); i++) {
    if (!val[i].is_number_integer()) return false;
    int codepoint = val[i].get<int>();
    result.push_back((char)(0x80 + (codepoint >> 8)));
    result.push_back((char)(codepoint & 0xFF));
  }
  return true;
}

static std::vector<TextReplacement_t> globalTextReplacements;

static constexpr unsigned char kPhoneLtrMarkerHigh = 0x8B;
static constexpr unsigned char kPhoneLtrMarkerLow = 0x2D;

static bool containsPhoneLtrMarker(const char* base) {
  if (base == nullptr) return false;
  for (const unsigned char* ptr =
           reinterpret_cast<const unsigned char*>(base);
       *ptr != 0xFF; ++ptr) {
    if (ptr[0] == kPhoneLtrMarkerHigh && ptr[1] == kPhoneLtrMarkerLow)
      return true;
  }
  return false;
}

static bool stripPhoneLtrMarkers(const char* begin, const char* end,
                                 std::string& stripped) {
  const unsigned char* ptr =
      reinterpret_cast<const unsigned char*>(begin);
  const unsigned char* finish =
      reinterpret_cast<const unsigned char*>(end);
  const unsigned char* marker = nullptr;
  for (; ptr + 1 < finish; ptr += 2) {
    if (ptr[0] == kPhoneLtrMarkerHigh && ptr[1] == kPhoneLtrMarkerLow) {
      marker = ptr;
      break;
    }
  }
  if (marker == nullptr) return false;

  stripped.reserve(static_cast<size_t>(end - begin));
  const char* copy = begin;
  ptr = reinterpret_cast<const unsigned char*>(begin);
  while (ptr + 1 < finish) {
    if (ptr[0] == kPhoneLtrMarkerHigh && ptr[1] == kPhoneLtrMarkerLow) {
      stripped.append(copy, reinterpret_cast<const char*>(ptr) - copy);
      ptr += 2;
      copy = reinterpret_cast<const char*>(ptr);
    } else {
      ptr += 2;
    }
  }
  stripped.append(copy, end - copy);
  return true;
}

namespace lb {

bool g_dialogueForceLTR = false;

void globalTextReplacementsInit() {
  auto parseRulesIter = config["gamedef"].find("textParseRules");
  if (parseRulesIter != config["gamedef"].end()) {
    static const std::pair<const char*, text_command_type> config_keys[] = {
        {"single", text_command_type::single},
        {"extraByte", text_command_type::extra_byte},
        {"extraWord", text_command_type::extra_word},
        {"expr", text_command_type::expr},
    };
    for (auto descr : config_keys) {
      auto singleByteIter = parseRulesIter->find(descr.first);
      if (singleByteIter != parseRulesIter->end() &&
          singleByteIter->is_array()) {
        for (size_t i = 0; i < singleByteIter->size(); i++) {
          if (!singleByteIter->at(i).is_number_integer()) continue;
          int cmd = singleByteIter->at(i).get<int>();
          if (cmd >= 0 && cmd < 0x80) parseTextRules[cmd] = descr.second;
        }
      }
    }
  }
  const json& patch = config["patch"];
  json::const_iterator replacementsArray = patch.find("globalTextReplacements");
  if (replacementsArray == patch.end()) return;
  if (!replacementsArray->is_array()) return;
  for (size_t i = 0; i < replacementsArray->size(); i++) {
    const json& replacement = replacementsArray->at(i);
    auto fromIterator = replacement.find("from");
    auto toIterator = replacement.find("to");
    if (fromIterator == replacement.cend() || toIterator == replacement.cend())
      continue;
    TextReplacement_t current;
    if (parseTextReplacement(*fromIterator, current.From) &&
        parseTextReplacement(*toIterator, current.To)) {
      auto excludeIterator = replacement.find("exclude");
      if (excludeIterator != replacement.end() && excludeIterator->is_array()) {
        for (size_t j = 0; j < excludeIterator->size(); j++) {
          const json& exclude = excludeIterator->at(j);
          if (exclude.is_array() && exclude.size() >= 2 &&
              exclude.at(0).is_number_integer() &&
              exclude.at(1).is_number_integer()) {
            current.Excludes.emplace(exclude.at(0).get<int>(),
                                     exclude.at(1).get<int>());
          }
        }
      }
      globalTextReplacements.emplace_back(std::move(current));
    }
  }
}

static void replaceTextFragment(const char* fragBegin, const char* fragEnd,
                                int fileId, int stringId,
                                LazyAllocatingProcessedString& result) {
  std::string transformed;
  for (const auto& it : globalTextReplacements) {
    if (it.Excludes.find(std::make_pair(fileId, stringId)) !=
        it.Excludes.end()) {
      continue;
    }
    for (const char* ptr = fragBegin; (size_t)(fragEnd - ptr) >= it.From.size();
         ptr += 2) {
      if (!memcmp(ptr, it.From.data(), it.From.size())) {
        size_t pos = ptr - fragBegin;
        if (transformed.empty()) transformed.assign(fragBegin, fragEnd);
        transformed.replace(pos, it.From.size(), it.To);
        fragBegin = transformed.data();  // pointers could have been invalidated
        ptr = fragBegin + pos;
        fragEnd = fragBegin + transformed.size();
      }
    }
  }
  std::string markerStripped;
  if (stripPhoneLtrMarkers(fragBegin, fragEnd, markerStripped)) {
    g_dialogueForceLTR = true;
    result.forceLTR = true;
    fragBegin = markerStripped.data();
    fragEnd = fragBegin + markerStripped.size();
  }
  result.appendFragment(fragBegin, fragEnd);
}

const char* processTextReplacements(const char* base, int fileId,
                                    int stringId) {
  g_dialogueForceLTR = false;
  const bool baseHasPhoneLtrMarker = containsPhoneLtrMarker(base);
  if (globalTextReplacements.empty() && !baseHasPhoneLtrMarker) return base;
  static std::vector<std::vector<ProcessedString_t>> processedTextReplacements;
  if (fileId >= (int)processedTextReplacements.size())
    processedTextReplacements.resize(fileId + 1);
  if (stringId >= (int)processedTextReplacements[fileId].size())
    processedTextReplacements[fileId].resize(stringId + 1);
  ProcessedString_t& result = processedTextReplacements[fileId][stringId];
  if (!result.replaced.empty()) {
    g_dialogueForceLTR = result.forceLTR;
    return result.replaced.data();
  }
  if (result.useOriginal) {
    g_dialogueForceLTR = result.forceLTR;
    return base;
  }
  result.useOriginal = true;
  result.forceLTR = baseHasPhoneLtrMarker;
  LazyAllocatingProcessedString processor(result, base);
  const char* ptr = base;
  const char* textFragmentBegin = nullptr;
  bool bad = false;
  while (!bad && *ptr != (char)0xFF) {
    if ((signed char)*ptr < 0) {
      // text
      if (!textFragmentBegin) textFragmentBegin = ptr;
      ptr += 2;
    } else {
      // command
      if (textFragmentBegin) {
        replaceTextFragment(textFragmentBegin, ptr, fileId, stringId,
                            processor);
      }
      textFragmentBegin = nullptr;
      const char* cmdstart = ptr;
      switch (parseTextRules[*ptr]) {
        case text_command_type::unknown:
          LanguageBarrierLog(
              "unknown text command " + std::to_string((int)*ptr) +
              " while processing script #" + std::to_string(fileId) +
              ", string #" + std::to_string(stringId));
          bad = true;
          break;
        case text_command_type::single:
          ++ptr;
          break;
        case text_command_type::extra_byte:
          ptr += 2;
          break;
        case text_command_type::extra_word:
          ptr += 3;
          break;
        case text_command_type::expr:
          ++ptr;
          static const char sizes[4] = {2, 3, 4, 6};
          while (*ptr) {
            if (*ptr & 0x80)
              ptr += sizes[((unsigned char)*ptr >> 5) & 3];
            else
              ptr += 2;
          }
          ++ptr;
          break;
      }
      processor.appendFragment(cmdstart, ptr);
    }
  }
  if (textFragmentBegin) {
    replaceTextFragment(textFragmentBegin, ptr, fileId, stringId, processor);
  }
  if (bad) {
    result.replaced.clear();
    result.useOriginal = true;
  }
  if (result.useOriginal) {
    g_dialogueForceLTR = result.forceLTR;
    return base;
  }
  result.replaced.push_back((char)0xFF);
  g_dialogueForceLTR = result.forceLTR;
  return result.replaced.data();
}

}  // namespace lb

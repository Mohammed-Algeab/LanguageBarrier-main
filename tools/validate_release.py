from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LB = ROOT / "LanguageBarrier"
errors: list[str] = []
checks: list[str] = []


def require(condition: bool, message: str) -> None:
    if condition:
        checks.append(message)
    else:
        errors.append(message)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)} JSON parse failed: {exc}")
        return None


harakat = load_json(LB / "harakat.json")
if isinstance(harakat, dict):
    marks = harakat.get("marks", {})
    expected = {"fatha", "damma", "kasra", "sukun", "fathatan", "dammatan", "kasratan", "shadda"}
    require(harakat.get("version") == 1, "harakat.json declares version 1")
    require(expected <= set(marks), "harakat.json has all eight mark categories")
    for name in expected:
        value = marks.get(name)
        require(isinstance(value, dict), f"harakat mark {name} is an object")
        if isinstance(value, dict):
            for field in ("glyphIds", "glyphRanges", "unicode"):
                require(isinstance(value.get(field), list), f"harakat mark {name}.{field} is an array")

example = load_json(LB / "harakat-sghd-example.json")
if isinstance(example, dict):
    ids = []
    for value in example.get("marks", {}).values():
        ids.extend(value.get("glyphIds", []))
    require(sorted(ids) == list(range(811, 819)), "SGHD example contains tested IDs 811..818 exactly once")
    require(not re.search(r"\b0[0-9]+\b", (LB / "harakat-sghd-example.json").read_text()), "SGHD example has no zero-leading glyph IDs")

vcpkg_config = load_json(ROOT / "vcpkg-configuration.json")
if isinstance(vcpkg_config, dict):
    overlays = vcpkg_config.get("overlay-triplets")
    require(isinstance(overlays, list) and "./triplets" in overlays, "vcpkg configuration declares ./triplets as an overlay")

snippet = load_json(ROOT / "HARAKAT_PATCHDEF_SNIPPET.json")
if isinstance(snippet, dict):
    patch = snippet.get("patch", {})
    required = {
        "arabicHarakatEnabled", "arabicHarakatStripBacklog",
        "arabicHarakatUpperX", "arabicHarakatUpperY",
        "arabicHarakatKasraX", "arabicHarakatKasraY",
        "arabicHarakatShaddaX", "arabicHarakatShaddaY",
        "arabicHarakatShaddaUpperX", "arabicHarakatShaddaUpperY",
        "arabicHarakatShaddaKasraX", "arabicHarakatShaddaKasraY",
        "arabicHarakatStripSghdCallsites",
    }
    require(required <= set(patch), "patchdef snippet has opt-in, X/Y, and SGHD callsite keys")
    targets = patch.get("arabicHarakatStripSghdCallsites")
    require(isinstance(targets, list), "SGHD callsite targets are an array")
    if isinstance(targets, list):
        require(all(re.fullmatch(r"clearlistDrawRet(?:[1-9]|1[0-3])", str(x)) for x in targets), "SGHD callsites use known clearlistDrawRet1..13 names")
        require(len(set(targets)) == len(targets), "SGHD callsites contain no duplicate names")

project = LB / "LanguageBarrier.vcxproj"
try:
    ET.parse(project)
    project_text = project.read_text(encoding="utf-8-sig")
    require("HarakatConfig.cpp" in project_text and "HarakatConfig.h" in project_text, "HarakatConfig files are in vcxproj")
    require("harakat-sghd-example.json" in project_text, "SGHD example is visible in vcxproj")
    require(project_text.count("harakat.json") >= 6, "runtime harakat.json is copied in all project configurations")
    for config in ("dinput8-Release", "cryptbase-Release"):
        start = project_text.find(f"Condition=\"'$(Configuration)|$(Platform)'=='{config}|Win32'\" Label=\"Configuration\"")
        require(start >= 0, f"{config} property group exists")
        if start >= 0:
            block = project_text[start:project_text.find("</PropertyGroup>", start) + len("</PropertyGroup>")]
            require("<PlatformToolset>v142</PlatformToolset>" in block, f"{config} uses v142")
    release_definition_start = project_text.find("<ItemDefinitionGroup Condition=\"'$(Configuration)|$(Platform)'=='dinput8-Release|Win32'\">")
    release_definition_end = project_text.find("</ItemDefinitionGroup>", release_definition_start)
    release_definitions = project_text[release_definition_start:release_definition_end]
    cryptbase_definition_start = project_text.find("<ItemDefinitionGroup Condition=\"'$(Configuration)|$(Platform)'=='cryptbase-Release|Win32'\">")
    cryptbase_definition_end = project_text.find("</ItemDefinitionGroup>", cryptbase_definition_start)
    cryptbase_definitions = project_text[cryptbase_definition_start:cryptbase_definition_end]
    require("<SubSystem>Windows,6.01</SubSystem>" not in project_text, "project has no invalid comma-form SubSystem value")
    for config, block in (("dinput8-Release", release_definitions), ("cryptbase-Release", cryptbase_definitions)):
        require("<SubSystem>Windows</SubSystem>" in block, f"{config} uses valid Windows SubSystem value")
        require("<MinimumRequiredVersion>6.01</MinimumRequiredVersion>" in block, f"{config} targets minimum OS version 6.01 separately")
        require("libcmt.lib" not in block, f"{config} does not manually duplicate the static CRT library")
    vcpkg_release = project_text[project_text.find('<PropertyGroup Label="Vcpkg" Condition="\'$(Configuration)|$(Platform)\'==\'dinput8-Release|Win32\'">'):]
    require("<VcpkgUseStatic>false</VcpkgUseStatic>" in vcpkg_release, "Release vcpkg integration does not append a duplicate -static suffix")
    require("<VcpkgUseMD>false</VcpkgUseMD>" in vcpkg_release, "Release vcpkg integration requests non-MD runtime")
    require(vcpkg_release.count("<VcpkgAdditionalInstallOptions>") >= 2, "both Release projects pass overlay triplets through MSBuild additional options")
    require("--overlay-triplets=\"$(VcpkgManifestRoot)\\triplets\"" in vcpkg_release, "MSBuild uses the supported VcpkgAdditionalInstallOptions overlay flag")
    require("<VcpkgOverlayTriplets>" not in project_text, "project does not rely on the unsupported VcpkgOverlayTriplets property")
except Exception as exc:
    errors.append(f"vcxproj validation failed: {exc}")

workflow = ROOT / ".github" / "workflows" / "build.yml"
try:
    workflow_text = workflow.read_text(encoding="utf-8-sig")
    try:
        import yaml  # type: ignore
        yaml.safe_load(workflow_text)
        require(True, "build.yml parses as YAML")
    except ImportError:
        require(True, "build.yml YAML parse skipped because PyYAML is unavailable")
    require("runs-on: windows-2022" in workflow_text, "workflow uses windows-2022")
    require("/p:Configuration=\"${{ matrix.configuration }}\"" in workflow_text, "workflow builds selected Release configuration")
    require("/p:Platform=x86" in workflow_text, "workflow builds x86 solution platform")
    require("dinput8-Release|x86" in (ROOT / "LanguageBarrier.sln").read_text(encoding="utf-8-sig"), "solution exposes dinput8 Release as x86")
    require("dinput8-Release|Win32" in (ROOT / "LanguageBarrier.sln").read_text(encoding="utf-8-sig"), "solution maps x86 to the project Win32 configuration")
    require("x86-windows-static-v142" in workflow_text, "workflow uses the x86/static/v142 vcpkg triplet")
    require("VCPKG_PLATFORM_TOOLSET=v142" in workflow_text, "workflow exports v142 for vcpkg dependency builds")
    require("VCPKG_VISUAL_STUDIO_PATH" in workflow_text, "workflow pins vcpkg to the selected Visual Studio instance")
    require("VCPKG_OVERLAY_TRIPLETS" in workflow_text, "workflow exports the overlay triplet directory to every vcpkg invocation")
    require("/p:PlatformToolset=v142" in workflow_text, "workflow explicitly requests v142")
    require("/p:VcpkgUseStatic=false" in workflow_text, "workflow disables MSBuild static suffix appending")
    require("/p:VcpkgAdditionalInstallOptions=\"--overlay-triplets=%VCPKG_OVERLAY_TRIPLETS%\"" in workflow_text, "MSBuild receives the overlay-triplets option explicitly")
    require("/p:VcpkgOverlayTriplets" not in workflow_text, "workflow does not rely on the unsupported VcpkgOverlayTriplets property")
    triplet = ROOT / "triplets" / "x86-windows-static-v142.cmake"
    require(triplet.exists(), "custom vcpkg v142 triplet exists")
    if triplet.exists():
        triplet_text = triplet.read_text(encoding="utf-8-sig")
        require("VCPKG_TARGET_ARCHITECTURE x86" in triplet_text, "custom triplet targets x86")
        require("VCPKG_CRT_LINKAGE static" in triplet_text, "custom triplet uses static CRT")
        require("VCPKG_PLATFORM_TOOLSET v142" in triplet_text, "custom triplet selects v142")
    require("DLL_DEPENDENCIES.txt" in workflow_text and "DLL_IMPORTS.txt" in workflow_text and "PE_HEADERS.txt" in workflow_text, "workflow records dependencies, imports, and PE headers")
    require("CreateFile2" in workflow_text and "Windows 7 import check failed" in workflow_text, "workflow rejects CreateFile2 imports for Windows 7")
    require("LanguageBarrier\\contrib\\lib\\Release" not in workflow_text, "workflow has no stale contrib/lib/Release requirement")
except Exception as exc:
    errors.append(f"workflow validation failed: {exc}")

game_cpp = (LB / "Game.cpp").read_text(encoding="utf-8-sig")
require("fileExistsWin7" in game_cpp and "GetFileAttributesA" in game_cpp, "Game.cpp uses a Win7-safe file existence helper")
require("std::filesystem::exists" not in game_cpp, "Game.cpp does not call std::filesystem::exists")

cpp = (LB / "GameText.cpp").read_text(encoding="utf-8-sig")
require("drawGlyphVersion" in cpp and "STEINS;GATE" in cpp, "SGHD detection uses explicit gamedef fields")
require("arabicHarakatStripSghdCallsites" in cpp, "SGHD stripping requires explicit callsite list")
require("static_cast<uint8_t>(input[index + 1]) == 0xFF" in cpp, "temporary SC3 copy preserves optional second terminator")
require("first == 0x04" in cpp and "output.clear()" in cpp, "unknown variable-length control aborts safely")
require("ARABIC_HARAKAT_STRIP_BACKLOG" in cpp, "backlog strip remains opt-in")
require("[phone-ltr]" in cpp or "phone-ltr" in cpp, "phone-ltr path remains present")

# Remove comments and string literals for a conservative delimiter-balance check.
code = re.sub(r"//[^\n]*|/\*[\s\S]*?\*/", "", cpp)
code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
for opening, closing, label in (("{", "}", "brace"), ("(", ")", "parenthesis"), ("[", "]", "bracket")):
    require(code.count(opening) == code.count(closing), f"C++ {label} delimiters are balanced")

if errors:
    print("FAIL")
    for error in errors:
        print("ERROR:", error)
    print(f"Checks passed: {len(checks)}")
    sys.exit(1)

print("PASS")
for check in checks:
    print("OK:", check)
print(f"Checks passed: {len(checks)}")

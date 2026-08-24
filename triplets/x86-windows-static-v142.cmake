# LanguageBarrier Release triplet.
# Keep vcpkg-built dependencies on the same x86/v142/static-CRT
# toolchain as the Visual Studio project.
set(VCPKG_TARGET_ARCHITECTURE x86)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_PLATFORM_TOOLSET v142)

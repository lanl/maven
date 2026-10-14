; Per-user NSIS installer for MAVEN.
; Built with: makensis /DVERSION=1.2.3 /DEXE_PATH=dist\maven-windows.exe packaging\windows\installer.nsi
; No admin/UAC required -- installs under %LOCALAPPDATA%\Programs\maven so the
; self-updater (maven/desktop/updater.py) can keep overwriting the exe in place.

!ifndef VERSION
  !define VERSION "0.0.0-dev"
!endif
!ifndef EXE_PATH
  !define EXE_PATH "dist\maven-windows.exe"
!endif
!ifndef OUT_DIR
  !define OUT_DIR "release"
!endif

Name "MAVEN"
OutFile "${OUT_DIR}\maven-windows-installer.exe"
InstallDir "$LOCALAPPDATA\Programs\maven"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!include "MUI2.nsh"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

VIProductVersion "0.0.0.0"
VIAddVersionKey "ProductName" "MAVEN"
VIAddVersionKey "ProductVersion" "${VERSION}"

Section "Install"
  SetOutPath "$INSTDIR"
  File "/oname=maven.exe" "${EXE_PATH}"

  CreateDirectory "$SMPROGRAMS\MAVEN"
  CreateShortcut "$SMPROGRAMS\MAVEN\MAVEN.lnk" "$INSTDIR\maven.exe"
  CreateShortcut "$DESKTOP\MAVEN.lnk" "$INSTDIR\maven.exe"

  WriteUninstaller "$INSTDIR\uninstall.exe"

  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "DisplayName" "MAVEN"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven" \
    "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\maven.exe"
  Delete "$INSTDIR\uninstall.exe"
  Delete "$SMPROGRAMS\MAVEN\MAVEN.lnk"
  RMDir "$SMPROGRAMS\MAVEN"
  Delete "$DESKTOP\MAVEN.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\maven"
SectionEnd

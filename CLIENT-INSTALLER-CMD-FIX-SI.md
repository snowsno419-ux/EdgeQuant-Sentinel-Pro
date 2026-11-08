# Client Installer CMD එක close වෙන ගැටලුව - diagnostic fix (2026-11-06)

## Run කරන විදිහ

1. සම්පූර්ණ ZIP එක **Extract All** කරලා `C:\EdgeQuantBuild` වගේ local folder එකකට දාන්න. ZIP එක ඇතුළේ BAT එක run කරන්න එපා.
2. `RUN-CLIENT-INSTALLER-KEEP-OPEN.bat` double-click කරන්න. මෙය නව CMD window එකක් විවෘත කරලා build අවසානයේත් විවෘතව තබනවා.
3. නැත්නම් `BUILD-CLIENT-INSTALLER.bat` directly run කරන්න. ඒක අවසානයේ `pause` කරනවා.
4. Error එකක් ආවොත් project folder එකේ `CLIENT-INSTALLER-BUILD.log` තුළ සම්පූර්ණ details තියෙනවා. ඒ file එකේ අන්තිම error lines බලන්න.
5. **Build successful** බව පෙන්වා `dist\EdgeQuant-Sentinel-Client-Setup.exe` ගොනුව පවතිනවා නම් විතරක් installer එක test කරන්න.

## Known build blockers

- Owner/developer Windows PC එකක 64-bit Python (Tkinter සමඟ), internet, Windows Inno Setup 6 සහ MetaTrader5 package එක අවශ්‍යයි.
- Pre-build automated tests fail වුණොත් **Setup.exe නොහදන විදිහට** gate එක තවම තියෙනවා. කලින් version එකේ some legacy engine self-tests අලුත් trading rules සමඟ නොගැළපෙන බව වාර්තා වෙලා තිබුණා; මේ patch එකෙන් ඒවා pass වෙනවා කියලා claim කරන්නේ නැහැ.
- CMD වසා යන එක වැළැක්වීම සහ log file එකක් සුරැකීම **installer compilation සාර්ථකයි** කියන තේරුමක් නෙවෙයි.
- Source, credentials, broker details, session files හෝ log එකේ sensitive දත්ත clients හට නොදෙන්න.
- Installation test කරන්න Windows 10/11 x64 clean PC එකක් සහ DEMO account එකක් භාවිත කරන්න. මෙහි Windows build run කරලා verify කරලා නැහැ.

## If CMD still disappears

Command Prompt එක manually විවෘත කරලා:

```bat
cd /d "C:\EdgeQuantBuild\EdgeQuant-Sentinel-Universal-Engine-PRIVATE-GROUP-DASHBOARD-DEV"
cmd /k "BUILD-CLIENT-INSTALLER.bat"
```

Actual folder path එකට අනුව `cd` path එක වෙනස් කරන්න. එතකොට printed error එක සහ log එක inspect කරන්න.

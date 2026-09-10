---
name: windows-compiler
description: Kompletny przewodnik po kompilacji programów Linux/Unix na Windows z wykorzystaniem GitHub Actions. Obejmuje Python (PyInstaller/cx_Freeze), C/C++ (MSVC/MinGW), Rust (cargo), Go (GOOS=windows), Node.js (pkg/nexe), Java (jpackage). Obsługuje cross-compile z Linux, native build w GitHub Actions, code signing, dystrybucję (NSIS/Inno Setup/MSI). Używaj gdy użytkownik chce skompilować program na Windows, stworzyć .exe, zbudować dystrybucję Windows, skonfigurować CI/CD dla Windows, użyć GitHub Actions do buildu Windows, lub pyta o cross-compile Linux→Windows. Triggers: "kompiluj na Windows", "buduj .exe", "cross-compile Windows", "GitHub Actions Windows", "PyInstaller", "MSVC", "MinGW", "/windows-compiler".
---

# Windows Compiler — Kompletny Przewodnik

Kompilacja programów Linux/Unix na Windows z wykorzystaniem GitHub Actions i narzędzi CI/CD.

## Kiedy używać

- Użytkownik chce skompilować program na Windows (utworzyć .exe)
- Użytkownik pyta o cross-compile z Linux na Windows
- Użytkownik chce skonfigurować GitHub Actions dla buildu Windows
- Użytkownik potrzebuje dystrybucji Windows (installer, portable, single-file)
- Użytkownik pyta o code signing dla Windows
- Użytkownik porównuje opcje buildu (MSVC vs MinGW vs cross-compile)

## Decyzja: Native vs Cross-Compile

```
Czy możesz użyć GitHub Actions windows-latest?
├─ TAK → Native build (zalecane)
│        - Pełna kompatybilność
│        - Łatwe debugowanie
│        - Dostęp do MSVC
│
└─ NIE → Cross-compile z Linux
         - Tylko dla C/C++ (MinGW-w64)
         - Ograniczona kompatybilność
         - Trudne debugowanie
```

**Zasada:** Zawsze preferuj native build w GitHub Actions. Cross-compile tylko gdy nie masz dostępu do Windows runner.

---

## 1. Python — Kompilacja na Windows

### 1.1 PyInstaller (zalecane)

**Narzędzie:** Pakuje Python + zależności do single .exe

**Setup lokalny:**
```bash
pip install pyinstaller
```

**Podstawowa komenda:**
```bash
pyinstaller --onefile --windowed \
  --name "MyApp" \
  --icon=icon.ico \
  --add-data "data:data" \
  app.py
```

**Kluczowe opcje:**
| Opcja | Opis |
|-------|------|
| `--onefile` | Single .exe (wolny start, duży rozmiar) |
| `--onedir` | Katalog z plikami (szybszy start) |
| `--windowed` | Bez okna konsoli (GUI apps) |
| `--icon=FILE` | Ikona .ico |
| `--add-data SRC;DST` | Dołącz pliki danych |
| `--hidden-import MODULE` | Wymuś import modułu |
| `--exclude-module MODULE` | Wyklucz moduł (zmniejsza rozmiar) |
| `--upx-dir DIR` | Kompresja UPX |

**Spec file (zaawansowane):**
```python
# myapp.spec
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('data/', 'data/')],
    hiddenimports=['PySide6.QtCore', 'openai'],
    excludes=['tkinter', 'matplotlib'],
)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name='MyApp',
    icon='icon.ico',
    console=False,
)
```

### 1.2 cx_Freeze (alternatywa)

```bash
pip install cx_Freeze
```

```python
# setup.py
from cx_Freeze import setup, Executable

setup(
    name="MyApp",
    version="1.0",
    executables=[Executable("app.py", base="Win32GUI")],
    options={"build_exe": {"packages": ["PySide6"]}},
)
```

```bash
python setup.py build
```

### 1.3 GitHub Actions — Python

```yaml
name: Build Windows (Python)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -e .
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller --onefile --windowed app.py
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows
          path: dist/
      
      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*.exe
```

---

## 2. C/C++ — Kompilacja na Windows

### 2.1 MSVC (Microsoft Visual C++) — zalecane

**Wymagania:**
- Visual Studio 2022 Build Tools
- Windows SDK
- CMake 3.21+

**Lokalnie:**
```powershell
# Konfiguracja
cmake -B build -G "Visual Studio 17 2022" -A x64

# Kompilacja
cmake --build build --config Release
```

**Zalety:**
- Pełna kompatybilność z Windows API
- Najlepsza wydajność
- Wsparcie dla Qt, MFC, Win32

**Wady:**
- Wymaga Windows (nie cross-compile)
- Duży rozmiar (~8GB Build Tools)

### 2.2 MinGW-w64 (cross-compile z Linux)

**Instalacja:**
```bash
sudo apt install mingw-w64 cmake

# Lub cross-compile toolchain
sudo apt install gcc-mingw-w64 g++-mingw-w64
```

**Toolchain file:**
```cmake
# mingw-w64-toolchain.cmake
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)
```

**Kompilacja:**
```bash
cmake -B build-mingw \
  -DCMAKE_TOOLCHAIN_FILE=mingw-w64-toolchain.cmake

cmake --build build-mingw
```

**Ograniczenia:**
- Brak wsparcia dla MSVC-specific features
- Problemy z Qt6 (niekompletne porty)
- Trudne debugowanie

### 2.3 GitHub Actions — C/C++

```yaml
name: Build Windows (C++)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure CMake
        run: cmake -B build -G "Visual Studio 17 2022" -A x64
      
      - name: Build
        run: cmake --build build --config Release
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows-CPP
          path: build/Release/
```

**Z Qt:**
```yaml
- name: Install Qt
  uses: jurplel/install-qt-action@v4
  with:
    version: '6.7.0'
    host: 'windows'
    target: 'desktop'
    arch: 'win64_msvc2022_64'

- name: Deploy Qt DLLs
  run: windeployqt build/Release/MyApp.exe
```

---

## 3. Rust — Kompilacja na Windows

### 3.1 Native build (cross-compile z Linux)

**Instalacja targetu:**
```bash
rustup target add x86_64-pc-windows-gnu
```

**Kompilacja:**
```bash
cargo build --release --target x86_64-pc-windows-gnu
```

**Wynik:** `target/x86_64-pc-windows-gnu/release/myapp.exe`

### 3.2 MSVC target (wymaga Windows)

```bash
rustup target add x86_64-pc-windows-msvc
cargo build --release --target x86_64-pc-windows-msvc
```

### 3.3 GitHub Actions — Rust

```yaml
name: Build Windows (Rust)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      
      - name: Build
        run: cargo build --release
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows-Rust
          path: target/release/myapp.exe
```

**Cross-compile z Linux:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: x86_64-pc-windows-gnu
      
      - name: Install MinGW
        run: sudo apt install -y gcc-mingw-w64
      
      - name: Build
        run: cargo build --release --target x86_64-pc-windows-gnu
```

---

## 4. Go — Kompilacja na Windows

### 4.1 Cross-compile (najłatwiejsze)

```bash
GOOS=windows GOARCH=amd64 go build -o myapp.exe
```

**Zalety:**
- Brak zależności runtime
- Szybka kompilacja
- Static binary

### 4.2 GitHub Actions — Go

```yaml
name: Build Windows (Go)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest  # Cross-compile z Linux
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.21'
      
      - name: Build for Windows
        env:
          GOOS: windows
          GOARCH: amd64
        run: go build -o myapp.exe
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows-Go
          path: myapp.exe
```

---

## 5. Node.js — Kompilacja na Windows

### 5.1 pkg

```bash
npm install -g pkg
pkg package.json --targets node18-win-x64
```

### 5.2 nexe

```bash
npm install -g nexe
nexe -i app.js -t windows-x64-18.0.0
```

### 5.3 GitHub Actions — Node.js

```yaml
name: Build Windows (Node.js)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build executable
        run: npx pkg . --targets node18-win-x64
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows-Node
          path: "*.exe"
```

---

## 6. Java — Kompilacja na Windows

### 6.1 jpackage (JDK 14+)

```bash
jpackage --name MyApp \
  --input target/ \
  --main-jar myapp.jar \
  --main-class com.example.Main \
  --type exe \
  --win-dir-chooser \
  --win-shortcut \
  --win-menu
```

### 6.2 GitHub Actions — Java

```yaml
name: Build Windows (Java)
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
      
      - name: Build JAR
        run: mvn package
      
      - name: Create installer
        run: |
          jpackage --name MyApp \
            --input target/ \
            --main-jar myapp-1.0.jar \
            --main-class com.example.Main \
            --type exe
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows-Java
          path: "*.exe"
```

---

## 7. Code Signing

### 7.1 Dlaczego signing?

- Windows SmartScreen ostrzega przed niepodpisanymi .exe
- Antivirus mniej agresywnie flaguje
- Profesjonalny wygląd

### 7.2 Opcje

| Opcja | Koszt | Trudność |
|-------|:---:|:---:|
| Brak signingu | 0 | ✅ Łatwa |
| Self-signed | 0 | ⚠️ Średnia |
| Comodo/Sectigo | ~$200/rok | ⚠️ Średnia |
| Azure Trusted Signing | ~$0.10/sign | ✅ Łatwa |

### 7.3 Azure Trusted Signing (zalecane)

```yaml
- name: Sign executable
  if: startsWith(github.ref, 'refs/tags/')
  uses: azure/trusted-signing-action@v0
  with:
    azure-tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    azure-client-id: ${{ secrets.AZURE_CLIENT_ID }}
    azure-client-secret: ${{ secrets.AZURE_CLIENT_SECRET }}
    endpoint: https://eus.codesigning.azure.net/
    code-signing-account-name: MySigningAccount
    certificate-profile-name: MyCertProfile
    files-folder: dist
    files-folder-filter: exe
```

### 7.4 Self-signed certificate

```powershell
# Utwórz certyfikat
New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=MyApp" -CertStoreLocation Cert:\CurrentUser\My

# Podpisz
signtool sign /fd SHA256 /a /n "MyApp" /t http://timestamp.digicert.com MyApp.exe
```

---

## 8. Dystrybucja — Instalatory

### 8.1 NSIS (Nullsoft Scriptable Install System)

```nsis
; installer.nsi
Name "MyApp"
OutFile "MyApp-Installer.exe"
InstallDir "$PROGRAMFILES\MyApp"

Section "Install"
  SetOutPath $INSTDIR
  File /r "dist\*.*"
  CreateShortcut "$DESKTOP\MyApp.lnk" "$INSTDIR\MyApp.exe"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
  RMDir /r "$INSTDIR"
  Delete "$DESKTOP\MyApp.lnk"
SectionEnd
```

```bash
makensis installer.nsi
```

### 8.2 Inno Setup

```iss
; installer.iss
[Setup]
AppName=MyApp
AppVersion=1.0
DefaultDirName={pf}\MyApp
OutputBaseFilename=MyApp-Installer

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{desktop}\MyApp"; Filename: "{app}\MyApp.exe"
```

### 8.3 WiX Toolset (MSI)

```xml
<!-- Product.wxs -->
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="MyApp" Version="1.0" Manufacturer="MyCompany">
    <Package InstallerVersion="500" Compressed="yes"/>
    <Media Id="1" Cabinet="myapp.cab" EmbedCab="yes"/>
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="MyApp">
          <Component Id="MainExecutable" Guid="*">
            <File Id="MyAppEXE" Source="dist\MyApp.exe" KeyPath="yes"/>
          </Component>
        </Directory>
      </Directory>
    </Directory>
  </Product>
</Wix>
```

```bash
candle Product.wxs
light Product.wixobj -o MyApp-Installer.msi
```

---

## 9. GitHub Actions — Kompletny Workflow

### 9.1 Multi-platform build

```yaml
name: Build All Platforms
on:
  push:
    tags: ['v*']

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pyinstaller
      - run: pyinstaller --onefile --windowed app.py
      - uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows
          path: dist/

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pyinstaller
      - run: pyinstaller --onefile app.py
      - uses: actions/upload-artifact@v4
        with:
          name: MyApp-Linux
          path: dist/

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pyinstaller
      - run: pyinstaller --onefile app.py
      - uses: actions/upload-artifact@v4
        with:
          name: MyApp-macOS
          path: dist/

  release:
    needs: [build-windows, build-linux, build-macos]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: artifacts/
      - uses: softprops/action-gh-release@v2
        with:
          files: artifacts/**/*
```

### 9.2 Z testami i linting

```yaml
name: Build Windows
on:
  push:
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pytest
      - run: pytest tests/ -v

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install ruff
      - run: ruff check .

  build:
    needs: [test, lint]
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e . pyinstaller
      - run: pyinstaller --onefile --windowed app.py
      - uses: actions/upload-artifact@v4
        with:
          name: MyApp-Windows
          path: dist/
```

---

## 10. Rozwiązywanie problemów

### 10.1 PyInstaller — ModuleNotFoundError

**Problem:** Brakujące moduły po uruchomieniu .exe

**Rozwiązanie:** Dodaj do `hiddenimports`:
```python
hiddenimports=['missing_module', 'another_module']
```

### 10.2 PyInstaller — Brakujące pliki danych

**Problem:** Skills/resources nie ładują się

**Rozwiązanie:** Sprawdź `datas`:
```python
datas=[('src/data', 'data')]
```

### 10.3 Antivirus flaguje .exe

**Problem:** Windows Defender usuwa plik

**Rozwiązanie:**
- Dodaj wyjątek w antivirus
- Rozważ code signing
- Zgłoś false positive do Microsoft

### 10.4 MSVC — Linker errors

**Problem:** unresolved external symbol

**Rozwiązanie:**
- Sprawdź czy wszystkie biblioteki są zlinkowane
- Dodaj brakujące `.lib` do `target_link_libraries`

### 10.5 MinGW — Qt6 nie działa

**Problem:** Qt6 moduły nie kompilują się z MinGW

**Rozwiązanie:**
- Użyj MSVC zamiast MinGW
- Lub użyj Qt6 z oficjalnym portem MinGW

### 10.6 GitHub Actions — Build trwa zbyt długo

**Problem:** Build > 30 minut

**Rozwiązanie:**
- Włącz cache (`cache: 'pip'` lub `cache: 'npm'`)
- Wyklucz niepotrzebne moduły
- Włącz UPX compression

---

## 11. Porównanie narzędzi

| Język | Narzędzie | Rozmiar .exe | Czas startu | Trudność |
|-------|-----------|:---:|:---:|:---:|
| Python | PyInstaller | 150-200MB | 2-3s | ⚠️ Średnia |
| Python | cx_Freeze | 200-250MB | 2-3s | ⚠️ Średnia |
| C++ | MSVC | 5-20MB | 0.5s | ⚠️ Średnia |
| C++ | MinGW | 5-20MB | 0.5s | ❌ Wysoka |
| Rust | cargo | 2-10MB | 0.3s | ✅ Łatwa |
| Go | go build | 5-15MB | 0.2s | ✅ Łatwa |
| Node.js | pkg | 50-80MB | 1-2s | ⚠️ Średnia |
| Java | jpackage | 50-100MB | 1-2s | ⚠️ Średnia |

---

## 12. Najlepsze praktyki

### 12.1 Struktura projektu

```
myproject/
├── .github/
│   └── workflows/
│       └── build-windows.yml
├── build/
│   └── windows/
│       ├── myapp.spec      # PyInstaller config
│       └── icon.ico        # Ikona
├── src/
│   └── ...
└── README.md
```

### 12.2 Versioning

Używaj tagów git dla wersji:
```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

### 12.3 Changelog

Automatycznie generuj z commitów:
```yaml
- name: Generate changelog
  uses: janitorichq/release-changelog@v1
  with:
    token: ${{ secrets.GITHUB_TOKEN }}
```

### 12.4 Artifact retention

Ustaw `retention-days` dla artifactów:
```yaml
- uses: actions/upload-artifact@v4
  with:
    retention-days: 30
```

---

## 13. Zasoby

### 13.1 Dokumentacja

- PyInstaller: https://pyinstaller.org/
- GitHub Actions: https://docs.github.com/en/actions
- MSVC: https://docs.microsoft.com/cpp/
- MinGW-w64: https://www.mingw-w64.org/
- Rust: https://doc.rust-lang.org/cargo/
- Go: https://go.dev/doc/

### 13.2 Narzędzia

| Narzędzie | Przeznaczenie |
|-----------|---------------|
| PyInstaller | Python → .exe |
| cx_Freeze | Python → .exe (alternatywa) |
| pkg | Node.js → .exe |
| nexe | Node.js → .exe (alternatywa) |
| jpackage | Java → .exe/.msi |
| NSIS | Tworzenie installerów |
| Inno Setup | Tworzenie installerów |
| WiX Toolset | Tworzenie MSI |
| signtool | Code signing |

### 13.3 Szablony GitHub Actions

- Python: https://github.com/actions/starter-workflows
- C++: https://github.com/actions/starter-workflows
- Rust: https://github.com/dtolnay/rust-toolchain
- Multi-platform: https://github.com/softprops/action-gh-release

---

## 14. Podsumowanie

### Rekomendacje

| Scenariusz | Rekomendacja |
|------------|--------------|
| Python app | PyInstaller + GitHub Actions |
| C++ app | MSVC + GitHub Actions |
| Rust app | cargo + GitHub Actions |
| Go app | go build (cross-compile) |
| Node.js app | pkg + GitHub Actions |
| Java app | jpackage + GitHub Actions |
| Cross-compile Linux→Windows | Tylko Go/Rust (C++ odradzane) |
| Code signing | Azure Trusted Signing |
| Installer | NSIS lub Inno Setup |

### Kluczowe zasady

1. **Preferuj native build** w GitHub Actions (windows-latest)
2. **Cross-compile tylko gdy konieczne** (Go/Rust)
3. **Używaj cache** dla szybszych buildów
4. **Testuj na Windows** przed release
5. **Code signing opcjonalny** ale zalecany
6. **Wersjonuj z tagami git** (v1.0.0)

---

**Koniec skillu**

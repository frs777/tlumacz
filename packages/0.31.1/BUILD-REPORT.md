# Tłumacz 0.31.1 — pakiety

Data: 2026-09-10
Architektura hosta: x86_64

## Artefakty

- `tlumacz-0.31.1-1-any.pkg.tar.zst` — Arch Linux / lokalne repozytorium
- `tlumacz_0.31.1-1_all.deb` — Debian package, zbudowany ręcznie na hoście Arch (dpkg-buildpackage nie jest zainstalowany)
- `tlumacz-0.31.1-1.noarch.rpm` — RPM + SRPM, lokalna budowa rpmbuild bez rozwiązywania BuildRequires przez RPM DB
- `tlumacz-0.31.1-x86_64-linuxdeploy.AppImage` — AppImage type 2 zbudowany przez linuxdeploy + appimagetool; używa systemowego Python 3.14 i zależności hosta
- `Tlumacz-0.31.1-windows-x86_64.exe` — Windows x64, zbudowany natywnie na `windows-latest` przez GitHub Actions + PyInstaller 6.22.2 + Python 3.12.10

## Windows

- Workflow GitHub Actions: `build-windows.yml`
- Runner: `windows-latest`
- Python: `3.12.10`
- PyInstaller: `6.22.2`
- Testy: `263 passed, 2 warnings` na etapie Windows CI
- Artefakt: `Tlumacz-0.31.1-windows-x86_64.exe`, SHA-256: `ca0334bbee4eb8ddc0961e977fc8adff12dfd1a04c911dac421a6c6b718ccca3`
- Bazowy EXE nie zawiera ciężkich opcjonalnych backendów `Transformers/Torch`, `OpenVINO` i `FastAPI`; są one celowo wykluczone z bundla Windows.

## Weryfikacja

- PKGBUILD: `namcap` bez błędów; pakiet ma ostrzeżenie/false-positive dla opcjonalnego `uvicorn` oraz opcjonalnych backendów Python/OpenVINO.
- Arch: `makepkg` zakończony sukcesem, SHA-256 zweryfikowane; pakiet dodany do `/home/frs/RepoArch/x86_64/moje-repo.db` (symlink do `moje-repo.db.tar.gz`).
- RPM: `rpmbuild -ba --nodeps` zakończony sukcesem; wygenerowano RPM i SRPM.
- DEB: poprawna struktura `ar` (`debian-binary`, `control.tar.gz`, `data.tar.gz`) oraz obecność plików aplikacji zweryfikowane. Pełny `dpkg-buildpackage`/`lintian` nie był możliwy na hoście bez narzędzi Debian.
- AppImage: `linuxdeploy` + plugin `appimagetool` zakończone sukcesem; `--appimage-extract` zakończyło się sukcesem; payload zawiera launcher, desktop file, ikonę i `version.py`; wersja z rozpakowanego obrazu to `0.31.1`.

## Ograniczenia środowiska

AppImage został zbudowany i zweryfikowany przez `linuxdeploy` oraz plugin `appimagetool`. Build zgłosił ostrzeżenie o braku AppStream metadata oraz o wielu głównych kategoriach desktop entry. Obraz nadal korzysta z systemowego Python 3.14 i zależności hosta, więc nie jest w pełni samowystarczalnym bundlowaniem bibliotek Python.

Na hoście nie ma `dpkg-buildpackage`, `lintian` ani `sbuild`; dlatego DEB nie jest deklarowany jako zweryfikowany pełnym workflow Debian.

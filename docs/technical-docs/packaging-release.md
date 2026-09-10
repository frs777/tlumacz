# Pakietowanie i wydanie 0.31.1

Data wydania artefaktów: 2026-09-10.

## Artefakty

Pakiety są umieszczone w `packages/0.31.1/`:

- Arch: `tlumacz-0.31.1-1-any.pkg.tar.zst`
- Debian: `tlumacz_0.31.1-1_all.deb`
- RPM: `tlumacz-0.31.1-1.noarch.rpm`
- RPM source: `tlumacz-0.31.1-1.src.rpm`
- AppImage: `tlumacz-0.31.1-x86_64-linuxdeploy.AppImage`
- sumy: `SHA256SUMS`

## Arch Linux

PKGBUILD znajduje się w `packages/0.31.1/PKGBUILD`.

Budowa:

```bash
makepkg -s
```

Po budowie pakiet został dodany do lokalnego repozytorium:
`/home/frs/RepoArch/x86_64/moje-repo.db`.

## Debian

Docelowy workflow to `dpkg-buildpackage -us -uc` oraz kontrola `lintian` i clean build
w `sbuild`. Na hoście Arch użytym do wydania nie były dostępne `dpkg-buildpackage`,
`lintian` ani `sbuild`, dlatego artefakt DEB został złożony z poprawnej struktury
Debiana, ale nie jest deklarowany jako zweryfikowany pełnym workflow Debian.

## RPM

Spec znajduje się w `packaging/build-0.31.1/rpm/tlumacz.spec`.

Na hoście Arch wykonano `rpmbuild -ba --nodeps`; wygenerowano zarówno RPM, jak i SRPM.
Na Fedora/RHEL należy wykonać build z normalnym rozwiązywaniem `BuildRequires`, najlepiej
w `mock`.

## AppImage

AppImage został zbudowany przez `linuxdeploy` z pluginem `appimagetool` i wygenerowany jako
AppImage type-2 dla `x86_64`. Artefakt: `tlumacz-0.31.1-x86_64-linuxdeploy.AppImage`.

Weryfikacja zakończyła się sukcesem: `linuxdeploy`/`appimagetool` utworzyły obraz, a następnie
`--appimage-extract` poprawnie rozpakował payload zawierający launcher, desktop file, ikonę
oraz `tlumacz/version.py` z wersją `0.31.1`.

Obraz nie jest w pełni samowystarczalnym bundlowaniem bibliotek Python: AppRun korzysta z
systemowego Python 3.14 i zależności hosta. Build zgłosił jedynie ostrzeżenia o braku AppStream
`usr/share/metainfo/tlumacz.appdata.xml` oraz o wielu głównych kategoriach desktop entry.

## Powtarzalność

Szczegółowy raport i SHA-256 wszystkich artefaktów znajduje się w
`packages/0.31.1/BUILD-REPORT.md` oraz `packages/0.31.1/SHA256SUMS`.

# Maintainer: frs <frs@users.noreply.github.com>
# Build from a local source tarball (see build-aur.sh). Upload to AUR:
#   replace source with: https://github.com/frs777/tlumacz/archive/v$pkgver.tar.gz

pkgname=tlumacz
pkgver=0.20.0
pkgrel=1
pkgdesc="AI-powered document translator with a Qt GUI"
arch=('any')
url="https://github.com/frs777/tlumacz"
license=('MIT')
depends=(
    'python'
    'pyside6'
    'python-openai'
    'hicolor-icon-theme'
)
optdepends=(
    'python-pypdf: PDF extraction fallback (when poppler is missing)'
    'pandoc: DOCX extraction (docx to Markdown)'
    'poppler: PDF extraction (pdftotext)'
)
makedepends=(
    'python-build'
    'python-installer'
)
source=("tlumacz-$pkgver.tar.gz")
b2sums=('474a5db56ef80d017f1ed9b80bf5d385f08ad4dcbefbeeb8f877e1c9dc4623ea944ec85917557753306dbe15b0cc397021065109a4a266bb836822e1d075619d')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl

    install -Dm644 LICENSE.txt "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 tlumacz.desktop "$pkgdir/usr/share/applications/tlumacz.desktop"
    install -Dm644 tlumacz/qt_gui/resources/tlumacz.svg \
        "$pkgdir/usr/share/icons/hicolor/scalable/apps/tlumacz.svg"
}

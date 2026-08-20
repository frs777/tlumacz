# Maintainer: frs <frs@users.noreply.github.com>
# Build from a local source tarball (see build-aur.sh). Upload to AUR:
#   replace source with: https://github.com/frs777/tlumacz/archive/v$pkgver.tar.gz

pkgname=tlumacz
pkgver=0.17.1
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
b2sums=('3ade7014992dca756c9d6be7f4de347ab767d0fc1c290a34b0d69fc3b058b73614e8e39d8c202fa8376024e9e964bfb1ff0e338a9e770f0b04efdeadf8d68fe1')

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

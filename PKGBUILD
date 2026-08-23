# Maintainer: frs <frs@users.noreply.github.com>
# Build from a local source tarball (see build-aur.sh). Upload to AUR:
#   replace source with: https://github.com/frs777/tlumacz/archive/v$pkgver.tar.gz

pkgname=tlumacz
pkgver=0.19.1
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
b2sums=('38ed38b0b62462a0d7a8067ed31c25ccc442a4ffeb3465caac5ac087c780e41c25e81bf4a0f3ddbb48342f46acb393a3a38c3abec388872be1cf94c9819cec4f')

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

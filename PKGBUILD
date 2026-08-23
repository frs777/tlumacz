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
b2sums=('004070169cf19ac1f7301a5c4bf08f45ba7cf08a2d7730bc0580ab1c8daf74ad168bb89ce1178f7b741abeb0ae6624b8181dcdfb51990c4ef50cf4bb103d9cb2')

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

# Maintainer: frs <frs@users.noreply.github.com>
# Build from a local source tarball (see build-aur.sh). Upload to AUR:
#   replace source with: https://github.com/frs777/tlumacz/archive/v$pkgver.tar.gz

pkgname=tlumacz
pkgver=0.20.1
pkgrel=1
pkgdesc="AI-powered document translator with a Qt GUI"
arch=('any')
url="https://github.com/frs777/tlumacz"
license=('MIT')
depends=(
    'python'
    'pyside6'
    'python-openai'
    'python-pymupdf'
    'hicolor-icon-theme'
)
optdepends=(
    'pandoc: DOCX extraction (docx to Markdown)'
)
makedepends=(
    'python-build'
    'python-installer'
)
source=("tlumacz-$pkgver.tar.gz")
b2sums=('98402cd5d26a545b2a60d79497053f4aaaf0a3a2b314ad182f7089d27dbdb483f9d97c128b7a534bc0b073b5fc6ca6a04accc1a7872a4ed2fb7deb320f00be25')

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

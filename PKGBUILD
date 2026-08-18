# Maintainer: Agent Translator Team <team@example.com>
# NOTE: Replace url/source with the real repository URL before submitting to AUR.

pkgname=agent-translator
pkgver=0.5.0
pkgrel=1
pkgdesc="AI-powered document translator with a Qt GUI"
arch=('any')
url="https://github.com/protonpass/agent-translator"
license=('MIT')
depends=(
    'python'
    'pyside6'
    'python-openai'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-setuptools'
    'python-wheel'
)
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
# Replace SKIP with the real sha256sum of the release tarball (run: sha256sum file)
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl

    install -Dm644 LICENSE.txt "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 agent-translator.desktop "$pkgdir/usr/share/applications/agent-translator.desktop"
    install -Dm644 agent_translator/qt_gui/resources/agent-translator.svg \
        "$pkgdir/usr/share/icons/hicolor/scalable/apps/agent-translator.svg"
}
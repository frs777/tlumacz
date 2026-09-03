Name:           tlumacz
Version:        0.20.1
Release:        2%{?dist}
Summary:        AI-powered document translator with a Qt GUI

License:        MIT
URL:            https://github.com/frs777/tlumacz
Source0:        %{url}/archive/refs/tags/v%{version}/tlumacz-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-build
BuildRequires:  python3-installer
BuildRequires:  python3-setuptools

Requires:       python3
Requires:       python3-pyside6
Requires:       python3-openai
Requires:       python3-pymupdf
Requires:       hicolor-icon-theme

%description
Tłumacz is a Qt/PySide6 application for translating documents using
LLM models compatible with the OpenAI API. Supports Markdown, TXT,
HTML, PDF, DOCX, ODT and EPUB formats with round-trip preservation.

%prep
%autosetup -n tlumacz-%{version}

%build
python3 -m build --wheel --no-isolation

%install
python3 -m installer --destdir=%{buildroot} dist/*.whl

install -Dpm0644 LICENSE.txt %{buildroot}%{_licensedir}/%{name}/LICENSE.txt
install -Dpm0644 tlumacz.desktop %{buildroot}%{_datadir}/applications/tlumacz.desktop
install -Dpm0644 tlumacz/qt_gui/resources/tlumacz.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/tlumacz.svg

%files
%doc README.md
%{_bindir}/tlumacz
/usr/lib/python3*/site-packages/tlumacz/
/usr/lib/python3*/site-packages/tlumacz-*.dist-info/
%{_datadir}/applications/tlumacz.desktop
%{_datadir}/icons/hicolor/scalable/apps/tlumacz.svg
%{_licensedir}/%{name}/

%changelog
* Thu Sep 03 2026 frs <frs@users.noreply.github.com> - 0.20.1-2
- Added PyMuPDF dependency for PDF translation
- Fixed ODT/EPUB/HTML translation bugs
- Added i18n support (PL/EN)
- Split settings into 2 tabs (API+Server | Extras)
- Window geometry persistence

* Thu Sep 03 2026 frs <frs@users.noreply.github.com> - 0.20.1-1
- Initial RPM package for v0.20.1

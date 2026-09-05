"""Smoke tests for the Qt main window (offscreen)."""

import multiprocessing as mp
import time

import pytest

pytest.importorskip("PySide6")


def _sleep_process() -> None:
    time.sleep(30)


def _cancellable_process(cancel_event: mp.Event) -> None:
    """Process that exits when cancel_event is set."""
    while not cancel_event.is_set():
        time.sleep(0.1)


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    return app


def test_window_builds(qapp, config_home):
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    assert window.windowTitle() == "Tłumacz"
    window.close()


def test_worker_cancel_is_nonblocking_and_sets_event():
    """cancel() must be non-blocking (safe for GUI thread) and set the event.

    The actual process termination is cooperative: the child process checks
    the event between chunks and exits on its own. The worker's monitoring
    loop (TranslateWorker.run()) escalates to terminate/kill if the process
    does not exit within ~3s. See DEBUG_QT.md item C.
    """
    from tlumacz.qt_gui.worker import TranslateWorker

    context = mp.get_context("spawn")
    cancel_event = context.Event()
    worker = TranslateWorker(None, "", "")
    worker._cancel_event = cancel_event

    process = context.Process(target=_cancellable_process, args=(cancel_event,))
    process.start()
    worker._process = process

    # cancel() must return immediately (non-blocking)
    started = time.monotonic()
    worker.cancel()
    elapsed = time.monotonic() - started
    assert elapsed < 0.5, "cancel() should be non-blocking"

    # The event should be set, which will cause the process to exit
    assert cancel_event.is_set()

    # Wait for the cooperative exit (should happen within ~0.2s)
    process.join(timeout=2.0)
    assert not process.is_alive(), "process should exit after cancel_event is set"


def test_skills_checkboxes_and_persistence(qapp, config_home):
    from tlumacz.qt_gui.config import load_settings
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    assert window._skill_checkboxes, "bundled skills should populate checkboxes"

    for checkbox in window._skill_checkboxes:
        if "Markdown" in checkbox.text():
            checkbox.setChecked(True)

    settings = window._collect_settings()
    assert "Markdown" in settings.enabled_skills
    assert window._build_config().enabled_skills == settings.enabled_skills

    # a fresh window reloads the persisted state
    window.close()
    window2 = MainWindow(server=None)
    states = {
        checkbox.text(): checkbox.isChecked()
        for checkbox in window2._skill_checkboxes
    }
    assert states["Markdown — md, markdown"] is True
    window2.close()


def test_config_warning_dialog(qapp, config_home, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from tlumacz.qt_gui.main_window import MainWindow

    path = config_home / "tlumacz" / "config.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{broken", encoding="utf-8")

    shown = []
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args, **kwargs: shown.append(args)
    )
    window = MainWindow(server=None)
    assert shown, "warning dialog should be shown for a broken config"
    window.close()


def test_tabs_and_help(qapp, config_home):
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    tabs = window.tabs
    labels = [tabs.tabText(i) for i in range(tabs.count())]
    assert labels == ["Tłumaczenie", "API i serwer", "Dodatki", "Pomoc"]

    window.help_language.setCurrentIndex(1)  # English
    en_html = window.help_view.toHtml()
    assert "Settings tab" in en_html or "API" in en_html
    window.help_language.setCurrentIndex(0)  # Polish
    assert "API i serwer" in window.help_view.toHtml() or "Ustawienia" in window.help_view.toHtml()
    window.close()


def test_refresh_skills_picks_up_new_user_skill(qapp, config_home):
    from tlumacz.skill import save_skill
    from tlumacz.qt_gui.config import load_settings
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    before = {cb.text() for cb in window._skill_checkboxes}
    assert not any("Nowy skilla" in text for text in before)

    save_skill("", "Nowy skilla", "docx, doc", "Instrukcje.")
    window._on_refresh_skills()
    after = {cb.text() for cb in window._skill_checkboxes}
    assert any("Nowy skilla" in text for text in after)

    settings, warning = load_settings()
    assert warning is None
    assert settings.enabled_skills == window._enabled_skill_names()
    window.close()


def test_translation_activity_indicators(qapp, config_home):
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    window._set_running_state()
    assert not window.spinner_label.isHidden()
    assert window._spinner_timer.isActive()
    assert window._elapsed_display_timer.isActive()
    assert window.elapsed_label.text() == "Czas: 00:00"

    first = window.spinner_label.text()
    window._advance_spinner()
    assert window.spinner_label.text() != first

    window._set_idle_state()
    assert window.spinner_label.isHidden()
    assert not window._spinner_timer.isActive()
    assert not window._elapsed_display_timer.isActive()
    window.close()


def test_elapsed_time_format(qapp, config_home):
    from tlumacz.qt_gui.main_window import MainWindow

    window = MainWindow(server=None)
    assert window._format_elapsed(0) == "Czas: 00:00"
    assert window._format_elapsed(65_000) == "Czas: 01:05"
    assert window._format_elapsed(3_725_000) == "Czas: 01:02:05"
    window.close()

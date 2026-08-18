"""Application menu bar (File, Edit, View, Help) and focus-routed actions."""

from __future__ import annotations

from typing import Callable, Optional, cast

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

# Helpers ----------------------------------------------------------------------


def _focused_text_widget() -> Optional[QWidget]:
    w = QApplication.focusWidget()
    if isinstance(w, (QPlainTextEdit, QTextEdit, QLineEdit)):
        return cast(QWidget, w)
    return None


def _safe_call(widget: QWidget, method_name: str) -> None:
    method = getattr(widget, method_name, None)
    if callable(method):
        try:
            method()
        except Exception:
            # Do not surface focus-routing errors to learners; silently ignore.
            pass


def _bool_attr(widget: QWidget, attr: str, default: bool = False) -> bool:
    try:
        val = getattr(widget, attr, default)
        return bool(val() if callable(val) else val)
    except Exception:
        return default


def _enable_edit_actions(menu: QMenu) -> None:
    """Compute enabled state from the currently focused editable widget."""
    w = _focused_text_widget()
    try:
        undo = cast(QAction, menu.findChild(QAction, "edit.undo"))
        redo = cast(QAction, menu.findChild(QAction, "edit.redo"))
        cut = cast(QAction, menu.findChild(QAction, "edit.cut"))
        copy = cast(QAction, menu.findChild(QAction, "edit.copy"))
        paste = cast(QAction, menu.findChild(QAction, "edit.paste"))
        select_all = cast(QAction, menu.findChild(QAction, "edit.select_all"))
    except RuntimeError:
        return
    if w is None:
        for act in (undo, redo, cut, copy, paste, select_all):
            act.setEnabled(False)
        return
    is_readonly = _bool_attr(w, "isReadOnly", False)
    has_sel = _bool_attr(w, "hasSelectedText", False)
    undo_avail = _bool_attr(w, "isUndoAvailable", True)
    redo_avail = _bool_attr(w, "isRedoAvailable", True)
    undo.setEnabled(not is_readonly and undo_avail)
    redo.setEnabled(not is_readonly and redo_avail)
    cut.setEnabled(not is_readonly and has_sel)
    copy.setEnabled(has_sel)
    paste.setEnabled(not is_readonly)
    select_all.setEnabled(True)


# Public API -------------------------------------------------------------------


def build_menubar(
    window: QMainWindow,
    *,
    on_save: Callable[[], None],
    on_exit: Callable[[], None],
    on_toggle_sidebar: Callable[[], None],
    on_toggle_editor: Callable[[], None],
    on_toggle_theme: Callable[[], None],
) -> QMenuBar:
    bar = QMenuBar(window)

    # File
    file_menu = bar.addMenu("&File")
    act_save = QAction("Save Progress", window)
    act_save.setShortcut(QKeySequence("Ctrl+S"))
    act_save.triggered.connect(on_save)
    file_menu.addAction(act_save)
    file_menu.addSeparator()
    act_exit = QAction("Exit", window)
    act_exit.setShortcut(QKeySequence("Ctrl+Q"))
    act_exit.triggered.connect(on_exit)
    file_menu.addAction(act_exit)

    # Edit (focus-routed)
    edit_menu = bar.addMenu("&Edit")
    edit_menu.aboutToShow.connect(lambda: _enable_edit_actions(edit_menu))
    act_undo = QAction("Undo", edit_menu, objectName="edit.undo")
    act_undo.setShortcuts([QKeySequence.StandardKey.Undo])
    act_undo.triggered.connect(lambda: _safe_call(_focused_text_widget() or QWidget(), "undo"))
    edit_menu.addAction(act_undo)
    act_redo = QAction("Redo", edit_menu, objectName="edit.redo")
    # Windows/Qt include Ctrl+Y and Shift+Ctrl+Z by default via StandardKey
    act_redo.setShortcuts([QKeySequence.StandardKey.Redo])
    act_redo.triggered.connect(lambda: _safe_call(_focused_text_widget() or QWidget(), "redo"))
    edit_menu.addAction(act_redo)
    edit_menu.addSeparator()
    act_cut = QAction("Cut", edit_menu, objectName="edit.cut")
    act_cut.setShortcuts([QKeySequence.StandardKey.Cut])
    act_cut.triggered.connect(lambda: _safe_call(_focused_text_widget() or QWidget(), "cut"))
    edit_menu.addAction(act_cut)
    act_copy = QAction("Copy", edit_menu, objectName="edit.copy")
    act_copy.setShortcuts([QKeySequence.StandardKey.Copy])
    act_copy.triggered.connect(lambda: _safe_call(_focused_text_widget() or QWidget(), "copy"))
    edit_menu.addAction(act_copy)
    act_paste = QAction("Paste", edit_menu, objectName="edit.paste")
    act_paste.setShortcuts([QKeySequence.StandardKey.Paste])
    act_paste.triggered.connect(lambda: _safe_call(_focused_text_widget() or QWidget(), "paste"))
    edit_menu.addAction(act_paste)
    edit_menu.addSeparator()
    act_select_all = QAction("Select All", edit_menu, objectName="edit.select_all")
    act_select_all.setShortcuts([QKeySequence.StandardKey.SelectAll])
    act_select_all.triggered.connect(
        lambda: _safe_call(_focused_text_widget() or QWidget(), "selectAll")
    )
    edit_menu.addAction(act_select_all)

    # View
    view_menu = bar.addMenu("&View")
    act_sidebar = QAction("Curriculum Rail", window, checkable=True, objectName="view.sidebar")
    act_sidebar.setChecked(True)
    act_sidebar.setShortcut(QKeySequence("Ctrl+B"))
    act_sidebar.triggered.connect(on_toggle_sidebar)
    view_menu.addAction(act_sidebar)
    act_editor = QAction("Editor", window, checkable=True, objectName="view.editor")
    act_editor.setChecked(True)
    act_editor.setShortcut(QKeySequence("Ctrl+J"))
    act_editor.triggered.connect(on_toggle_editor)
    view_menu.addAction(act_editor)
    view_menu.addSeparator()
    act_theme = QAction("Toggle Dark/Light Theme", window)
    act_theme.setShortcut(QKeySequence("Ctrl+Shift+D"))
    act_theme.triggered.connect(on_toggle_theme)
    view_menu.addAction(act_theme)

    # Help
    help_menu = bar.addMenu("&Help")
    act_keys = QAction("Keyboard Shortcuts", window)
    act_keys.triggered.connect(
        lambda: _show_help_dialog(
            window,
            "Keyboard Shortcuts",
            (
                "Ctrl+B — Toggle sidebar\n"
                "Ctrl+J — Toggle editor column\n"
                "Ctrl+Shift+D — Toggle dark/light theme\n"
                "Ctrl+Enter — Run code\n"
                "Ctrl+S — Save progress\n"
                "Ctrl+Q — Quit"
            ),
        )
    )
    help_menu.addAction(act_keys)
    act_about = QAction("About Basilisk", window)
    act_about.triggered.connect(
        lambda: _show_help_dialog(
            window,
            "About Basilisk",
            "Basilisk — a native Python learning workspace built with PySide6.",
        )
    )
    help_menu.addAction(act_about)

    # Expose a small sync API so the host can keep checkmarks aligned with state.
    def sync_view_menu(sidebar_visible: bool, editor_visible: bool) -> None:
        act_sidebar.blockSignals(True)
        act_editor.blockSignals(True)
        act_sidebar.setChecked(sidebar_visible)
        act_editor.setChecked(editor_visible)
        act_sidebar.blockSignals(False)
        act_editor.blockSignals(False)

    # type: ignore[attr-defined]
    bar.sync_view_menu = sync_view_menu  # small helper for CourseApp
    # Attach actions for tests/host
    bar._act_editor = act_editor  # type: ignore[attr-defined]
    bar._act_sidebar = act_sidebar  # type: ignore[attr-defined]

    # Keep Edit action enabled states fresh when focus changes
    app = QApplication.instance()
    if app is not None:
        app.focusChanged.connect(lambda _old, _new: _enable_edit_actions(edit_menu))

    return bar


def _show_help_dialog(parent: QMainWindow, title: str, body: str) -> None:
    from PySide6.QtWidgets import QMessageBox

    QMessageBox.information(parent, title, body)


from __future__ import annotations
from contextlib import contextmanager
from typing import Callable

from PyQt4.QtGui import QApplication

import Adams  # type: ignore

PROGRESS_BAR_NAME = '.gui.main.status_toolbar.__PROGRESSBAR__status'
STATUS_LABEL_NAME = '.gui.main.status_toolbar.status_label'

STATUS_CALLBACK: Callable[[str], None] = None
PROGRESS_CALLBACK: Callable[[float], None] = None

class Label:
    def __set_name__(self, owner, name):
        self.storage_name = name # pylint: disable=all

    def __set__(self, instance, value: str):
        value = str(value)
        Adams.evaluate_exp(f'status_print("{value}")')
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.processEvents()
        instance.__dict__[self.storage_name] = value

        if STATUS_CALLBACK is not None:
            STATUS_CALLBACK(value)

    def __get__(self, instance, owner):
        return instance.__dict__[self.storage_name]


class Progress:
    def __set_name__(self, owner, name):
        self.storage_name = name # pylint: disable=all
        self._value = None

    def __set__(self, instance: ProgressBarUpdater, value: float):
        instance.__dict__[self.storage_name] = value
        if any([self.storage_name not in instance.__dict__,
                not Adams.evaluate_exp(f'{PROGRESS_BAR_NAME}.displayed'),
                (not isinstance(value, (float, int))) or self._value != int(value)]):
            self._value = value
            Adams.execute_cmd(f'int slider display slider_name={PROGRESS_BAR_NAME}')
            Adams.execute_cmd(f'int slider set slider_name={PROGRESS_BAR_NAME} value={int(value)}')
            app = QApplication.instance()
            if isinstance(app, QApplication):
                app.processEvents()
            instance.show_label()

            if PROGRESS_CALLBACK is not None:
                PROGRESS_CALLBACK(value)
    
    def __get__(self, instance, owner):
        return instance.__dict__[self.storage_name]


class ProgressBarUpdater():
    progress = Progress()
    label = Label()

    def __init__(self, label='', progress=0):
        self.label = label
        self.progress = progress
    
    def show_label(self):
        self.label = self.label
    
    def reset(self):
        self.progress=0
        self.label = ''
        Adams.execute_cmd(f'int slider undisplay slider_name={PROGRESS_BAR_NAME}')
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.processEvents()

@contextmanager
def progress_bar(init_text=''):
    progress_updater = ProgressBarUpdater(label=init_text)

    try:
        yield progress_updater

    finally:
        progress_updater.reset()

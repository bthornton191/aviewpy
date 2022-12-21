from contextlib import contextmanager

from PyQt4.QtGui import QApplication

import Adams  # type: ignore # noqa # isort: skip

PROGRESS_BAR_NAME = '.gui.main.status_toolbar.__PROGRESSBAR__status'
STATUS_LABEL_NAME = '.gui.main.status_toolbar.status_label'


class Label:
    def __set_name__(self, owner, name):
        self.storage_name = name # pylint: disable=all

    def __set__(self, instance, value: str):
        value = str(value)
        Adams.evaluate_exp(f'status_print("{value}")')
        QApplication.instance().processEvents()
        instance.__dict__[self.storage_name] = value

class Progress:
    def __set_name__(self, owner, name):
        self.storage_name = name # pylint: disable=all

    def __set__(self, instance, value: float):
        Adams.execute_cmd(f'int slider display slider_name={PROGRESS_BAR_NAME}')
        Adams.execute_cmd(f'int slider set slider_name={PROGRESS_BAR_NAME} value={int(value)}')
        instance.show_label()
        QApplication.instance().processEvents()
        instance.__dict__[self.storage_name] = value

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
        QApplication.instance().processEvents()

@contextmanager
def progress_bar(init_text=''):
    progress_updater = ProgressBarUpdater(label=init_text)

    try:
        yield progress_updater

    finally:
        progress_updater.reset()

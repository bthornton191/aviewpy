from __future__ import annotations

from logging import Logger
from contextlib import contextmanager
from typing import Callable, List

import Adams  # type: ignore
from PyQt4.QtGui import QApplication

PROGRESS_BAR_NAME = '.gui.main.status_toolbar.__PROGRESSBAR__status'
STATUS_LABEL_NAME = '.gui.main.status_toolbar.status_label'

STATUS_CALLBACKS: List[Callable[[str], None]] = []
PROGRESS_CALLBACKS: List[Callable[[float], None]] = []


class Label:

    CURRENT_STATUS = ''

    def __set_name__(self, owner, name):
        self.storage_name = name  # pylint: disable=all

    def __set__(self, instance, value: str):
        value = str(value)
        Adams.evaluate_exp(f'status_print("{value.strip()}")')
        self.CURRENT_STATUS = value
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.processEvents()
        instance.__dict__[self.storage_name] = value

        for callback in STATUS_CALLBACKS:

            # Skip empty strings if the callback is a logger
            if not value.strip() and is_logger(callback):
                continue

            callback(value)

    def __get__(self, instance, owner):
        return instance.__dict__[self.storage_name]


class Progress:
    def __set_name__(self, owner, name):
        self.storage_name = name  # pylint: disable=all
        self._value = None

    def __set__(self, instance: ProgressBarUpdater, value: float):
        instance.__dict__[self.storage_name] = value
        if (self.storage_name not in instance.__dict__ or
                None in [self._value, value] or
                int(self._value) != int(value) or
                not self.is_shown()):
            self._value = value
            self.show()
            Adams.execute_cmd(f'int slider set slider_name={PROGRESS_BAR_NAME} value={int(value)}')
            app = QApplication.instance()
            if isinstance(app, QApplication):
                app.processEvents()
            instance.show_label()

            for callback in PROGRESS_CALLBACKS:
                callback(value)

    def __get__(self, instance, owner):
        return instance.__dict__[self.storage_name]

    @staticmethod
    def hide():
        Adams.execute_cmd(f'int slider undisplay slider_name={PROGRESS_BAR_NAME}')

    @staticmethod
    def show():
        Adams.execute_cmd(f'int slider display slider_name={PROGRESS_BAR_NAME}')

    @staticmethod
    def is_shown():
        return Adams.evaluate_exp(f'{PROGRESS_BAR_NAME}.displayed')


class ProgressBarUpdater():
    progress = Progress()
    label = Label()

    def __init__(self, label='', progress=0, bar_hidden=False, inc=0):
        self.label = label
        self.progress = progress
        self.inc = inc

        if bar_hidden:
            Progress.hide()

    def show_label(self):
        self.label = self.label

    def reset(self, progress=0, label='', displayed=False):
        self.progress = progress
        self.label = label

        if not displayed:
            Progress.hide()

        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.processEvents()

    def increment(self, inc=None):
        if inc is None:
            inc = self.inc

        with self.status_callbacks_disabled():
            self.progress += inc

    @contextmanager
    def status_callbacks_disabled(self):
        status_callbacks = STATUS_CALLBACKS.copy()
        STATUS_CALLBACKS.clear()
        try:
            yield
        finally:
            STATUS_CALLBACKS.extend(status_callbacks)


def is_logger(func: Callable) -> bool:
    return (hasattr(func, '__self__') and
            isinstance(func.__self__, Logger))


@contextmanager
def progress_bar(init_text='',
                 bar_hidden=False,
                 inc: float = 0,
                 num_steps: int = None,
                 status_callback: Callable[[str], None] = None,
                 progress_callback: Callable[[float], None] = None):
    """Context manager for a progress bar. The progress bar is updated by setting the `progress`
    attribute of the context manager. If `inc` or `num_steps` are provided, the `increment` method
    can be used to increment the progress bar by the specified amount. The `label` attribute can 
    be used to set the text of the status label.


    Parameters
    ----------
    init_text : str, optional
        The initial text of the status label, by default ''
    bar_hidden : bool, optional
        Hides the progress bar, by default False
    inc : float, optional
        If provided, the `increment` method can be used to increment the progress bar by this 
        amount, by default 0
    num_steps : int, optional
        If provided, the `increment` method can be used to increment the progress bar by 
        `100 / num_steps`, by default None
    status_callback : Callable[[str], None], optional
        If provided, this function will be called with the current status label text, by default
        None
    progress_callback : Callable[[float], None], optional
        If provided, this function will be called with the current progress value, by default None

    Yields
    ------
    ProgressBarUpdater
        The progress bar updater object

    Examples
    --------
    In this example, the progress bar is used to iterate over all parts in the current model.
    ```python
    from aviewpy.ui import progress_bar
    parts = Adams.getCurrentModel().Parts.values()
    with progress_bar('Doing something to all parts...', num_steps=len(parts)) as pbar:
        for part in parts:
            pbar.label = f'Doing something to {part.full_name}'
            ...
            pbar.increment()
    ```

    In this example, a logger is passed as a status call back.
    ```python
    import logging
    from aviewpy.ui import progress_bar
    LOG = logging.getLogger(__name__)

    with progress_bar(status_callback=LOG.info, inc=10) as pbar:
        for i in range(10):
            pbar.label = f'Doing something {i}'
    ```
    """
    # Get the current state of the progress bar so that it can be restored after the context
    if num_steps is not None:
        inc = 100 / num_steps if num_steps > 0 else 100

    current_progress = float(Adams.evaluate_exp(f'{PROGRESS_BAR_NAME}.value'))
    current_status = Label.CURRENT_STATUS
    displayed = bool(Adams.evaluate_exp(f'{PROGRESS_BAR_NAME}.displayed'))

    progress_updater = ProgressBarUpdater(label=init_text, bar_hidden=bar_hidden, inc=inc)

    if status_callback is not None:
        STATUS_CALLBACKS.append(status_callback)
    if progress_callback is not None:
        PROGRESS_CALLBACKS.append(progress_callback)

    try:
        yield progress_updater

    finally:
        progress_updater.reset(current_progress, current_status.strip(), displayed)

        if status_callback is not None:
            STATUS_CALLBACKS.remove(status_callback)
        if progress_callback is not None:
            PROGRESS_CALLBACKS.remove(progress_callback)

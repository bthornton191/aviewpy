from contextlib import contextmanager

import Adams  # type: ignore # noqa


@contextmanager
def adams_errors_suppressed():

    level = Adams.evaluate_exp('user_string(".system_defaults.graphic_window_level")')
    Adams.execute_cmd('interface message graphic_window_level=quiet')
    try:
        yield
    finally:
        Adams.execute_cmd(f'interface message graphic_window_level={level}')


@contextmanager
def adams_warnings_suppressed():

    level = Adams.evaluate_exp('user_string(".system_defaults.threshold")')
    Adams.execute_cmd('interface message threshold=error')
    try:
        yield
    finally:
        Adams.execute_cmd(f'interface message threshold={level}')


def alert_box(msg: str, alert_type: str = 'info', exc_type: Exception = None):
    """Adams View alert box

    Parameters
    ----------
    msg : str
        Text to display
    alert_type : str enum['warning', 'error', 'info']
        Type of alert
    exc_type : Exception, optional
        Exception to raise, by default None
    """
    msg = msg.replace('"', '\'')
    Adams.execute_cmd(f'mdi gui_utl_alert_box_1 type={alert_type} text="{msg}"')

    if exc_type is not None:
        raise exc_type(msg)


from itertools import chain
import traceback
from typing import List, Type

import Adams  # type: ignore

def aview_excepthook(exc_type: Type[Exception], exc_value: Exception, exc_tb: List[str]):
    """A useful excepthook for developing in Adams using the Python api. Normally, Python exceptions
    are shown in the command window and log file, but not shown in the message window like other 
    Adams errors. This makes them easy to miss. This except hook will show a message including 
    traceback in the messages window.

    Note
    ----
    This excepthook aborts and stops all commands

    Parameters
    ----------
    exc_type : Type[Exception]
        Exception Type
    exc_value : Exception
        Exception Value
    exc_tb : List[str]
        Exception Traceback

    Raises
    ------
    exc_type.with_traceback
        Raises the exception with the traceback
    """
    tb = traceback.format_exception(exc_type, exc_value, exc_tb)
    messages = [
        '---------------------------------------------------------------------',
        'Python Error Encountered',
        *chain.from_iterable(s.splitlines() for s in tb),
        '---------------------------------------------------------------------',
    ]

    for msg in messages:
        Adams.execute_cmd('interface message severity = error message = "{}"'
                          .format(msg
                                  .replace('\\', '\\\\')
                                  .replace('"', '\\"')
                                  .rstrip()))
    Adams.execute_cmd('abort stop_all_commands = yes')

    raise exc_type.with_traceback(exc_tb)

import Adams # type: ignore # noqa # isort:skip

def show_message(msg: str, severity: str = 'information'):
    """Show message in Adams View

    Parameters
    ----------
    msg : str
        Message to display
    severity : str enum['information', 'warning', 'error', 'fault']
    """
    msg = msg.replace('"', '\'')
    thresh = Adams.evaluate_exp('user_string(".system_defaults.threshold")')
    Adams.execute_cmd(f'interface message threshold={severity}')
    Adams.execute_cmd(f'interface message message="{msg}" severity={severity}')
    Adams.execute_cmd(f'interface message threshold={thresh}')

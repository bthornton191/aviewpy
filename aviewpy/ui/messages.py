import Adams # type: ignore # noqa # isort:skip

def show_message(msg: str, severity: str = 'information', print_to_terminal: bool = True):
    """Show message in Adams View

    Parameters
    ----------
    msg : str
        Message to display
    severity : str enum['information', 'warning', 'error', 'fault']
        Severity of the message, by default 'information'
    print_to_terminal : bool, optional
        Whether to print the message to the terminal, by default True
    """
    msg = msg.replace('"', '\'')
    thresh = Adams.evaluate_exp('user_string(".system_defaults.threshold")')
    Adams.execute_cmd(f'interface message threshold={severity}')
    Adams.execute_cmd(f'interface message message="{msg}" severity={severity}')
    Adams.execute_cmd(f'interface message threshold={thresh}')

    if print_to_terminal:
        print(msg)

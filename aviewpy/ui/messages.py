import Adams  # type: ignore # noqa # isort:skip


def show_message(msg: str, severity='information', print_to_terminal=True, force_shown=False):
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
    if force_shown:

        # Get the current message threshold
        current_thresh = Adams.evaluate_exp('user_string(".system_defaults.threshold")')

        # Set the message threshold to the given severity
        Adams.execute_cmd(f'interface message threshold={severity}')

    try:

        # Replace double quotes with single quotes (The message window doesn't show double quotes)
        msg = msg.replace('"', '\'')

        # Show the message
        Adams.execute_cmd(f'interface message message="{msg}" severity={severity}')

    finally:

        if force_shown:

            # Set the message threshold back to the original value
            Adams.execute_cmd(f'interface message threshold={current_thresh}')

    if print_to_terminal:

        # Print the message to the terminal if desired
        print(msg)

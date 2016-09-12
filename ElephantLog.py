import logging
import os


def init_log(log_level='debug', file_level='debug', console_level='warn'):
    """
    Initialize the main logging instance and setup the handlers.

    Returns (logging.Logger):
    The Logger instance for the main logger named 'Elephant'.
    """
    # Logger and formatter
    log = logging.getLogger('Elephant')
    log.setLevel(getattr(logging, log_level.upper())
                 if hasattr(logging, log_level.upper())
                 else logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # File handler
    # Add it if and only if it does not appear to exist.
    if os.path.abspath('Elephant.log') not in \
            [h.baseFilename
             for h in log.handlers
             if h.__class__.__name__ == 'FileHandler']:
        fle = logging.FileHandler('Elephant.log')
        fle.setLevel(getattr(logging, file_level.upper())
                     if hasattr(logging, file_level.upper())
                     else logging.DEBUG)
        fle.setFormatter(fmt)
        log.addHandler(fle)

    # Console handler
    # Add it if and only if it does not already appear to exist.
    if 'StreamHandler' not in [h.__class__.__name__ for h in log.handlers]:
        cns = logging.StreamHandler()
        cns.setLevel(getattr(logging, console_level.upper())
                     if hasattr(logging, console_level.upper())
                     else logging.WARN)
        cns.setFormatter(fmt)
        log.addHandler(cns)

    return log

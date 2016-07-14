import logging
import os


def init_log():
    """
    Initialize the main logging instance and setup the handlers.

    Returns (logging.Logger):
    The Logger instance for the main logger named 'Elephant'.
    """
    # Logger and formatter
    log = logging.getLogger('Elephant')
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # File handler
    if os.path.abspath('Elephant.log') not in \
            [h.baseFilename
             for h in log.handlers
             if h.__class__.__name__ == 'FileHandler']:
        fle = logging.FileHandler('Elephant.log')
        fle.setLevel(logging.DEBUG)
        fle.setFormatter(fmt)
        log.addHandler(fle)
    # Console handler
    if 'StreamHandler' not in [h.__class__.__name__ for h in log.handlers]:
        cns = logging.StreamHandler()
        cns.setLevel(logging.WARN)
        cns.setFormatter(fmt)
        log.addHandler(cns)
    return log
import logging


def init_log():
    """
    Initialize the main logging instance and setup the handlers.

    Returns (logging.Logger):
    The Logger instance for the main logget named 'Elephant'.
    """
    # Logger and formatter
    log = logging.getLogger('Elephant')
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    # File handler
    fle = logging.FileHandler('Elephant.log')
    fle.setLevel(logging.DEBUG)
    fle.setFormatter(fmt)
    if fle not in log.handlers:
        log.addHandler(fle)
    # Console handler
    cns = logging.StreamHandler()
    cns.setLevel(logging.WARN)
    cns.setFormatter(fmt)
    if cns not in log.handlers:
        log.addHandler(cns)
    return log
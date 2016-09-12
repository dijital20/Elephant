import glob
import logging
import os

from logging.handlers import RotatingFileHandler


LOG_FILENAME = 'Elephant.log'


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

    # Console handler
    # Add it if and only if it does not already appear to exist.
    if 'StreamHandler' not in [h.__class__.__name__ for h in log.handlers]:
        print('Adding Console Handler')
        cns = logging.StreamHandler()
        cns.setLevel(getattr(logging, console_level.upper())
                     if hasattr(logging, console_level.upper())
                     else logging.WARN)
        cns.setFormatter(fmt)
        log.addHandler(cns)
        log.debug('Added console handler at level {0}'.format(
            log.getEffectiveLevel()))

        # Rotating File handler
        # Add it if and only if it does nto appear to exist.
        if os.path.abspath(LOG_FILENAME) not in \
                [h.baseFilename
                 for h in log.handlers
                 if h.__class__.__name__ == 'RotatingFileHandler']:
            print('Adding Rotating Log File Handler')
            # Delete existing files
            for log_file in glob.glob(
                    os.path.abspath(LOG_FILENAME).replace('.log', '*.log')):
                try:
                    os.remove(log_file)
                    print('Deleted: {0}'.format(log_file))
                except Exception as e:
                    print('ERROR deleting {0}: {1}'.format(log_file, e))
            fle = RotatingFileHandler(LOG_FILENAME, mode='w',
                                      maxBytes='1000000', backupCount=5)
            fle.setLevel(getattr(logging, file_level.upper())
                         if hasattr(logging, file_level.upper())
                         else logging.DEBUG)
            fle.setFormatter(fmt)
            log.addHandler(fle)
            log.debug(
                'Added RotatingFileHandler for Elephant.log at level {0}'.format(
                    log.getEffectiveLevel()))

    return log

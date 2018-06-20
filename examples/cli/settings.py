import os
import sys

__LOG_FORMAT = os.environ.get(
    'LOG_FORMAT', 
    '%(asctime)s.%(msecs).03d[%(levelname)0.3s] %(name)s:%(funcName)s.%(lineno)d %(message)s')

__DATE_FORMAT = os.environ.get('LOG_DATE_FORMAT', '%m-%d %H:%M:%S')

LOGGING_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': __LOG_FORMAT,
            'datefmt': __DATE_FORMAT
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'stdout': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'proctor': {
            'handlers': ['stdout'],
            'level': 'INFO',
            'propagate': False,
        },
        'main': {
            'handlers': ['stdout'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

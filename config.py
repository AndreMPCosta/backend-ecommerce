available_languages = [
    'pt',
    'en-US'
]

domain = 'awesomedowmain.com'

backend_url = 'https://backend.awesomedomain.com'

backend_ip = 'XXX.XXX.XXX.XXX'

shipping_rate = 5
free_shipping = 30

# Pagination
max_rows = 20

from_email = 'random_email@awesomedomain.com'

current_language = 'pt'

# Payment
IBAN = 'PT 0050 XXXX XXXX XXXX XXXX'

sample_logger = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s :: %(client_addr)s - "%(request_line)s" %(status_code)s',
            'datefmt': "%d/%m/%Y %H:%M:%S",
            "use_colors": True
        },
        "access_file": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(asctime)s :: %(client_addr)s - "%(request_line)s" %(status_code)s',
            'datefmt': "%d/%m/%Y %H:%M:%S",
            "use_colors": None
        },
        "error_file": {
            "()": "uvicorn.logging.DefaultFormatter",
        }
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "access_file",
            "filename": "./logs/access.log",
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 500000,
            "backupCount": 4
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "error_file",
            "filename": "./logs/error.log",
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 500000,
            "backupCount": 4
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "DEBUG",
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": [
                "error_file"
            ]
        },
        "uvicorn.access": {
            "handlers": ["access", "access_file"],
            "level": "INFO",
            "propagate": False
        },
    },
}

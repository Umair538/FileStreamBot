from os import environ as env

class Telegram:
    # Aapki direct details yahan set kar di hain
    API_ID = 32540406
    API_HASH = "ea63215cc52356b39dee38ac14767218"
    OWNER_ID = int(env.get("OWNER_ID", 5530237028)) # Isko apni Telegram ID se change kar sakte hain
    ALLOWED_USER_IDS = env.get("ALLOWED_USER_IDS", "").split()
    BOT_USERNAME = "soomi2_bot" # Aapke naye bot ka username
    BOT_TOKEN = "8624171834:AAEkNjC7FWWbr4LpefGx99uPSPWOosnnGBQ"
    CHANNEL_ID = -1003375031883 # Aapke private channel ki ID
    SECRET_CODE_LENGTH = 24

class Server:
    # Hugging Face ke mutabiq server settings (Yeh lazmi hain)
    BASE_URL = "https://somi5765-somi.hf.space" # Aapke HF Space ka direct link
    BIND_ADDRESS = "0.0.0.0"
    PORT = 7860 # Hugging Face par hamesha 7860 port lagta hai, yeh 8080 par nahi chalta!

# LOGGING CONFIGURATION
LOGGER_CONFIG_JSON = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] -> %(message)s',
            'datefmt': '%d/%m/%Y %H:%M:%S'
        },
    },
    'handlers': {
        'file_handler': {
            'class': 'logging.FileHandler',
            'filename': 'event-log.txt',
            'formatter': 'default'
        },
        'stream_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'loggers': {
        'uvicorn': {
            'level': 'INFO',
            'handlers': ['file_handler', 'stream_handler']
        },
        'uvicorn.error': {
            'level': 'WARNING',
            'handlers':['file_handler', 'stream_handler']
        },
        'bot': {
            'level': 'INFO',
            'handlers': ['file_handler', 'stream_handler']
        },
        'hydrogram': {
            'level': 'INFO',
            'handlers': ['file_handler', 'stream_handler']
        }
    }
}

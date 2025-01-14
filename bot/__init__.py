from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig, error as log_error, info as log_info, warning as log_warning
import sys
from socket import setdefaulttimeout
from faulthandler import enable as faulthandler_enable
from telegram.ext import Updater as tgUpdater, Defaults
from os import remove as osremove, path as ospath, environ
from subprocess import Popen, run as srun, PIPE
from time import sleep, time
from threading import Thread, Lock
from dotenv import load_dotenv
from asyncio import get_event_loop

main_loop = get_event_loop()

faulthandler_enable()

setdefaulttimeout(600)

botStartTime = time()

basicConfig(format='[%(levelname)s] [%(name)s] [%(lineno)d] %(message)s',
                    handlers=[FileHandler('log.txt'), StreamHandler()],
                    level=INFO)

LOGGER = getLogger(__name__)

Interval = []
DRIVES_NAMES = []
DRIVES_IDS = []
INDEX_URLS = []
GLOBAL_EXTENSION_FILTER = ['.html', '.php']
user_data = {}

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}

if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)

CONFIG_ENV = environ.get('CONFIG_ENV', None)
if CONFIG_ENV:
    log_info("CONFIG_ENV variable found! Downloading config file ...")
    download_file = srun(["curl", "-sL", f"{CONFIG_ENV}", "-o", "config.env"])
    if download_file.returncode == 0:
        log_info("Config file downloaded as 'config.env'")
    else:
        log_error("Something went wrong while downloading config file! please recheck the CONFIG_ENV variable")
        sys.exit(1)
else:
    log_warning("CONFIG_ENV variable not found! exiting ...")
    sys.exit(1)

TOKEN_PICKLE = environ.get('TOKEN_PICKLE', None)
if TOKEN_PICKLE:
    log_info("TOKEN_PICKLE variable found! Downloading token.pickle file ...")
    download_file = srun(["curl", "-sL", f"{TOKEN_PICKLE}", "-o", "token.pickle"])
    if download_file.returncode == 0:
        log_info("Pickle file downloaded as 'token.pickle'")
    else:
        log_error("Something went wrong while downloading token.pickle file! please recheck the TOKEN_PICKLE variable")

ACCOUNTS_ZIP = environ.get('ACCOUNTS_ZIP', None)
if ACCOUNTS_ZIP:
    log_info("ACCOUNTS_ZIP variable found! Downloading accounts.zip file ...")
    download_file = srun(["curl", "-sL", f"{environ.get('ACCOUNTS_ZIP')}", "-o", "accounts.zip"])
    if download_file.returncode == 0:
        log_info("Service Accounts zip file downloaded as 'accounts.zip'")
    else:
        log_error("Something went wrong while downloading Service Accounts zip file! please recheck the ACCOUNTS_ZIP variable")

load_dotenv('config.env', override=True)

UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
if len(UPSTREAM_REPO) == 0:
   UPSTREAM_REPO = None

UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
if len(UPSTREAM_BRANCH) == 0:
    UPSTREAM_BRANCH = 'main'

if UPSTREAM_REPO:
    if ospath.exists('.git'):
        srun(["rm", "-rf", ".git"])

    fetch_updates = srun([f"git init -q \
                     && git config --global user.email pseudokawaii@gmail.com \
                     && git config --global user.name pseudokawaii \
                     && git add . \
                     && git commit -sm update -q \
                     && git remote add origin {UPSTREAM_REPO} \
                     && git fetch origin -q \
                     && git reset --hard origin/{UPSTREAM_BRANCH} -q"], shell=True)

    if fetch_updates.returncode == 0:
        log_info('Successfully updated with latest commit from UPSTREAM_REPO')
    else:
        log_error('Something went wrong while updating, recheck UPSTREAM_REPO variable!')

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    log_error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

OWNER_ID = environ.get('OWNER_ID', '')
if len(OWNER_ID) == 0:
    log_error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)

TELEGRAM_API = environ.get('TELEGRAM_API', '')
if len(TELEGRAM_API) == 0:
    log_error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)
else:
    TELEGRAM_API = int(TELEGRAM_API)

TELEGRAM_HASH = environ.get('TELEGRAM_HASH', '')
if len(TELEGRAM_HASH) == 0:
    log_error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)

GDRIVE_ID = environ.get('GDRIVE_ID', '')
if len(GDRIVE_ID) == 0:
    GDRIVE_ID = ''

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = '/project/downloads/'
elif not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR = f'{DOWNLOAD_DIR}/'

AUTHORIZED_CHATS = environ.get('AUTHORIZED_CHATS', '')
if len(AUTHORIZED_CHATS) != 0:
    aid = AUTHORIZED_CHATS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {'is_auth': True}

INDEX_URL = environ.get('INDEX_URL', '').rstrip("/")
if len(INDEX_URL) == 0:
    INDEX_URL = ''

STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

AUTO_DELETE_MESSAGE_DURATION = environ.get('AUTO_DELETE_MESSAGE_DURATION', '')
if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
    AUTO_DELETE_MESSAGE_DURATION = 30
else:
    AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = '' if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

CMD_SUFFIX = environ.get('CMD_SUFFIX', '')

SERVER_PORT = environ.get('SERVER_PORT', '') or environ.get('PORT', '')
if len(SERVER_PORT) == 0:
    SERVER_PORT = 80
else:
    SERVER_PORT = int(SERVER_PORT)

STOP_DUPLICATE = environ.get('STOP_DUPLICATE', '')
STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'

VIEW_LINK = environ.get('VIEW_LINK', '')
VIEW_LINK = VIEW_LINK.lower() == 'true'

IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'

USE_SERVICE_ACCOUNTS = environ.get('USE_SERVICE_ACCOUNTS', '')
USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'

config_dict = {'AUTHORIZED_CHATS': AUTHORIZED_CHATS,
               'AUTO_DELETE_MESSAGE_DURATION': AUTO_DELETE_MESSAGE_DURATION,
               'BOT_TOKEN': BOT_TOKEN,
               'CMD_SUFFIX': CMD_SUFFIX,
               'DOWNLOAD_DIR': DOWNLOAD_DIR,
               'GDRIVE_ID': GDRIVE_ID,
               'INDEX_URL': INDEX_URL,
               'IS_TEAM_DRIVE': IS_TEAM_DRIVE,
               'OWNER_ID': OWNER_ID,
               'SERVER_PORT': SERVER_PORT,
               'STATUS_LIMIT': STATUS_LIMIT,
               'STATUS_UPDATE_INTERVAL': STATUS_UPDATE_INTERVAL,
               'STOP_DUPLICATE': STOP_DUPLICATE,
               'TELEGRAM_API': TELEGRAM_API,
               'TELEGRAM_HASH': TELEGRAM_HASH,
               'USE_SERVICE_ACCOUNTS': USE_SERVICE_ACCOUNTS,
               'VIEW_LINK': VIEW_LINK}
if GDRIVE_ID:
    DRIVES_NAMES.append("Main")
    DRIVES_IDS.append(GDRIVE_ID)
    INDEX_URLS.append(INDEX_URL)

if ospath.exists('accounts.zip'):
    if ospath.exists('accounts'):
        srun(["rm", "-rf", "accounts"])
    srun(["unzip", "-q", "-o", "accounts.zip", "-x", "accounts/emails.txt"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove('accounts.zip')
if not ospath.exists('accounts'):
    config_dict['USE_SERVICE_ACCOUNTS'] = False
sleep(0.5)

Popen(["gunicorn", "web.wserver:app", "--bind", f"0.0.0.0:{SERVER_PORT}", "--access-logfile", "/dev/null", "--error-logfile", "/dev/null"])
log_info(f"HTTP server started at port {SERVER_PORT}")

tgDefaults = Defaults(parse_mode='HTML', disable_web_page_preview=True, allow_sending_without_reply=True, run_async=True)
updater = tgUpdater(token=BOT_TOKEN, defaults=tgDefaults, request_kwargs={'read_timeout': 20, 'connect_timeout': 15})
bot = updater.bot
dispatcher = updater.dispatcher
job_queue = updater.job_queue

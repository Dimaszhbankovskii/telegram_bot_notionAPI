import logging
from pydantic import Field
from pydantic_settings import BaseSettings


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

console_handler = logging.StreamHandler()

logger = logging.getLogger('my_bot')
logger.addHandler(console_handler)


class CredsNotionAPI(BaseSettings):
    search_path: str = Field('https://api.notion.com/v1/search', env='SEARCH_PATH_NOTION')
    search_databases_path: str = Field('https://api.notion.com/v1/databases', env='SEARCH_DATABASES_PATH_NOTION')
    authorization_header: str = Field('Bearer secret_TRXbcIjGWyXkKJdXjEj2jF06e03ZidnpWhkHSMdo3zE',
                                      env='AUTHORIZATION_HEADER_NOTION')
    version: str = Field('2021-08-16', env='VERSION_NOTION')
    bot_token: str = Field('6308344660:AAGf_frIZ4AKW3gPDN8dVMNdpZ_cJUknq5w', env='BOT_TOKEN')


creds_notion_api: CredsNotionAPI = CredsNotionAPI()

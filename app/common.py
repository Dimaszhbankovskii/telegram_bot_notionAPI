import logging
from opentelemetry import trace
from pydantic import Field
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def log_info(message: str):
    # with tracer.start_as_current_span("models_files") as span:
    logger.info(message.encode('unicode_escape').decode())


def log_error(message: str):
    with tracer.start_as_current_span("models_files") as span:
        logger.error(message.encode('unicode_escape').decode())


def log_debug(message: str):
    with tracer.start_as_current_span("models_files") as span:
        logger.debug(message.encode('unicode_escape').decode())


class CredsNotionAPI(BaseSettings):
    search_path: str = Field('https://api.notion.com/v1/search', env='SEARCH_PATH_NOTION')
    authorization_header: str = Field('Bearer secret_TRXbcIjGWyXkKJdXjEj2jF06e03ZidnpWhkHSMdo3zE',
                                      env='AUTHORIZATION_HEADER_NOTION')
    version: str = Field('2021-08-16', env='VERSION_NOTION')
    bot_token: str = Field('6308344660:AAGf_frIZ4AKW3gPDN8dVMNdpZ_cJUknq5w', env='BOT_TOKEN')


creds_notion_api: CredsNotionAPI = CredsNotionAPI()

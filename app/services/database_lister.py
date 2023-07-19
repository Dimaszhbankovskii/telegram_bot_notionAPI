import re
from uuid import UUID

from services.request_operator import get_request_operator, RequestOperator
from schemas.common_data import common_data_notion
from schemas.database import Database


# def get_database_lister():
#     return DatabaseLister()


class DatabaseLister:
    """
    Класс для получения списка баз данных, с которыми идет взаимодействие через TelegramBot
    """

    def __init__(self,
                 request_operator: RequestOperator) -> None:
        self.common_data = common_data_notion
        self.__request_operator = request_operator
        self.__request_body_database_lister = {
            "filter": {
                "value": "database",
                "property": "object"
            }
        }
        self.__template_name_workout_database = re.compile(r'^Тренировка.')

    async def __get_model_databases(self) -> list[Database]:
        """
        Метод получения всех баз данных

        :return:
        """
        resp: dict = await self.__request_operator.post_request_response_data(
            url=self.common_data.url_search,
            headers=self.common_data.mandatory_headers | self.common_data.content_json_header,
            data=self.__request_body_database_lister
        )
        databases: list[dict] = resp.get('results')
        return [Database.model_validate(db) for db in databases]

    async def get_all_databases(self) -> dict[UUID, str]:
        databases: list[Database] = await self.__get_model_databases()
        return {db.id: db.title[0].plain_text for db in databases}

    async def get_workout_databases(self) -> dict[UUID, str]:
        """
        Метод получения баз данных для тренировок

        :return:
        """
        databases: list[Database] = await self.__get_model_databases()
        return {
            db.id: db.title[0].plain_text for db in databases
            if re.match(self.__template_name_workout_database, db.title[0].plain_text)
        }

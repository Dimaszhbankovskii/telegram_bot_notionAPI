import re
from uuid import UUID

from services.request_operator import RequestOperator
from schemas.entry_database import EntryDB
from schemas.common_data import common_data_notion
from schemas.database import Database


class DatabaseOperator:

    def __init__(self,
                 request_operator: RequestOperator) -> None:
        self._common_data = common_data_notion
        self._request_operator = request_operator
        self._request_body_database_lister = {
            "filter": {
                "value": "database",
                "property": "object"
            }
        }
        self._request_body_page_lister = {
            "filter": {
                "value": "page",
                "property": "object"
            }
        }


class DatabaseWorkoutOperator(DatabaseOperator):

    def __init__(self,
                 request_operator: RequestOperator) -> None:
        super().__init__(request_operator=request_operator)
        self.template_exercise = re.compile(r'^[1-9].')
        self.template_exercise_number = re.compile(r"^[1-9].[1-9]$")

    async def __get_model_databases_by_title(self, title: str) -> list[Database]:
        """
        Метод получения всех баз данных

        :return:
        """
        resp: dict = await self._request_operator.post_request_response_data(
            url=self._common_data.url_search,
            headers=self._common_data.mandatory_headers | self._common_data.content_json_header,
            data=self._request_body_database_lister | {'query': title}
        )
        databases: list[dict] = resp.get('results')
        return [Database.model_validate(db) for db in databases]

    async def get_database_by_id(self, id: UUID, title: str) -> Database | None:
        databases: list[Database] = await self.__get_model_databases_by_title(title)
        for db in databases:
            if db.id == id:
                return db
        return None

    async def __get_last_raw_entry_by_database_id(self,
                                                  database_id: UUID,
                                                  title: str) -> EntryDB:
        """
        Поучение последней записи таблицы в необработанном виде

        :return: В случае успеха возвращает последнюю запись таблицы в необработанном виде
        :rtype: :obj:`schemas.entry_database`
        """
        resp: dict = await self._request_operator.post_request_response_data(
            url=self._common_data.url_search,
            headers=self._common_data.mandatory_headers | self._common_data.content_json_header,
            data=self._request_body_page_lister | {'query': title}
        )
        results = resp.get('results')
        entries: list[EntryDB] = [EntryDB.model_validate(obj) for obj in results
                                  if obj.get('parent') and obj.get('parent').get('database_id') == str(database_id)]
        entries.sort(key=lambda x: x.created_time, reverse=True)
        return entries[0]

    async def get_last_processed_entry_by_database_id(self,
                                                      database_id: UUID,
                                                      title: str) -> dict[str, int]:
        """
        Получение последней обработанной записи таблицы

        :return: В случае успеха возвращает последнюю запись таблицы в обработанном виде
        :rtype: :obj:`schemas.entry_database`
        """
        raw_entry: EntryDB = await self.__get_last_raw_entry_by_database_id(database_id, title)
        num_exercise_res: dict = {}
        for key, value in raw_entry.properties.items():
            if value.get('type') == 'number' and re.match(self.template_exercise_number, key):
                num_exercise_res[key] = value.get(value.get("type"))
        num_exercise_res = dict(sorted(num_exercise_res.items(), key=lambda para: para[0]))
        return num_exercise_res

    async def get_report_last_workout(self,
                                      database_id: UUID,
                                      title: str) -> dict[str, dict[str, int]]:
        database: Database = await self.get_database_by_id(database_id, title)
        list_exercises: list[str] = database.description[0].plain_text.split('\n')
        exercises: dict[str, str] = {elem.split('. ')[0]: elem.split('. ')[1]
                                     for elem in list_exercises if re.match(self.template_exercise, elem)}
        result_exercises: dict[str, int] = await self.get_last_processed_entry_by_database_id(database_id, title)

        report: dict[str, dict[str, int]] = {}
        for num, exercise in exercises.items():
            report[f'{num}. {exercise}'] = {
                key: value for key, value in result_exercises.items() if key.startswith(f'{num}.')
            }
        return report

    @staticmethod
    def convert_report_to_str_mess(report: dict) -> str:
        """
        Конвертиация отчета в сообщение

        :param report: Отчет
        :type report: :obj:`dict`

        :return: Сообщение об отчете, которое отправляется в телеграмм бот
        :rtype: :obj:`str`
        """
        mess = ''
        for exercise, result in report.items():
            mess += exercise + '\n'
            for num, data in result.items():
                mess += f'{num} -> {data}\n'
        return mess


class DatabaseRunOperator:

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
        self.__request_body_page_lister = {
            "filter": {
                "value": "page",
                "property": "object"
            }
        }

    async def __get_last_raw_entry_by_database_id(self,
                                                  database_id: UUID,
                                                  title: str) -> EntryDB:
        """
        Поучение последней записи таблицы в необработанном виде

        :return: В случае успеха возвращает последнюю запись таблицы в необработанном виде
        :rtype: :obj:`schemas.entry_database`
        """
        resp: dict = await self.__request_operator.post_request_response_data(
            url=self.common_data.url_search,
            headers=self.common_data.mandatory_headers | self.common_data.content_json_header,
            data=self.__request_body_page_lister | {'query': title}
        )
        results = resp.get('results')
        entries: list[EntryDB] = [EntryDB.model_validate(obj) for obj in results
                                  if obj.get('parent') and obj.get('parent').get('database_id') == str(database_id)]
        entries.sort(key=lambda x: x.created_time, reverse=True)
        return entries[0]

    async def get_report_last_workout(self,
                                      database_id: UUID,
                                      title: str) -> dict:
        raw_entry: EntryDB = await self.__get_last_raw_entry_by_database_id(database_id, title)
        report: dict = {
            'Название': raw_entry.properties.get('Название').get('title')[0].get('plain_text'),
            'Дата': raw_entry.properties.get('Дата').get('date').get('start'),
            'Дистанция (км)': raw_entry.properties.get('Дистанция (км)').get('number'),
            'Общее время': raw_entry.properties.get('Общее время').get('formula').get('string'),
            'Средний темп': raw_entry.properties.get('Средний темп').get('formula').get('string'),
            'Сожжено (ккал)': raw_entry.properties.get('Сожжено (ккал)').get('number'),
            'Средний пульс (уд/мин)': raw_entry.properties.get('Средний пульс (уд/мин)').get('number'),
            'Максимальный пульс (уд/мин)': raw_entry.properties.get('Максимальный пульс (уд/мин)').get('number'),
            'Время паузы': raw_entry.properties.get('Время паузы').get('formula').get('string')
        }
        return report

    @staticmethod
    def convert_report_to_str_mess(report: dict) -> str:
        """
        Конвертиация отчета в сообщение

        :param report: Отчет
        :type report: :obj:`dict`

        :return: Сообщение об отчете, которое отправляется в телеграмм бот
        :rtype: :obj:`str`
        """
        return '\n'.join([f'{key}: {value}' for key, value in report.items()])

import logging
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

    async def get_database_by_id(self, database_id: UUID) -> Database | None:
        """
        Метод получения базы данных по id

        :param database_id: id базы данных
        :return: pydantic модель базы данных
        """
        response: dict = await self._request_operator.get_request_response_data(
            url=f'{self._common_data.url_search_databases}/{database_id}',
            headers=self._common_data.mandatory_headers
        )
        logging.info(f'Get database with id {database_id}')
        return Database.model_validate(response)

    async def get_list_record_database(self, database_id: UUID, query: dict | None = None) -> list[dict]:
        """
        Поучение последней записи таблицы в необработанном виде

        :param database_id: id базы данных
        :param query: !!!

        :return: В случае успеха возвращает последнюю запись таблицы в необработанном виде
        :rtype: :obj:`schemas.entry_database`
        """
        data = query if query else {}
        response: dict = await self._request_operator.post_request_response_data(
            url=f'{self._common_data.url_search_databases}/{database_id}/query',
            headers=self._common_data.mandatory_headers | self._common_data.content_json_header,
            data=data
        )
        logging.info(f'Get list records of database with id {database_id}')
        return response.get('results')


class DatabaseWorkoutOperator(DatabaseOperator):

    def __init__(self,
                 request_operator: RequestOperator) -> None:
        super().__init__(request_operator=request_operator)
        self.template_exercise = re.compile(r'^[1-9].')
        self.template_exercise_number = re.compile(r"^[1-9].[1-9]$")

    async def get_last_processed_record_by_date(self, database_id: UUID) -> dict[str, int]:
        """
        Получение последней обработанной записи таблицы

        :return: В случае успеха возвращает последнюю запись таблицы в обработанном виде
        :rtype: :obj:`schemas.entry_database`
        """
        records: list[dict] = await self.get_list_record_database(
            database_id=database_id,
            query={"sorts": [{"property": "Дата",
                              "direction": "descending"}]}
        )
        record: EntryDB = EntryDB.model_validate(records[0])
        num_exercise_res: dict = {}
        for key, value in record.properties.items():
            if value.get('type') == 'number' and re.match(self.template_exercise_number, key):
                num_exercise_res[key] = value.get(value.get("type"))
        num_exercise_res = dict(sorted(num_exercise_res.items(), key=lambda para: para[0]))
        return num_exercise_res

    async def get_report_last_workout(self, database_id: UUID) -> dict[str, dict[str, int]]:
        database: Database = await self.get_database_by_id(database_id)
        list_exercises: list[str] = database.description[0].plain_text.split('\n')
        exercises: dict[str, str] = {elem.split('. ')[0]: elem.split('. ')[1]
                                     for elem in list_exercises if re.match(self.template_exercise, elem)}
        result_exercises: dict[str, int] = await self.get_last_processed_record_by_date(database_id)

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


class DatabaseRunOperator(DatabaseOperator):

    def __init__(self,
                 request_operator: RequestOperator) -> None:
        super().__init__(request_operator=request_operator)

    async def get_report_last_workout(self, database_id: UUID) -> dict:
        records: list[dict] = await self.get_list_record_database(
            database_id=database_id,
            query={"sorts": [{"property": "Дата",
                              "direction": "descending"}]}
        )
        record: EntryDB = EntryDB.model_validate(records[0])
        report: dict = {
            'Название': record.properties.get('Название').get('title')[0].get('plain_text'),
            'Дата': record.properties.get('Дата').get('date').get('start'),
            'Дистанция (км)': record.properties.get('Дистанция (км)').get('number'),
            'Общее время': record.properties.get('Общее время').get('formula').get('string'),
            'Средний темп': record.properties.get('Средний темп').get('formula').get('string'),
            'Сожжено (ккал)': record.properties.get('Сожжено (ккал)').get('number'),
            'Средний пульс (уд/мин)': record.properties.get('Средний пульс (уд/мин)').get('number'),
            'Максимальный пульс (уд/мин)': record.properties.get('Максимальный пульс (уд/мин)').get('number'),
            'Время паузы': record.properties.get('Время паузы').get('formula').get('string')
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

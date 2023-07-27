import logging
import re
import datetime
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

    def get_field(self, data: dict, name: str):
        field = data.get(name)
        match field.get('type'):
            case 'number':
                return field.get('number')
            case 'string':
                return field.get('string')
            case 'date':
                return field.get('date').get('start')
            case 'title':
                return field.get('title')[0].get('plain_text')
            case 'formula':
                return self.get_field({'formula': field.get('formula')}, 'formula')

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
        self.params = ('Название', 'Дата', 'Дистанция (км)', 'Общее время', 'Средний темп', 'Сожжено (ккал)',
                       'Средний пульс (уд/мин)', 'Максимальный пульс (уд/мин)', 'Время паузы')

    async def get_report_last_workout(self, database_id: UUID) -> dict:
        records: list[dict] = await self.get_list_record_database(
            database_id=database_id,
            query={"sorts": [{"property": "Дата",
                              "direction": "descending"}]}
        )
        record: EntryDB = EntryDB.model_validate(records[0])
        report = {param: self.get_field(record.properties, param) for param in self.params}
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

    def convert_image_str_to_data(self, mess: str) -> dict:
        lines: list[str] = [line for line in mess.split('\n') if line]
        lines_values: list[str] = [line for i, line in enumerate(lines) if i % 2 == 0]
        lines_params: list[str] = [line for i, line in enumerate(lines) if i % 2 == 1]
        data: dict = {}
        for line_params, line_values in zip(lines_params, lines_values):
            params: list[str] = re.split(r'\s+(?=[А-Я])', line_params)
            values: list[str] = line_values.split()
            for param, value in zip(params, values):
                data[param] = value
        return data

    async def send_new_report(self, report: dict, database_id: str | None = "e9949596-756e-40af-abcb-efbac49ee837"):
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "Название": {
                    "title": [
                        {"text": {"content": "Тест. Пробежка"}}
                    ]
                },
                "Дата": {
                    "date": {"start": str(datetime.date.today())}
                },
                "Дистанция (км)": {"number": 10},
                "Сожжено (ккал)": {"number": int(report.get('Сожжено'))},
                "Средний пульс (уд/мин)": {"number": int(report.get('Средний пульс'))},
                "Максимальный пульс (уд/мин)": {"number": int(report.get('Макс. пульс'))},
                "Время (часы)": {"number": int(report.get('Время тренировки').split(':')[0])},
                "Время (минуты)": {"number": int(report.get('Время тренировки').split(':')[1])},
                "Время (секунды)": {"number": int(report.get('Время тренировки').split(':')[2])},
                "Время паузы (часы)": {"number": int(report.get('Время пауз').split(':')[0])},
                "Время паузы (минуты)": {"number": int(report.get('Время пауз').split(':')[1])},
                "Время паузы (секунды)": {"number": int(report.get('Время пауз').split(':')[2])}
            }
        }
        print(data)
        await self._request_operator.post_request_response_data(
            url='https://api.notion.com/v1/pages',
            headers=self._common_data.mandatory_headers | self._common_data.content_json_header,
            data=data
        )

import logging
import io
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, User
from uuid import UUID
from PIL import Image

from services.database_lister import DatabaseLister
from services.database_operator import DatabaseWorkoutOperator, DatabaseRunOperator
from services.image_operator import ImageOperator


class TelegramBot:

    def __init__(self,
                 token: str,
                 database_lister: DatabaseLister,
                 database_workout_operator: DatabaseWorkoutOperator,
                 database_run_operator: DatabaseRunOperator) -> None:
        self.token = token
        self.database_lister = database_lister
        self.database_workout_operator = database_workout_operator
        self.database_run_operator = database_run_operator

        self.bot = AsyncTeleBot(token=token)

        @self.bot.message_handler(commands=['start'])
        async def command_start(message):
            """
            Команда старта
            """
            await self.__command_start(message)

        @self.bot.message_handler(content_types=['text'])
        async def work_flow(message):
            """
            Рабочий процесс
            """
            await self.__work_flow(message)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('database/')
                                         and call.data.endswith('/operations'))
        async def get_database_operation(call):
            await self.__get_database_operation(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('database/')
                                         and call.data.endswith('/last_result'))
        async def process_database_operation(call):
            await self.__process_database_operation(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('database/')
                                         and call.data.endswith('/new_result'))
        async def process_database_operation_tmp(call):
            await self.__process_database_operation_tmp(call)

        @self.bot.message_handler(content_types=['document'])
        async def process_file(message):
            await self.__process_file(message)

    async def __command_start(self, message):
        logging.info('Bot starting to work')
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton(text="👋 Поздороваться"))
        keyboard.add(KeyboardButton(text="🦾 Тренировки"))
        user_data: User = message.from_user
        await self.bot.send_message(chat_id=message.chat.id,
                                    text=f"Привет, {user_data.first_name}! Я бот для взаимодействия с твоим Notion.\n"
                                         f"Выбери желаемое действие ниже ...",
                                    reply_markup=keyboard)

    async def __work_flow(self, message):
        logging.info(f'Bot processing workflow message "{message.text}"')
        if message.text == "👋 Поздороваться":
            await self.bot.send_message(chat_id=message.chat.id,
                                        text="Привет! Спасибо, что пользуешься мной!)")
        elif message.text == "🦾 Тренировки":
            workout_databases: dict[UUID, str] = await self.database_lister.get_workout_databases()
            workout_keyboard_menu = InlineKeyboardMarkup()
            for key, value in workout_databases.items():
                workout_keyboard_menu.add(InlineKeyboardButton(text=value,
                                                               callback_data=f'database/{key}/operations'))
            await self.bot.send_message(chat_id=message.chat.id,
                                        text="Выберите тренировку:",
                                        reply_markup=workout_keyboard_menu)

    async def __get_database_operation(self, call):
        params: list[str] = call.data.split('/')
        data_type: str = params[0]
        database_id: UUID = UUID(params[1])
        action: str = params[2]
        logging.info(f'Bot displaying a list of commands for database "{database_id}"')

        databases: dict[UUID, str] = await self.database_lister.get_all_databases()
        if not databases.get(database_id):
            # TODO: error
            print('Error !!!')

        workout_keyboard_menu = telebot.types.InlineKeyboardMarkup()
        workout_keyboard_menu.add(InlineKeyboardButton(text='Показать результат последней тренировки',
                                                       callback_data=f'{data_type}/{database_id}/last_result'))
        workout_keyboard_menu.add(InlineKeyboardButton(text='Загрузить новую тренировку',
                                                       callback_data=f'{data_type}/{database_id}/new_result'))
        await self.bot.send_message(chat_id=call.message.chat.id,
                                    text=f"Выберите действие для '{databases.get(database_id)}'",
                                    reply_markup=workout_keyboard_menu)

    async def __process_database_operation(self, call):
        params: list[str] = call.data.split('/')
        data_type: str = params[0]
        database_id: UUID = UUID(params[1])
        action: str = params[2]

        databases: dict[UUID, str] = await self.database_lister.get_all_databases()
        if not databases.get(database_id):
            # TODO: error
            print('Error !!!')
        database_title: str = databases.get(database_id)

        if database_title.split('.')[1].strip() == 'Турник':
            report: dict[str, dict[str, int]] = \
                await self.database_workout_operator.get_report_last_workout(database_id=database_id)
            await self.bot.send_message(chat_id=call.message.chat.id,
                                        text=self.database_workout_operator.convert_report_to_str_mess(report))
        elif database_title.split('.')[1].strip() == 'Пробежка':
            report = await self.database_run_operator.get_report_last_workout(database_id=database_id)
            await self.bot.send_message(chat_id=call.message.chat.id,
                                        text=self.database_run_operator.convert_report_to_str_mess(report))

    async def __process_database_operation_tmp(self, call):
        params: list[str] = call.data.split('/')
        data_type: str = params[0]
        database_id: UUID = UUID(params[1])
        action: str = params[2]

        databases: dict[UUID, str] = await self.database_lister.get_all_databases()
        if not databases.get(database_id):
            # TODO: error
            print('Error !!!')
        database_title: str = databases.get(database_id)

        # if database_title.split('.')[1].strip() == 'Турник':
        #     report: dict[str, dict[str, int]] = \
        #         await self.database_workout_operator.get_report_last_workout(database_id=database_id)
        #     await self.bot.send_message(chat_id=call.message.chat.id,
        #                                 text=self.database_workout_operator.convert_report_to_str_mess(report))
        if database_title.split('.')[1].strip() == 'Пробежка':
            print('CHECK !')
            mesg = await self.bot.send_message(call.message.chat.id, 'Отправте скрин тренировки в сообщении')
            # report = await self.database_run_operator.get_report_last_workout(database_id=database_id)
            # await self.bot.send_message(chat_id=call.message.chat.id,
            #                             text=self.database_run_operator.convert_report_to_str_mess(report))

    async def __process_file(self, message):
        if message.caption == 'Тренировка. Пробежка':
            file_info = await self.bot.get_file(message.document.file_id)
            downloaded_file = await self.bot.download_file(file_info.file_path)
            image = Image.open(io.BytesIO(downloaded_file))

            image_operator = ImageOperator()
            text: str = image_operator.parse_image_to_string(image)
            data: dict = self.database_run_operator.convert_image_str_to_data(text)
            print('----------')
            print(data)
            print('----------')
            await self.database_run_operator.send_new_report(data)

    async def run(self):
        await self.bot.infinity_polling()

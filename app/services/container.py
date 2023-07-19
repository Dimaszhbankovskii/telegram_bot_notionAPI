from dependency_injector import containers, providers

from services.telegram_bot import TelegramBot
from services.database_lister import DatabaseLister
from services.request_operator import RequestOperator
from services.database_workout import DatabaseWorkoutOperator, DatabaseRunOperator


class ApplicationContainer(containers.DeclarativeContainer):
    request_operator = providers.Singleton(RequestOperator)

    database_workout_operator = providers.Singleton(DatabaseWorkoutOperator,
                                                    request_operator=request_operator)

    database_run_operator = providers.Singleton(DatabaseRunOperator,
                                                request_operator=request_operator)

    database_lister = providers.Singleton(DatabaseLister,
                                          request_operator=request_operator)

    telegram_bot = providers.Factory(TelegramBot,
                                     database_lister=database_lister,
                                     database_workout_operator=database_workout_operator,
                                     database_run_operator=database_run_operator)

```mermaid
classDiagram
TelegramBot *-- DatabaseLister
TelegramBot : str token
TelegramBot : run()

DatabaseLister : get_workout_databases()
```
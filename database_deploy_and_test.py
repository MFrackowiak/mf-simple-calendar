from calendar.database_manager import DatabaseManager


if __name__ == '__main__':
    try:
        db_manager = DatabaseManager(False)
    except ConnectionError as e:
        print(str(e))

    db_manager = DatabaseManager(True)
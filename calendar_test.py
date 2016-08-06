from calendar.calendar import Calendar


if __name__ == '__main__':
    calendar = Calendar()

    print(calendar.add_user("Test1", "Test2345", 0))
    print(calendar.add_user("           Test1         ", "                        Test2345", 0))

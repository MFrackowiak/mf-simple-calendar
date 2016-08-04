from calendar.var_utils import get_password_hash


if __name__ == '__main__':
    a = get_password_hash("admin1")
    print(a)
    print(len(a))

    b = get_password_hash("ęąśćłó")
    print(b)
    print(len(b))
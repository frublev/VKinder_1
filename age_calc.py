from datetime import datetime


def get_age(str_age):
    age = datetime.now() - datetime.strptime(str_age, '%d.%m.%Y')
    age = int(age.days / 365)
    return age

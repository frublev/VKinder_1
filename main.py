import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from db_mongo import MongoDB
from random import randrange
from vk_manager import vk_connect, start_implicit_flow, check_token
from db_updating import get_best


app_token = ''


def write_msg(recipient, message, attachments=None):
    vk.messages.send(
        user_id=recipient,
        message=message,
        random_id=randrange(10 ** 7),
        attachment=attachments
    )


if __name__ == '__main__':
    step = 0
    vk_user, user_id = None, None
    users_db = MongoDB('users').collection
    vk_session = vk_api.VkApi(token=app_token)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me and step == 0:
                user_in_db = users_db.find_one({'_id': event.user_id})
                try:
                    if user_in_db['token']:
                        pass
                except TypeError:
                    step = 1
                    url = start_implicit_flow()
                    write_msg(
                        event.user_id,
                        f"Хай, {event.user_id}, для получения токена пройдите по ссылке {url}, затем введите токен"
                    )
                else:
                    token_status = check_token(user_in_db['token'])
                    if token_status == 1:
                        vk_user = vk_connect(user_in_db['token'])
                        write_msg(
                            event.user_id,
                            f"Хай, {event.user_id}, у вас валидный токен. Продолжим? (да/нет)"
                        )
                        step = 2
                    else:
                        step = 1
                        url = start_implicit_flow()
                        write_msg(
                            event.user_id,
                            f"Хай, {event.user_id}, для получения токена пройдите по ссылке {url}, затем введите токен"
                        )

            elif event.to_me and step == 1:
                user_token = event.text
                vk_user = vk_connect(user_token)
                user_id = event.user_id
                write_msg(event.user_id, "Подождите немного...")
                the_best = get_best(vk_user, user_id, users_db, user_token)
                photos = the_best.get_photos(vk_user, 3)
                write_msg(event.user_id, "Результат:", photos)
                write_msg(event.user_id, "Желаете еще? (да/нет)")
                step = 2

            elif event.to_me and step == 2:
                request = event.text
                if request == "да":
                    the_best = get_best(vk_user, user_id, users_db)
                    photos = the_best.get_photos(vk_user, 3)
                    write_msg(event.user_id, "Пожалуйста", photos)
                    write_msg(event.user_id, "Желаете еще? (да/нет)")
                elif request == "нет":
                    write_msg(event.user_id, "Как хотите")
                    step = 0
                else:
                    write_msg(event.user_id, "Не понял вашего ответа...")
                    step = 0

import vk_api
import requests

API_VERSION = '5.131'
APP_ID = 7907533
SCOPE = 1024

serv_token = ''


def start_implicit_flow():
    url = f'https://oauth.vk.com/authorize?client_id={APP_ID}&display=page&redirect_uri=https://oauth.vk.com/blank' \
          f'.html&scope={SCOPE}&response_type=token&v={API_VERSION}'
    return url


def vk_connect(token):
    connect_params = {'token': token, 'app_id': APP_ID, 'api_version': API_VERSION}
    vk_session = vk_api.VkApi(**connect_params)
    return vk_session


def check_token(token):
    api = "https://api.vk.com/method/secure.checkToken"
    params = {'token': token, 'access_token': serv_token, "v": API_VERSION}
    response = requests.get(api, params)
    token_info = response.json()
    token_status = None
    try:
        if token_info['response']:
            if token_info['response']['success'] == 1:
                token_status = 1
            else:
                token_status = "Токен не валиден"
            pass
    except KeyError:
        try:
            if token_info['error']['error_code'] == 15:
                token_status = "Некорректный токен"
            else:
                token_status = token_info['error']['error_msg']
        except KeyError:
            token_status = "Неизвестная ошибка"
    return token_status

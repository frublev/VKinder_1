import vk_api
import re
import datetime
from datetime import datetime
from age_calc import get_age
from weight_ratio import AGE_M, AGE_F, CF_I_M_B, CF_FRIENDS, CF_GROUPS


class User:
    def __init__(self, id, sex=1, place=1, age=30, friends=None, friends_friends=None, groups=None, groups_members=None,
                 interests=None, music=None, books=None, params=None, score=1, old_candidates=None, actual_date=None):
        if friends is None:
            friends = []
        if books is None:
            books = []
        if music is None:
            music = []
        if interests is None:
            interests = []
        if groups_members is None:
            groups_members = []
        if groups is None:
            groups = []
        if friends_friends is None:
            friends_friends = set()
        if friends is None:
            friends = []
        self.id = id
        self.sex = sex
        self.place = place
        self.age = age
        self.friends = friends
        self.friends_friends = friends_friends
        self.groups = groups
        self.groups_members = groups_members
        self.interests = interests
        self.music = music
        self.books = books
        self.params = params
        self.score = score
        self.old_candidates = old_candidates
        self.actual_date = actual_date

    def initial_data_for_mongo(self):
        data_for_mongo = {
            '_id': self.id,
            'params': self.params,
            'actual_date': self.actual_date
        }
        return data_for_mongo

    def _score_i_m_b(self, user0, score_type):
        in_str = None
        check_interests = None
        if score_type == 'interests':
            in_str = user0.interests
            check_interests = self.interests
        elif score_type == 'music':
            in_str = user0.music
            check_interests = self.music
        elif score_type == 'books':
            in_str = user0.books
            check_interests = self.books
        our_interests = []
        for interest in in_str:
            interest = interest.strip()
            regex = re.compile(re.escape(interest), re.IGNORECASE)
            result = regex.findall(check_interests)
            if result:
                our_interests.append(interest)
        if our_interests:
            cf_ = CF_I_M_B.get(score_type)
            cf = cf_[0] + (len(our_interests) - 1) * cf_[1]
        else:
            cf = 1
        return cf

    def score_user(self, user0, common_friends=0):
        age_dif = self.age - user0.age
        age_dif = str(age_dif)
        if user0.sex == 1:
            cf_age = AGE_F.get(age_dif)
        else:
            cf_age = AGE_M.get(age_dif)
        if common_friends and common_friends <= CF_FRIENDS[2]:
            cf_friends = CF_FRIENDS[0] + CF_FRIENDS[1] * (common_friends - 1)
        elif common_friends > CF_FRIENDS[2]:
            cf_friends = CF_FRIENDS[0] + CF_FRIENDS[1] * CF_FRIENDS[2]
        else:
            cf_friends = 1
        count_group = user0.groups_members.count(self.id)
        if count_group and count_group <= CF_GROUPS[2]:
            cf_groups = CF_GROUPS[0] + CF_GROUPS[1] * (count_group - 1)
        elif count_group > CF_GROUPS[2]:
            cf_groups = CF_GROUPS[0] + CF_GROUPS[1] * CF_GROUPS[2]
        else:
            cf_groups = 1
        cf_int = self._score_i_m_b(user0, 'interests')
        cf_mus = self._score_i_m_b(user0, 'music')
        cf_bks = self._score_i_m_b(user0, 'books')
        self.score = cf_age * cf_friends * cf_groups * cf_int * cf_mus * cf_bks

    def get_user_info(self, vk):
        params = {
            "user_ids": self.id,
            "fields": "sex,bdate,city,interests,music,books",
            "v": "5.92"
        }
        vk = vk.get_api()
        user = vk.users.get(**params)
        friends = vk.friends.get(user_id=self.id)
        groups = vk.groups.get(user_id=self.id)
        self.sex = user[0]['sex']
        self.place = user[0]['city']['id']
        self.age = get_age(user[0]['bdate'])
        self.friends = set(friends['items'])
        self.groups = groups['items']
        self.interests = user[0]['interests'].split(',')
        self.music = user[0]['music'].split(',')
        self.books = user[0]['books'].split(',')
        print(f'Получена основная информация о пользователе {self.id} (user0)')
        self.friends_n_members(vk)
        self.create_request()
        self.actual_date = datetime.today()

    def friends_n_members(self, vk, f_or_g=False):
        if f_or_g:
            dict_view = self.friends
        else:
            dict_view = self.groups
        id_list = []
        for friend in dict_view:
            try:
                vk_tools = vk_api.VkTools(vk)
                if f_or_g:
                    resp = vk_tools.get_all('friends.get', 5000, {'user_id': friend})
                    print(f'Получены id друзей пользователя {friend} (user0)')
                else:
                    resp = vk_tools.get_all('groups.getMembers', 1000, {'group_id': friend})
                    print(f'Получены id участников группы {friend} (группа, в которой состоит user0)')
                for id_ in resp['items']:
                    id_list.append(id_)
            except vk_api.exceptions.VkToolsException:
                print('vk_api.VkTools вызвало исключение, запущена обработка со сдвигом (offset)')
                try:
                    vk = vk.get_api()
                    if f_or_g:
                        resp = vk.friends.get(user_id=friend, offset=0)
                    else:
                        resp = vk.groups.getMembers(group_id=friend, offset=0)
                    offs = 0
                    while offs <= resp['count']:
                        if f_or_g:
                            ids = vk.friends.get(user_id=friend, offset=offs)
                        else:
                            ids = vk.groups.getMembers(group_id=friend, offset=offs)
                        for id in ids['items']:
                            id_list.append(id)
                        print('\rПолучены id участников группы / друзей друга',
                              friend, ' - ', round((offs + len(ids['items'])) / resp['count'] * 100), '%',
                              end="")
                        offs += 1000
                    if len(id_list) == resp['count']:
                        print(' OK')
                    else:
                        print(' Отклонение:', len(id_list) - resp['count'])
                except vk_api.exceptions.ApiError:
                    pass
        if f_or_g:
            self.friends_friends = id_list
        else:
            self.groups_members = id_list

    def create_request(self):
        if self.sex == 1:
            sex = 2
        else:
            sex = 1
        if self.age < 18:
            raise Exception('You are too young!')
        if self.sex == 1:
            age_from = self.age - 2
            age_to = self.age + 6
        else:
            age_from = self.age - 6
            age_to = self.age + 2
        if age_from < 18:
            age_from = 18
        self.params = {
            'sort': 0,
            'count': 1000,
            'sex': sex,
            'age_from': age_from,
            'age_to': age_to,
            'city': self.place,
            'has_photo': 1,
            'offset': 0,
            'status': 6,
            'fields': 'common_count,interests,music,books'
        }

    def get_candidate(self, vk, old_candidates, top_count):
        self.get_user_info(vk)
        age_range = self.params['age_to'] - self.params['age_from']
        params_ = self.params.copy()
        top_users = [{'vk_id': '', 'score': 0}] * top_count
        for r in range(age_range + 1):
            params_['age_to'] = params_['age_from']
            results = vk_api.requests_pool.vk_request_one_param_pool(
                vk,
                'users.search',
                key='birth_month',
                values=[i for i in range(1, 13)],
                default_values=params_
            )
            results = results[0]
            user_count = 0
            for key_num in results:
                for user in results[key_num]['items']:
                    user_info = User(user['id'], age=params_['age_from'], interests=str(user.get('interests')),
                                     music=str(user.get('music')), books=str(user.get('books')))
                    if user_info.id not in old_candidates:
                        user_info.score_user(self, user.get('common_count'))
                        if user_info.score > top_users[0]['score']:
                            top_users.pop(0)
                            user_info = {
                                'vk_id': user_info.id,
                                'score': user_info.score
                            }
                            top_users.append(user_info)
                            # print(user_info)
                            top_users = sorted(top_users, key=lambda k: k['score'])
                user_count += results[key_num]['count']
            age = params_['age_from']
            print(f'Найдено {user_count} кандидатов в возрасте {age} лет')
            params_['age_from'] += 1
        return top_users

    def get_photos(self, vk, top_count):
        params = {
            'owner_id': self.id,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 0
        }
        vk = vk.get_api()
        photos = vk.photos.get(**params)
        photos = photos['items']
        count_of_photos = len(photos)
        if count_of_photos > 0:
            photos = sorted(photos, key=lambda k: k['likes']['count'], reverse=True)
            top3 = []
            print(photos)
            if count_of_photos > top_count:
                count_of_photos = top_count
            for i in range(count_of_photos):
                attachment = 'photo' + str(photos[i]['owner_id']) + '_' + str(photos[i]['id'])
                top3.append(attachment)
        else:
            top3 = 'Нечем порадовать'
        return top3

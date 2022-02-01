from vk_user.user import User


def best_and_update(user_in_db):
    index_in_top = len(user_in_db['top']) - 1
    best = user_in_db['top'].pop(index_in_top)
    user_in_db['old'].append(best)
    return best


def get_best(vk, user_id, users_db, token=None):
    user_in_db = users_db.find_one({'_id': user_id})
    if not user_in_db or len(user_in_db['top']) == 0:
        user0 = User(user_id)
        if user_in_db:
            old_top = user_in_db['old']
        else:
            old_top = []
        top = user0.get_candidate(vk, old_top, 100)
        user_in_db = {'_id': user_id, 'top': top, 'old': old_top, 'token': token}
    the_best = best_and_update(user_in_db)
    users_db.replace_one({'_id': user_id}, user_in_db, upsert=True)
    return User(the_best['vk_id'])

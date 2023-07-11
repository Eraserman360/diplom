import vk_api

from datetime import datetime
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from conf import comunity_token, acces_token
from Back import VkTools

from BD import Viewed, engine, Users
from sqlalchemy.orm import Session



class BotInterface():

    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.params = None
        self.forms = {}

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': message,
                               'attachment': attachment,
                               'random_id': get_random_id()
                               }
                              )

    def write_to_bd(self, event, user):
        with Session(engine) as session:
            to_bd = Viewed(profile_id=event.user_id, worksheet_id=user['id'])
            session.add(to_bd)
            session.commit()

    def write_to_bd_user_setings_with_sex(self, user_id, sex):
        with Session(engine) as session:
            self.write_to_bd_chek_user_and_add(user_id)
            session.query(Users).filter(Users.profile_id == user_id).update({"sex": sex})
            session.commit()

    def write_to_bd_user_setings_with_age(self, user_id, age):
        with Session(engine) as session:
            self.write_to_bd_chek_user_and_add(user_id)
            session.query(Users).filter(Users.profile_id == user_id).update({"age": age})
            session.commit()

    def write_to_bd_user_setings_with_city(self, user_id, city_id):
        with Session(engine) as session:
            self.write_to_bd_chek_user_and_add(user_id)
            session.query(Users).filter(Users.profile_id == user_id).update({"city": city_id})
            session.commit()

    def write_to_bd_add_user(self, user_id):
        with Session(engine) as session:
            to_bd = Users(profile_id=user_id)
            session.add(to_bd)
            session.commit()

    def write_to_bd_chek_user_and_add(self, user_id):
        with Session(engine) as session:
            users = session.query(Users).filter(Users.profile_id == user_id).all()
            if len(users) == 0:
                self.write_to_bd_add_user(user_id)
                self.write_to_bd_chek_user_and_add(user_id)
            print(users[0])
            return users[0]

    def get_user(self, event, user):
        with Session(engine) as session:
            return session.query(Viewed).filter(Viewed.worksheet_id == user['id'], Viewed.profile_id == event.user_id).all()
    def event_handler(self):
        longpoll = VkLongPoll(self.interface)
        offset = 0
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                if 'город' in command:
                    user_city = command.split()[1]
                    city_id = self.api.get_city(user_city)
                    self.write_to_bd_user_setings_with_city(event.user_id, city_id)
                    self.message_send(event.user_id, f'Город сохранен')
                elif 'возраст' in command:
                    user_age = command.split()[1]
                    self.write_to_bd_user_setings_with_age(event.user_id, user_age)
                    self.message_send(event.user_id, f'Возраст сохранен')
                elif 'пол' in command:
                    user_sex = 2 if command.split()[1] == 'м' else 1
                    self.write_to_bd_user_setings_with_sex(event.user_id, user_sex)
                    self.message_send(event.user_id, f'Пол сохранен')
                elif command == 'поиск':
                    self.params = self.api.get_profile_info(event.user_id)
                    user_from_bd = [self.write_to_bd_chek_user_and_add(event.user_id)]
                    print(self.params)
                    if not ("sex" in self.params):
                        if not("sex" in user_from_bd):
                            return self.message_send(event.user_id,
                                                     f'у Вас не указан пол. Введите Пол через команду Пол [м/ж]')
                        else:
                            self.params['sex'] = user_from_bd['sex']
                    if not ("city" in self.params):
                        if not("city" in user_from_bd):
                            return self.message_send(event.user_id,
                                                     f'у Вас не указан город. Введите город через команду Город [Название]')
                        else:
                            self.params['city'] = user_from_bd['city']
                    if not ("bdate" in self.params):
                        if not("age" in user_from_bd):
                            return self.message_send(event.user_id,
                                                     f'у Вас не указан Возраст. Введите Возраст через команду Возраст [число]')
                        else:
                            today = datetime.today()
                            self.params['bdate'] = today.year - user_from_bd['age']
                    if not(event.user_id in self.forms):
                        self.forms[event.user_id] = []
                    if len(self.forms[event.user_id]) == 0:
                        users = self.api.serch_users(self.params, offset)
                        print(users)
                        self.forms[event.user_id] = users
                    else:
                        users = self.forms[event.user_id]
                    print(self.forms[event.user_id])
                    user = users.pop()
                    self.forms[event.user_id] = users
                    from_bd = self.get_user(event, user)
                    while len(from_bd) != 0:
                        if len(users) == 0:
                            users = self.api.serch_users(self.params, offset)
                            print(users)
                            self.forms[event.user_id] = users
                            offset += 50
                        user = users.pop()
                        from_bd = self.get_user(event, user)
                        self.forms[event.user_id] = users
                    self.write_to_bd(event, user)
                    photos_user = self.api.get_photos(user['id'])
                    attachment = ''
                    for num, photo in enumerate(photos_user):
                        attachment += f'photo{photo["owner_id"]}_{photo["id"]}'
                        if num == 2:
                            break
                    self.message_send(event.user_id,
                                      f'Встречайте {user["name"]}',
                                      attachment=attachment
                                      )
                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')
                else:
                    self.message_send(event.user_id, 'команда не опознана')


if __name__ == '__main__':
    bot = BotInterface(comunity_token, acces_token)
    bot.event_handler()

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from conf import comunity_token, acces_token
from Back import VkTools

from BD import Viewed, engine
from sqlalchemy.orm import Session



class BotInterface():

    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.params = None

    def message_send(self, user_id, message, attachment=None):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': message,
                               'attachment': attachment,
                               'random_id': get_random_id()
                               }
                              )

    def event_handler(self):
        longpoll = VkLongPoll(self.interface)
        offset = 0
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()

                if command == 'привет':
                    self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'здравствуй {self.params["name"]}')
                elif command == 'поиск':
                    users = self.api.serch_users(self.params,offset)
                    user = users.pop()
                    with Session(engine) as session:
                        from_bd = session.query(Viewed).filter(Viewed.worksheet_id == user['id'], Viewed.profile_id == event.user_id).all()
                    if len(from_bd) != 0:
                        self.message_send(event.user_id, f'Повторите команду')
                        offset +=10
                    else:
                        with Session(engine) as session:
                            to_bd = Viewed(profile_id=event.user_id, worksheet_id=user['id'])
                            session.add(to_bd)
                            session.commit()
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

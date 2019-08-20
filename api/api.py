import json
import argparse
import urllib.request


def send_request(request):
    with urllib.request.urlopen(request) as u:
        result = json.loads(u.read())
    return result


class UserData:
    def __init__(self, data_dict):
        self.first_name = data_dict['first_name']
        self.last_name = data_dict['last_name']
        self.id = data_dict['id']
        self.domain = data_dict['domain']

    def __str__(self):
        return f'{self.first_name} {self.last_name}, vk.com/{self.domain}'


class VkApiTools:
    @staticmethod
    def get_request(token, method_name, params):
        params_line = '&'.join([f'{name}={value}' for name, value in params])
        return f'http://api.vk.com/method/{method_name}?{params_line}&access_token={token}'

    @staticmethod
    def parse_friends_response(response):
        friends_list = []
        for friend in response:
            friends_list.append(UserData(friend))
        return friends_list



class VkApi:
    def __init__(self, vk_id, access_token):
        self.id = vk_id
        self.access_token = access_token
        self.commands = {
            'friends': self.get_friends,
            'user_name': self.get_id,
            'albums': self.get_albums_names
        }

    def execute(self, cmd):
        cmd_name, cmd_arg = cmd
        self.commands[cmd_name](cmd_arg)

    def get_friends(self, user_id):
        method_name = 'friends.get'
        fields = ['domain']
        params = [
            ('user_id', user_id),
            ('v', 5.95),
            ('order', 'name'),
            ('fields', ','.join(fields))
        ]

        request = VkApiTools.get_request(self.access_token, method_name, params)
        json_result = send_request(request)
        friends_list = VkApiTools.parse_friends_response(json_result['response']['items'])

        print(f'\nFriends of user vk.com/id{user_id}\n')
        for friend in friends_list:
            print(friend)

    def get_id(self, user_name):
        method_name = 'users.get'
        params = [
            ('user_ids', user_name),
            ('v', 5.95)
        ]
        request = VkApiTools.get_request(self.access_token, method_name, params)
        json_result = send_request(request)
        vk_id = json_result['response'][0]['id']
        print(f'\nID of user vk.com/{user_name}\n')
        print(vk_id)

    def get_albums_names(self, user_id):
        method_name = 'photos.getAlbums'
        params = [
            ('owner_id', user_id),
            ('v', 5.95)
        ]
        request = VkApiTools.get_request(self.access_token, method_name, params)
        json_result = send_request(request)
        items = json_result['response']['items']
        album_names = [item['title'] for item in items]
        print(f'\nAlbums of user vk.com/id{user_id}\n')
        print('\n'.join(album_names))

def get_parser():
    parser = argparse.ArgumentParser(description='VK api')
    parser.add_argument('-f', '--friends', type=int, help='get friends of user with id')
    parser.add_argument('-u', '--user_name', type=str, help='get id of user with name')
    parser.add_argument('-a', '--albums', type=int, help='get albums names of user with id')

    return parser.parse_args()


def main():
    parser = get_parser()

    config_file = 'config.json'

    with open(config_file, 'rt') as f:
        config = json.load(f)

    vk_id = config['id']
    access_token = config['token']

    commands = []
    if parser.friends:
        commands.append(('friends', parser.friends))
    if parser.user_name:
        commands.append(('user_name', parser.user_name))
    if parser.albums:
        commands.append(('albums', parser.albums))

    api = VkApi(vk_id, access_token)

    for cmd in commands:
        api.execute(cmd)



if __name__ == '__main__':
    main()

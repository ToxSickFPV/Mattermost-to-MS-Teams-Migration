import asyncio
import traceback
from datetime import datetime
import re

import pytz
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.user import User
from utils.api import API, Role
from utils.data import Data
from utils.constants import EMOJI_MAP, ACCEPTABLE_IMAGE_FILE_ENDINGS, IGNORED_FILE_ENDINGS
from teams import TEAMS
import logging

data = Data()
data.init()
api = API()
api.init()

users: dict[str, User] = {}

logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('files.log')
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def convert_to_user_dict(user_list: list[User]) -> dict[str, User]:
    dictionary: dict[str, User] = {}
    for user in user_list:
        dictionary[user.user_principal_name.lower()] = user
    return dictionary


def get_file_paths(fileinfo_ids: str) -> list[str]:
    global data
    return_list: list[str] = []
    id_list = str(fileinfo_ids).removeprefix('[').removesuffix(']').replace('"', '').split(',')
    for fileinfo_id in id_list:
        return_list.append(data.get_fileinfo(fileinfo_id)['path'])
    return return_list


def replace_emojis(text):
    for github_emoji, teams_emoji in EMOJI_MAP.items():
        text = text.replace(github_emoji, teams_emoji)

    return text


def replace_titles(text: str) -> str:
    regex = '^(.*?)\n---------------------------\n(.*)$'
    result = re.sub(regex, r'<b>\1</b>\n\2', text, flags=re.DOTALL)
    return result


def replace_line_breaks(text: str) -> str:
    return text.replace('\n', '<br>')


def sanitize_text(text: str) -> str:
    return replace_line_breaks(replace_titles(replace_emojis(text)))


def get_sanitized_paths(file_paths: list[str], team_channel_name: str) -> tuple[list[str], str]:
    global logger
    accepted_paths: list[str] = []
    message_addition = ''
    for path in file_paths:
        ending = path.split('.')[-1].lower()
        if ending in IGNORED_FILE_ENDINGS: continue
        if ending in ACCEPTABLE_IMAGE_FILE_ENDINGS:
            accepted_paths.append(path)
            continue
        logger.info('ADD FILE: ' + path.replace("/", "\\") + f' TO CHANNEL {team_channel_name}')
        message_addition += f'<br><br>Attached file in: /Mattermost/{path.split("/")[-1]}\n\n'

    return accepted_paths, message_addition


async def migrate_channels_for_team(team_id: str, team_name: str, channels: dict[str, str], alias_user_mail: str) -> tuple[str, int]:
    post_count = 0
    channel_info_on_fail = ''

    try:
        for channel, channel_original_name in channels.items():

            if channel == 'General':
                channel_id = await api.get_general_channel(team_id)
            else:
                channel_id = await api.post_channel(team_id, channel)

            channel_info_on_fail = f'failed on channel "{channel}", id: {channel_id}'
            logger.info(f'channel "{channel}", id: {channel_id}:')

            print(f'channel id: {channel_id}')
            channel_posts = data.get_channel_posts(channel_original_name)
            print(f'has {len(channel_posts)} posts')

            for index, post in channel_posts.iterrows():
                post_count += 1
                if post_count < 0: continue
                message = sanitize_text(str(post['message']))
                if post['email'].lower() in users:
                    user = users[post['email'].lower()]
                else:
                    user = users[alias_user_mail]
                    message = f'Original post from user {post["username"]} ({post["email"]})<br><br>' + message

                posting_date = datetime.fromtimestamp(int(post['createat'] / 1000)).replace(tzinfo=pytz.UTC)
                file_paths: list[str] = []
                if post['fileids'] != '[]':
                    file_paths = get_file_paths(post['fileids'])
                    file_paths, message_addition = get_sanitized_paths(file_paths, f'{team_name}::{channel}')
                    message += message_addition
                if not message: continue
                print(f'{post_count}: ', end='')
                try:
                    if len(file_paths) == 0:
                        await api.post_message(team_id, channel_id, posting_date, user, message)
                    else:
                        await api.post_image_message(team_id, channel_id, posting_date, user, message, file_paths)
                except ODataError as e:
                    print(e.__dict__)
                    if e.response_status_code == 409 or e.response_status_code == 400:
                        print(f'ERROR: {e.error.inner_error.additional_data}')
                    else:
                        raise e

        return '', 0

    except:
        return channel_info_on_fail, post_count


async def assign_users_to_team(team_id: str, channels: dict[str, str], admin_id: str):
    try:
        members = data.get_channel_members(list(channels.values()))
        for member in members:
            if member.lower() in users:
                user = users[member.lower()]
                await api.assign_user_to_team(user.id, team_id, Role.Member)
        await api.assign_user_to_team(admin_id, team_id, Role.Owner)
    except Exception as e:
        traceback.print_exc()


async def main():
    global data
    global api
    global users
    global logger

    admin_id = input('User ID of Administrator >>> ')
    alias_user_mail = input('Alias user mail (if a Mattermost user is not found in MS Teams) >>> ')

    start_time = datetime.now()
    users = convert_to_user_dict((await api.get_users()).value)

    post_count = 0
    team_info_on_fail = ''
    channel_info_on_fail = ''

    try:
        for team, channels in TEAMS.items():
            team_id = await api.post_team(team)
            team_info_on_fail = f'failed on team "{team}", id: {team_id}'
            channel_info_on_fail = ''
            print('team id:', team_id)
            logger.info(f'team "{team}", id: {team_id}:')

            channel_info_on_fail, post_count = await migrate_channels_for_team(team_id, team, channels, alias_user_mail)
            await api.end_team_migration(team_id)
            await assign_users_to_team(team_id, channels, admin_id)

    except Exception as e:
        traceback.print_exc()
        print(team_info_on_fail)
        print(channel_info_on_fail)
        print(f'POST COUNT: {post_count}')

    print('Total run time:', datetime.now() - start_time)


if __name__ == '__main__':
    asyncio.run(main())

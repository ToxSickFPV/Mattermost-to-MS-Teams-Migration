import traceback

from utils.singleton import Singleton
import pandas as pd
from pandas import DataFrame, Series


class Data(Singleton):

    __users: DataFrame
    __channels: DataFrame
    __posts_unmerged: DataFrame
    __file_infos: DataFrame
    __posts: DataFrame

    def __init__(self):
        pass

    def init(self):
        try:
            self.__users = pd.read_csv('../mm_data/export_users.csv')
            self.__channels = pd.read_csv('../mm_data/export_channels.csv')
            self.__posts_unmerged = pd.read_csv('../mm_data/export_posts.csv')
            self.__file_infos = pd.read_csv('../mm_data/export_fileinfo.csv')
        except Exception as e:
            print('Data import FAILED')
            traceback.print_exc()
            exit(1)

        posts_channels_df = pd.merge(self.__posts_unmerged, self.__channels, left_on='channelid', right_on='id', how='left',
                                     suffixes=('', '_channel'))
        self.__posts = pd.merge(posts_channels_df, self.__users, left_on='userid', right_on='id', how='left',
                                suffixes=('', '_user'))
        self.__init_filter_and_sort()

    def get_channel_posts(self, channel_names: str) -> DataFrame:
        names = channel_names.split(' && ')
        if len(names) == 1:
            posts = self.__posts[self.__posts['displayname'] == names[0]]
        elif len(names) == 2:
            posts = self.__posts[(self.__posts['displayname'] == names[0]) | (self.__posts['displayname'] == names[1])]
        else:
            raise ValueError('Invalid channel names. Channel names must be single (without &&) or merge (with exactly one &&)')
        if posts.empty:
            raise Exception('Channel with name %s does not exist' % channel_names)
        return posts

    def get_user(self, user_id: str) -> Series:
        user = self.__users[self.__users['id'] == user_id]
        if user.size != 1:
            raise Exception('User with id %s does not exist' % user_id)
        return user.iloc[0]

    def get_fileinfo(self, fileinfo_id: str) -> Series:
        info = self.__file_infos[self.__file_infos['id'] == fileinfo_id]
        if len(info) != 1:
            raise Exception('File info with id %s does not exist' % fileinfo_id)
        return info.iloc[0]

    def get_channel_members(self, channel_names: list[str]) -> DataFrame:
        for channel_name in channel_names:
            split = channel_name.split(' && ')
            if len(split) == 2:
                channel_names.remove(channel_name)
                channel_names.append(split[0])
                channel_names.append(split[1])
        print(channel_names)
        channel_posts = self.__posts[self.__posts['displayname'].isin(channel_names)]
        return channel_posts['email'].unique()

    def __init_filter_and_sort(self):
        filtered_df = self.__posts[self.__posts['displayname'].notna()]  # filter on no private chats
        filtered_df = filtered_df[filtered_df['type'].isna()]
        filtered_df = filtered_df[filtered_df['deleteat'] == 0]  # filter on not deleted
        filtered_df = filtered_df[['createat', 'message', 'filenames', 'fileids', 'displayname', 'name', 'username', 'email', 'firstname', 'lastname', 'roles']]
        self.__posts = filtered_df.sort_values(by='createat', ascending=True)  # sort by creation date

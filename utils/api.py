import base64
import time
from datetime import datetime
from enum import StrEnum

from msgraph.generated.models.drive_item import DriveItem
from msgraph.generated.models.folder import Folder

from utils.singleton import Singleton

from PIL import Image

from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.aad_user_conversation_member import AadUserConversationMember
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.channel_collection_response import ChannelCollectionResponse
from msgraph.generated.models.channel_membership_type import ChannelMembershipType
from msgraph.generated.models.chat_message_from_identity_set import ChatMessageFromIdentitySet
from msgraph.generated.models.chat_message_hosted_content import ChatMessageHostedContent
from msgraph.generated.models.identity import Identity
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.team import Team
from msgraph.generated.models.channel import Channel
from msgraph.generated.models.chat_message import ChatMessage
from msgraph.generated.models.user import User
from msgraph.generated.models.user_collection_response import UserCollectionResponse

IMAGES_BASE_PATH = '../mm_data/data/'

class Role(StrEnum):
    Owner = "owner",
    Member = "member",
    Guest = "guest"


class API(Singleton):

    __client: GraphServiceClient

    def init(self):
        try:
            t_id = input("Graph Service Client: Tenant ID >>> ")
            c_id = input("Graph Service Client: Client ID >>> ")
            c_secret = input("Graph Service Client: Client Secret >>> ")

            credential = ClientSecretCredential(
                tenant_id=t_id,
                client_id=c_id,
                client_secret=c_secret
            )
            scopes = ['https://graph.microsoft.com/.default']
            self.__client = GraphServiceClient(credentials=credential, scopes=scopes)
        except:
            print('Creation of Graph Service Client failed')
            exit(1)

    async def get_users(self) -> UserCollectionResponse:
        self.__check_client()
        return await self.__client.users.get()

    async def post_team(self, name: str, description: str = None):
        self.__check_client()
        print('Creating team', name)
        if not description: description = name
        request_body = Team(
            display_name=name,
            description=description,
            created_date_time=datetime.fromtimestamp(1577833200),
            additional_data={
                "template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
                "@microsoft.graph.teamCreationMode": "migration"
            }
        )

        await self.__client.teams.post(request_body)
        time.sleep(10)
        result = await self.get_team_by_name(name)
        return result.id

    async def post_channel(self, team_id: str, name: str, description: str = None) -> str:
        self.__check_client()
        print('Creating channel', name)
        if not description: description = name
        request_body = Channel(
            display_name=name,
            description=description,
            membership_type=ChannelMembershipType.Standard,
            created_date_time=datetime.fromtimestamp(1577833230),
            additional_data={
                "@microsoft.graph.channelCreationMode": "migration"
            }
        )

        result = await self.__client.teams.by_team_id(team_id).channels.post(request_body)
        return result.id

    async def post_message(self, team_id: str, channel_id: str, creation_date_time: datetime, user: User, message: str) -> str:
        self.__check_client()
        print('Posting message:', message)
        request_body = ChatMessage(
            created_date_time=creation_date_time,
            from_=ChatMessageFromIdentitySet(
                user=Identity(
                    id=user.id,
                    display_name=user.display_name,
                    additional_data={
                            "userIdentityType": "aadUser",
                    }
                )
            ),
            body=ItemBody(
                content_type=BodyType.Html,
                content=message,
            )
        )

        result = await (self.__client
                        .teams.by_team_id(team_id)
                        .channels.by_channel_id(channel_id)
                        .messages
                        .post(request_body))
        return result.id

    async def post_image_message(self, team_id: str, channel_id: str, creation_date_time: datetime, user: User, message: str, image_paths: list[str]):
        self.__check_client()
        print('Posting image message', message)
        final_message = message
        temp_id = 1
        for path in image_paths:
            img = Image.open(IMAGES_BASE_PATH + path)
            width, height = img.size
            img.close()
            final_message += ('<div><div>\n<div><span><img height="' + str(height) + '" src="../hostedContents/' + str(temp_id)
                              + '/$value" width="' + str(width) + '" style="vertical-align:bottom; width:' + str(width)
                              + 'px; height:' + str(height)
                              + 'px"></span>\n\n</div>\n\n\n</div>\n</div>')
            temp_id += 1

        request_body = ChatMessage(
            created_date_time=creation_date_time,
            from_=ChatMessageFromIdentitySet(
                user=Identity(
                    id=user.id,
                    display_name=user.display_name,
                    additional_data={
                        "user_identity_type": "aadUser",
                    }
                )
            ),
            body=ItemBody(
                content_type=BodyType.Html,
                content=final_message,
            ),
            hosted_contents=self.__get_hosted_content(image_paths),
        )

        return await self.__client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).messages.post(request_body)

    async def end_team_migration(self, team_id: str):
        self.__check_client()
        print('Ending team migration for team with id', team_id)
        channels = await self.__get_all_channels(team_id)
        for channel in channels.value:
            await self.__end_channel_migration(team_id, channel.id)

        await self.__client.teams.by_team_id(team_id).complete_migration.post()

    async def assign_user_to_team(self, user_id: str, team_id: str, role: Role) -> bool:
        self.__check_client()
        print('Assigning user %s to team %s with role %s' % (user_id, team_id, role.value))
        request_body = AadUserConversationMember(
            odata_type="#microsoft.graph.aadUserConversationMember",
            roles=[role.value],
            additional_data={
                "user@odata.bind": "https://graph.microsoft.com/v1.0/users('" + user_id + "')",
            }
        )

        result = await self.__client.teams.by_team_id(team_id).members.post(request_body)
        return True if result else False

    async def __create_migration_folder(self, team_id: str, channel_id: str) -> tuple[str, str, str]:
        get_response = await self.__client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).files_folder.get()
        drive_id = get_response.parent_reference.drive_id
        parent_id = get_response.id

        drive_item: DriveItem = DriveItem(
            name='Mattermost',
            folder=Folder(),
            additional_data={
                "@microsoft.graph.conflictBehavior": "rename",
            }
        )
        post_response = await self.__client.drives.by_drive_id(drive_id).items.by_drive_item_id(parent_id).children.post(drive_item)
        mattermost_folder_id = post_response.id

        return drive_id, parent_id, mattermost_folder_id

    async def __get_all_channels(self, team_id: str) -> ChannelCollectionResponse:
        self.__check_client()
        return await self.__client.teams.by_team_id(team_id).all_channels.get()

    async def get_general_channel(self, team_id: str) -> str:
        self.__check_client()
        all_channels = await self.__get_all_channels(team_id)
        for channel in all_channels.value:
            if channel.display_name == 'General': return channel.id

    async def __end_channel_migration(self, team_id: str, channel_id: str):
        self.__check_client()
        await self.__client.teams.by_team_id(team_id).channels.by_channel_id(channel_id).complete_migration.post()

    def __get_hosted_content(self, paths: list[str]) -> list[ChatMessageHostedContent]:
        return_list: list[ChatMessageHostedContent] = []
        temp_id = 1
        for path in paths:
            with open(IMAGES_BASE_PATH + path, 'rb') as image_file:
                ending = path.split('.')[-1].lower()
                return_list.append(ChatMessageHostedContent(
                    content_bytes=base64.urlsafe_b64decode(base64.b64encode(image_file.read()).decode('utf-8')),
                    content_type=f"image/{ending}",
                    additional_data={
                        "@microsoft.graph.temporaryId": str(temp_id),
                    }
                ))
                temp_id += 1

        return return_list

    async def get_team_by_name(self, name: str, retries: int = 0) -> Team:
        self.__check_client()
        teams = await self.__client.teams.get()
        for team in teams.value:
            if team.display_name == name:
                return team
        if retries < 6:
            print('Failed to get team id: retrying')
            time.sleep(5)
            return await self.get_team_by_name(name, retries + 1)
        return None

    def __check_client(self):
        if not self.__client:
            raise Exception('API Client not initialized')

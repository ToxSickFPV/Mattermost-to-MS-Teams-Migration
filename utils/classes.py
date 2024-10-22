from dataclasses import dataclass


@dataclass
class Message:
    contentType: str
    content: str


@dataclass
class FromUser:
    id: str
    displayName: str
    userIdentityType: str


@dataclass
class FromObject:
    user: FromUser


@dataclass
class MessagePost:
    createdDateTime: str
    fromType: FromObject
    body: Message


@dataclass
class HostedContent:
    ms_graph_temporaryId: str
    contentBytes: str
    contentType: str


@dataclass
class ImageMessagePost:
    createdDateTime: str
    fromType: FromObject
    body: Message
    hostedContents: list[HostedContent]


@dataclass
class User:
    businessPhones: list[str]
    displayName: str
    givenName: str
    jobTitle: str
    mail: str
    mobilePhone: str
    officeLocation: str
    preferredLanguage: str
    surname: str
    userPrincipalName: str
    id: str
    
"""
Definition of teams and team channels to create by the script.
The mapping of the MS Teams channel to the Mattermost Channel is happening here.

Example:

'Team 1': {
    'Channel 1': 'Mattermost Channel Name 1',
    'Channel 2': 'Mattermost Channel Name 2',
    'Channel 3': 'Mattermost Channel Name 3',
    ...
},
'Team 2': {
    'Channel 1': 'Mattermost Channel Name 1',
    'Channel 2': 'Mattermost Channel Name 2',
    'Channel 3': 'Mattermost Channel Name 3',
    ...
},
...

The 'General' channel is automatically created for every team. If it is not mentioned in this definition it will
be deleted. if it is mentioned the given Mattermost channel will be migrated into it.

"""

TEAMS = {
    'Team 1': {
        'General': 'Mattermost Channel Name 1',     # General channel will be used in this team
        'Channel 2': 'Mattermost Channel Name 2',
        'Channel 3': 'Mattermost Channel Name 3'
    },
    'Team 2': {
        'Channel 1': 'Mattermost Channel Name 1',   # General channel deleted in this team
        'Channel 2': 'Mattermost Channel Name 2',
        'Channel 3': 'Mattermost Channel Name 3'
    }
}
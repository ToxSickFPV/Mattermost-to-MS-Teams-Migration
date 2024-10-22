# Mattermost to MS Teams Migration

> **_NOTE:_**  The purpose of this migration script is to demonstrate how a Mattermost - MS Teams migration could be done.
> It was coded quick and dirty to function for my use case.
> Please do some testing before actually using it, or just use it as reference.

This script will migrate Mattermost chat channels to MS Teams. The Migration converts
- Mattermost channel &rarr; MS Teams channel
- Mattermost channel message &rarr; MS Teams channel post
- Mattermost channel message with image &rarr; MS Teams channel post with image
- Mattermost channel message with file &rarr; MS Teams channel post (with hint to file) - Shared Team file

## Setup

### Export Mattermost
1. Export the following tables from Mattermost as CSV-Files and place them in the `mm_data` folder of this project:
   - channels &rarr; export_channels.csv
   - fileinfo &rarr; export_fileinfo.csv
   - posts &rarr; export_posts.csv
   - users &rarr; export_users.csv
2. Export the `data` folder from Mattermost and place it in the `mm_data` folder of this project (folder with all the images and files sent over Mattermost)

### Enter Graph API Credentials
When starting the script you get prompted for the tenant id / client id / client secret for the Graph API.

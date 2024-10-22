ACCEPTABLE_IMAGE_FILE_ENDINGS = {'jpg', 'jpeg', 'png'}
IGNORED_FILE_ENDINGS = {'mp4', 'avi', 'mkv', 'mpg', 'gif', 'bmp', 'tiff', 'webp'}


EMOJI_MAP = {}
with open('../mm_data/emojis.txt', 'r', encoding='utf-8') as file:
    for line in file:
        split = line.strip().split(' ')
        EMOJI_MAP[split[1]] = split[0]

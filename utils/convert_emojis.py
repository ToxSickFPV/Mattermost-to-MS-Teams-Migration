

EMOJIS = {}
print('EMOJIS = {')
with open('../mm_data/emojis.txt', 'r', encoding='utf-8') as file:
    for line in file:
        split = line.strip().split(' ')
        EMOJIS[split[1]] = split[0]
        print(f"'{split[1]}': '{split[0]}'")
print('}')
print(EMOJIS)

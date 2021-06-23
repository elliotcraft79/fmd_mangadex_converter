import sqlite3
import re
import csv

con = sqlite3.connect('favorites.db')
cur = con.cursor()

conversion_con = sqlite3.connect('conversion.db')
conversion_cur = conversion_con.cursor()

cur.execute("SELECT * FROM favorites where moduleid = 'd07c9c2425764da8ba056505f57cf40c'")

mangadex_favorites = cur.fetchall()
already_converted = []

for favorite in mangadex_favorites:
    title_match = re.match(r"d07c9c2425764da8ba056505f57cf40c\/title\/(?P<id>\d+)", favorite[0])
    if title_match == None:
        continue
    title_id = title_match.group('id')
    if title_id in already_converted:
        continue
    conversion_cur.execute(f"SELECT * FROM manga_map WHERE legacy_id = '{title_id}'")
    title_mapping = conversion_cur.fetchone()
    if title_mapping:
        new_favorite_link = '/title/' + title_mapping[1]
        new_favorite_id = 'd07c9c2425764da8ba056505f57cf40c' + new_favorite_link
    else:
        continue
    print(f"{title_id} - {new_favorite_id}")
    new_chapters = []
    for chapter in favorite[8].strip().split('\n'):
        conversion_cur.execute(f"SELECT * FROM chapter_map WHERE legacy_id = '{chapter.replace('/chapter/', '')}'")
        chapter_mapping = conversion_cur.fetchone()
        if chapter_mapping:
            new_chapters.append(f"/{chapter_mapping[1]}")
        else:
            continue
    new_chapters = '\n'.join(new_chapters) + '\n'
    cur.execute(f"UPDATE favorites SET id = '{new_favorite_id}', link = '{new_favorite_link}', downloadedchapterlist = '{new_chapters}' WHERE id = '{favorite[0]}'")
    con.commit()
    already_converted.append(title_id)

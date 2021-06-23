import sqlite3
import re

con = sqlite3.connect('downloads.db')
cur = con.cursor()

conversion_con = sqlite3.connect('conversion.db')
conversion_cur = conversion_con.cursor()

cur.execute("SELECT * FROM downloads WHERE moduleid = 'd07c9c2425764da8ba056505f57cf40c'")

downloads = cur.fetchall()
already_converted = []

for download in downloads:
    if re.match(r"\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b", download[8]):
        print(f"{download[8]} is already a UUID")
        continue
    title_match = re.match(r"\/title\/(?P<id>\d+)", download[8])
    if title_match == None:
        print('no title match')
        continue
    title_id = title_match.group('id')
    if title_id in already_converted:
        continue
    conversion_cur.execute(f"SELECT * FROM manga_map WHERE legacy_id = '{title_id}'")
    title_mapping = conversion_cur.fetchone()
    if title_mapping:
        new_title_id = '/title/' + title_mapping[1]
    else:
        continue
    print(f"{title_id} - {new_title_id}")
    new_chapters = []
    for chapter in download[15].strip().split('\n'):
        conversion_cur.execute(f"SELECT * FROM chapter_map WHERE legacy_id = '{chapter.replace('/chapter/', '')}'")
        chapter_mapping = conversion_cur.fetchone()
        if chapter_mapping:
            new_chapters.append(f"/{chapter_mapping[1]}")
        else:
            continue
    new_chapters = '\n'.join(new_chapters) + '\n'
    cur.execute(f"UPDATE downloads SET link = '{new_title_id}', chapterslinks = '{new_chapters}' WHERE id = '{download[0]}'")
    con.commit()
    already_converted.append(title_id)

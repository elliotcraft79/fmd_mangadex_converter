import sqlite3
import re
import sys
import os
import shutil

DB_list = ['favorites.db', 'downloadedchapters.db', 'downloads.db', 'd07c9c2425764da8ba056505f57cf40c.db']

def build_DB_path():
    possiblity_path = ['.', 'userdata', 'data', '..', os.path.join('..', 'userdata'), os.path.join('..', 'data')]
    DB_path = []
    for DB_ in DB_list:
        for path_ in possiblity_path:
            if os.path.lexists(os.path.join(os.path.abspath(path_), DB_)):
                DB_path += [os.path.join(os.path.abspath(path_), DB_)]
    return DB_path

def DB_convert(DB_, conversion_cur):
    if os.path.basename(DB_) == 'd07c9c2425764da8ba056505f57cf40c.db':
        skip_convert = input('do you want to skip converting mangadex manga database (it will take longtime)?>>')
        if str(skip_convert).lower() == 'n':
            pass
        elif str(skip_convert).lower() == 'no':
            pass
        else:
            return
        
    con = sqlite3.connect(DB_)

    sql_table_name = {'favorites.db': ['favorites', 'id', 0, 8],
                      'downloadedchapters.db': ['downloadedchapters', 'id', 0, 1],
                      'downloads.db': ['downloads', 'moduleid', 8, 15],
                      'd07c9c2425764da8ba056505f57cf40c.db': ['masterlist', '', 0, 0]
                      }[os.path.basename(DB_)]
    
    #cur = con.execute(f"SELECT * FROM '{sql_table_name[0]}'")
    #print([column_des[0] for column_des in cur.description])
    
    cur = con.cursor()

    

    #print(f"SELECT * FROM '{sql_table_name[0]}'" + ("" if sql_table_name[1] == "" else f"where {sql_table_name[1]} LIKE 'd07c9c2425764da8ba056505f57cf40c%'"))
    cur.execute(f"SELECT * FROM '{sql_table_name[0]}'" + ("" if sql_table_name[1] == "" else f"where {sql_table_name[1]} LIKE 'd07c9c2425764da8ba056505f57cf40c%'"))

    mangadex_titles = cur.fetchall()
    already_converted = []

    #print(DB_)
    #print(mangadex_titles)
    
    for title in mangadex_titles:
        #print(len(title))
        if re.match(r"^(?:d07c9c2425764da8ba056505f57cf40c)?\/title\/([0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12})", title[sql_table_name[2]]):
            print(f"{title[sql_table_name[2]]} is already a UUID")
            continue
        title_match = re.match(r"^(?:d07c9c2425764da8ba056505f57cf40c)?\/title\/(?P<id>\d+)", title[sql_table_name[2]])
        if title_match == None:
            continue
        title_id = title_match.group('id')
        if title_id in already_converted:
            continue
        conversion_cur.execute(f"SELECT * FROM manga_map WHERE legacy_id = '{title_id}'")
        title_mapping = conversion_cur.fetchone()
        if title_mapping:
            new_title_link = '/title/' + title_mapping[1]
            new_title_moudle_link = 'd07c9c2425764da8ba056505f57cf40c' + new_title_link
        else:
            continue
        print(f"{title_id} - {new_title_moudle_link}")
        new_chapters = []
        for chapter in title[sql_table_name[3]].strip().split('\n'):
            conversion_cur.execute(f"SELECT * FROM chapter_map WHERE legacy_id = '{chapter.replace('/chapter/', '')}'")
            chapter_mapping = conversion_cur.fetchone()
            if chapter_mapping:
                new_chapters.append(f"/{chapter_mapping[1]}")
            else:
                continue
        new_chapters = '\n'.join(new_chapters) + '\n'
        update_sql_command = {'favorites.db': f"UPDATE favorites SET id = '{new_title_moudle_link}', link = '{new_title_link}', downloadedchapterlist = '{new_chapters}' WHERE id = '{title[0]}'",
                              'downloadedchapters.db': f"UPDATE downloadedchapters SET id = '{new_title_moudle_link}', chapters = '{new_chapters}' WHERE id = '{title[0]}'",
                              'downloads.db': f"UPDATE downloads SET link = '{new_title_link}', chapterslinks = '{new_chapters}' WHERE id = '{title[0]}'",
                              'd07c9c2425764da8ba056505f57cf40c.db': f"UPDATE masterlist SET link = '{new_title_link}' WHERE link = '{title[0]}'"
                              }[os.path.basename(DB_)]
        cur.execute(update_sql_command)
        con.commit()
        already_converted.append(title_id)

def converter():
    DB_path = build_DB_path()
    conversion_con = sqlite3.connect('conversion.db')
    conversion_cur = conversion_con.cursor()
    for DB_ in DB_path:
        #make copy befoer start
        shutil.copy2(DB_, os.path.splitext(DB_)[0]+'.bak')

        DB_convert(DB_, conversion_cur)
        
if __name__ == '__main__':
    converter()

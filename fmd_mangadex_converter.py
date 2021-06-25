import sqlite3
import re
import sys
import os
import shutil

DB_LIST = [
    "favorites.db",
    "downloadedchapters.db",
    "downloads.db",
    "d07c9c2425764da8ba056505f57cf40c.db",
]


def build_db_path():
    possible_paths = [
        ".",
        "userdata",
        "data",
        "..",
        os.path.join("..", "userdata"),
        os.path.join("..", "data"),
    ]
    db_path = []
    for db in DB_LIST:
        for path in possible_paths:
            if os.path.lexists(os.path.join(os.path.abspath(path), db)):
                db_path.append(os.path.join(os.path.abspath(path), db))
    return db_path


def convert_db(db_path, conversion_cur):
    print(db_path)
    db_name = os.path.basename(db_path)
    if db_name == "d07c9c2425764da8ba056505f57cf40c.db":
        skip_convert = input(
            "Do you want to skip converting the mangadex manga database (it will take a while to convert)?\n>> "
        )
        if str(skip_convert).lower().startswith('n'):
            pass
        else:
            return

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    sql_column_names = {
        "favorites.db": {
            "table": "favorites",
            "id_column": "id",
            "link_column": "id",
            "chapters_column": "downloadedchapterlist",
        },
        "downloadedchapters.db": {
            "table": "downloadedchapters",
            "id_column": "id",
            "link_column": "id",
            "chapters_column": "chapters",
        },
        "downloads.db": {
            "table": "downloads",
            "id_column": "moduleid",
            "link_column": "link",
            "chapters_column": "chapterslinks",
        },
        "d07c9c2425764da8ba056505f57cf40c.db": {
            "table": "masterlist",
            "id_column": "",
            "link_column": "link",
            "chapters_column": "",
        },
    }[db_name]
    cur = con.cursor()

    id_sql = (
        f"WHERE {sql_column_names['id_column']} LIKE 'd07c9c2425764da8ba056505f57cf40c%'"
        if sql_column_names["id_column"] != ""
        else ""
    )
    cur.execute(f"SELECT * FROM {sql_column_names['table']} {id_sql}")

    mangadex_titles = cur.fetchall()
    already_converted = []

    for title in mangadex_titles:
        if re.match(
            r"^(?:d07c9c2425764da8ba056505f57cf40c)?\/title\/([0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12})",
            title[sql_column_names["link_column"]],
        ):
            print(f"{title[sql_column_names['link_column']]} is already a UUID")
            continue
        title_match = re.match(
            r"^(?:d07c9c2425764da8ba056505f57cf40c)?\/title\/(?P<id>\d+)",
            title[sql_column_names["link_column"]],
        )
        if title_match == None:
            continue
        title_id = title_match.group("id")
        if title_id in already_converted:
            continue
        title_update_info = {"old_id": title[0]}
        conversion_cur.execute("SELECT * FROM manga_map WHERE legacy_id = ?", (title_id,))
        title_mapping = conversion_cur.fetchone()
        if title_mapping:
            title_update_info["new_link"] = "/title/" + title_mapping["new_id"]
            title_update_info["new_id"] = (
                "d07c9c2425764da8ba056505f57cf40c" + title_update_info["new_link"]
            )
        else:
            continue
        print(f"{title_id} -> {title_mapping['new_id']}")
        if sql_column_names["chapters_column"] != "":
            new_chapters = []
            for chapter in title[sql_column_names["chapters_column"]].strip().split("\n"):
                conversion_cur.execute(
                    "SELECT * FROM chapter_map WHERE legacy_id = ?",
                    (chapter.replace("/chapter/", ""),),
                )
                chapter_mapping = conversion_cur.fetchone()
                if chapter_mapping:
                    new_chapters.append(f"/{chapter_mapping['new_id']}")
                else:
                    continue
            title_update_info["new_chapters"] = "\n".join(new_chapters) + "\n"
        update_sql_command = {
            "favorites.db": "UPDATE favorites SET id = :new_id, link = :new_link, downloadedchapterlist = :new_chapters WHERE id = :old_id",
            "downloadedchapters.db": "UPDATE downloadedchapters SET id = :new_id, chapters = :new_chapters WHERE id = :old_id",
            "downloads.db": "UPDATE downloads SET link = :new_link, chapterslinks = :new_chapters WHERE id = :old_id",
            "d07c9c2425764da8ba056505f57cf40c.db": "UPDATE masterlist SET link = :new_link WHERE link = :old_id",
        }[db_name]
        cur.execute(update_sql_command, title_update_info)
        con.commit()
        already_converted.append(title_id)


def converter():
    db_path = build_db_path()
    conversion_con = sqlite3.connect("conversion.db")
    conversion_cur = conversion_con.cursor()
    conversion_cur.row_factory = sqlite3.Row
    for db in db_path:
        # make a backup before starting
        shutil.copy2(db, os.path.splitext(db)[0] + ".bak")

        convert_db(db, conversion_cur)


if __name__ == "__main__":
    converter()

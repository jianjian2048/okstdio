import sqlite3


class AppDB:

    def __init__(self) -> None:
        self.conn = sqlite3.connect("example/assets/app.db")
        self.cursor = self.conn.cursor()
        self.create_all_table()

    def create_all_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hero (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hero_name TEXT NOT NULL UNIQUE,
                level INTEGER CHECK(level BETWEEN 0 AND 50)
            )
            """
        )

    def create_hero(self, hero_name: str):
        self.cursor.execute(
            "INSERT INTO hero(hero_name, level) VALUES (?, ?)", (hero_name, 0)
        )
        self.conn.commit()

    def get_hero_list(self):
        self.cursor.execute("SELECT id, hero_name, level FROM hero")
        return self.cursor.fetchall()

    def get_hero(self, hero_name: str):
        self.cursor.execute(
            "SELECT id, hero_name, level FROM hero WHERE hero_name = ?", (hero_name,)
        )
        hero = self.cursor.fetchone()
        if hero:
            return hero
        return None

    def hero_upgrade(self, hero_name: str):
        hero = self.get_hero(hero_name)
        if not hero:
            return
        update_data = (hero[2] + 1, hero[0], hero[1])
        self.cursor.execute(
            "UPDATE hero SET level = ? WHERE id = ? AND hero_name = ?", update_data
        )
        self.conn.commit()
        return self.get_hero(hero_name)

    def close(self):
        self.conn.close()


app_db = AppDB()

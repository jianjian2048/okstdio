"""数据库操作模块

使用 SQLite 存储英雄数据
数据库文件位置: example/assets/app.db
"""

import sqlite3


class AppDB:
    """应用数据库类
    
    封装了所有数据库操作，包括：
    - 表结构创建
    - 英雄的增删改查
    - 英雄升级
    """

    def __init__(self) -> None:
        """初始化数据库连接
        
        自动创建数据库文件（如果不存在）
        并初始化所有表结构
        """
        self.conn = sqlite3.connect("example/assets/app.db")
        self.cursor = self.conn.cursor()
        self.create_all_table()

    def create_all_table(self):
        """创建所有数据表
        
        使用 IF NOT EXISTS 确保多次调用是安全的
        
        表结构:
        - id: 自增主键
        - hero_name: 英雄名称（唯一，非空）
        - level: 等级（0-50）
        """
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
        """创建新英雄
        
        Args:
            hero_name: 英雄名称（必须唯一）
            
        初始等级为 0
        如果名称重复会抛出 sqlite3.IntegrityError
        """
        self.cursor.execute(
            "INSERT INTO hero(hero_name, level) VALUES (?, ?)", (hero_name, 0)
        )
        self.conn.commit()

    def get_hero_list(self):
        """获取所有英雄列表
        
        Returns:
            list[tuple]: [(id, hero_name, level), ...]
        """
        self.cursor.execute("SELECT id, hero_name, level FROM hero")
        return self.cursor.fetchall()

    def get_hero(self, hero_name: str):
        """根据名称查询英雄
        
        Args:
            hero_name: 英雄名称
            
        Returns:
            tuple | None: (id, hero_name, level) 或 None（如果不存在）
        """
        self.cursor.execute(
            "SELECT id, hero_name, level FROM hero WHERE hero_name = ?", (hero_name,)
        )
        hero = self.cursor.fetchone()
        if hero:
            return hero
        return None

    def hero_upgrade(self, hero_name: str):
        """英雄升级
        
        Args:
            hero_name: 英雄名称
            
        Returns:
            int | None: 升级后的等级，如果英雄不存在返回 None
            
        等级 +1，不会超过 50（由数据库约束保证）
        """
        hero = self.get_hero(hero_name)
        if not hero:
            return
        update_data = (hero[2] + 1, hero[0], hero[1])
        self.cursor.execute(
            "UPDATE hero SET level = ? WHERE id = ? AND hero_name = ?", update_data
        )
        self.conn.commit()
        return self.get_hero(hero_name)[2]

    def close(self):
        """关闭数据库连接
        
        应用退出时调用
        """
        self.conn.close()


# 全局数据库实例
app_db = AppDB()

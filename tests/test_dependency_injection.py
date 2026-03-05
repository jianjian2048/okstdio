"""依赖注入系统测试"""

import asyncio
from okstdio.server import RPCServer, IOWrite


# 测试依赖类
class Database:
    """模拟数据库连接"""
    def __init__(self):
        self.connection_string = "DB Connection"
        self.created_at = asyncio.get_event_loop().time()


class Config:
    """模拟配置对象"""
    def __init__(self):
        self.debug = True
        self.version = "1.0.0"


async def test_builtin_iowrite():
    """测试内置 IOWrite 依赖"""
    print("测试 1: 内置 IOWrite 依赖")
    app = RPCServer("test_app")
    
    @app.add_method()
    async def test_io(io_write: IOWrite) -> str:
        return f"IOWrite injected: {type(io_write).__name__}"
    
    # 模拟执行
    result = await app._RPCServer__execute_method(
        test_io, 
        {}, 
        "test_id"
    )
    print(f"  结果：{result.result}")
    assert "IOWrite" in result.result
    print("  ✓ 通过\n")


async def test_custom_dependency():
    """测试自定义依赖"""
    print("测试 2: 自定义依赖（单例）")
    app = RPCServer("test_app")
    
    # 注册 Database 依赖
    app.register_dependency(Database, lambda: Database(), singleton=True)
    
    @app.add_method()
    def get_db(db: Database) -> dict:
        return {"connection": db.connection_string}
    
    # 模拟执行
    result = await app._RPCServer__execute_method(
        get_db,
        {},
        "test_id"
    )
    print(f"  结果：{result.result}")
    assert result.result["connection"] == "DB Connection"
    print("  ✓ 通过\n")


async def test_singleton_behavior():
    """测试单例行为"""
    print("测试 3: 单例行为验证")
    app = RPCServer("test_app")
    
    app.register_dependency(Database, lambda: Database(), singleton=True)
    
    def get_db_info(db: Database) -> dict:
        return {"created_at": db.created_at}
    
    # 第一次执行
    result1 = await app._RPCServer__execute_method(get_db_info, {}, "id1")
    # 第二次执行
    result2 = await app._RPCServer__execute_method(get_db_info, {}, "id2")
    
    print(f"  第一次创建时间：{result1.result['created_at']}")
    print(f"  第二次创建时间：{result2.result['created_at']}")
    assert result1.result['created_at'] == result2.result['created_at']
    print("  ✓ 单例验证通过\n")


async def test_non_singleton_behavior():
    """测试非单例行为"""
    print("测试 4: 非单例行为验证")
    app = RPCServer("test_app")
    
    # 使用一个计数器来验证每次都是新实例
    instance_count = {"count": 0}
    
    def create_db():
        instance_count["count"] += 1
        db = Database()
        db.instance_id = instance_count["count"]
        return db
    
    app.register_dependency(Database, create_db, singleton=False)
    
    def get_db_info(db: Database) -> dict:
        return {"instance_id": db.instance_id}
    
    # 第一次执行
    result1 = await app._RPCServer__execute_method(get_db_info, {}, "id1")
    # 第二次执行
    result2 = await app._RPCServer__execute_method(get_db_info, {}, "id2")
    
    print(f"  第一次实例 ID: {result1.result['instance_id']}")
    print(f"  第二次实例 ID: {result2.result['instance_id']}")
    assert result1.result['instance_id'] != result2.result['instance_id']
    print("  ✓ 非单例验证通过\n")


async def test_multiple_dependencies():
    """测试多个依赖"""
    print("测试 5: 多个依赖注入")
    app = RPCServer("test_app")
    
    app.register_dependency(Database, lambda: Database(), singleton=True)
    app.register_dependency(Config, lambda: Config(), singleton=True)
    
    def get_info(db: Database, config: Config) -> dict:
        return {
            "db": db.connection_string,
            "debug": config.debug,
            "version": config.version
        }
    
    result = await app._RPCServer__execute_method(
        get_info,
        {},
        "test_id"
    )
    print(f"  结果：{result.result}")
    assert result.result["db"] == "DB Connection"
    assert result.result["debug"] == True
    assert result.result["version"] == "1.0.0"
    print("  ✓ 通过\n")


async def test_delayed_registration():
    """测试延迟注册"""
    print("测试 6: 延迟注册（运行时动态注册）")
    app = RPCServer("test_app")
    
    # 初始不注册，在方法中注册
    def init_device(device_id: str) -> dict:
        # 模拟创建设备对象
        device = Database()
        device.connection_string = f"Device-{device_id}"
        app.register_dependency(Database, lambda: device, singleton=True)
        return {"status": f"Device {device_id} registered"}
    
    def use_device(db: Database) -> dict:
        return {"connection": db.connection_string}
    
    # 先初始化设备
    result1 = await app._RPCServer__execute_method(
        init_device,
        {"device_id": "DEV001"},
        "id1"
    )
    print(f"  初始化结果：{result1.result}")
    
    # 使用设备
    result2 = await app._RPCServer__execute_method(
        use_device,
        {},
        "id2"
    )
    print(f"  使用结果：{result2.result}")
    assert result2.result["connection"] == "Device-DEV001"
    print("  ✓ 通过\n")


async def test_string_key_dependency():
    """测试字符串键依赖"""
    print("测试 7: 字符串键依赖（工厂函数）")
    app = RPCServer("test_app")
    
    # 注册工厂函数 - 返回一个不需要参数的工厂
    app.register_dependency(
        "db_factory",
        lambda: lambda db_name: Database(),
        singleton=True
    )
    
    def use_factory() -> dict:
        factory = app.get_dependency("db_factory")
        db = factory("test_db")
        return {"connection": db.connection_string}
    
    result = await app._RPCServer__execute_method(
        use_factory,
        {},
        "test_id"
    )
    print(f"  结果：{result.result}")
    assert result.result["connection"] == "DB Connection"
    print("  ✓ 通过\n")


async def main():
    """运行所有测试"""
    print("=" * 50)
    print("依赖注入系统测试")
    print("=" * 50 + "\n")
    
    await test_builtin_iowrite()
    await test_custom_dependency()
    await test_singleton_behavior()
    await test_non_singleton_behavior()
    await test_multiple_dependencies()
    await test_delayed_registration()
    await test_string_key_dependency()
    
    print("=" * 50)
    print("所有测试通过！✓")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

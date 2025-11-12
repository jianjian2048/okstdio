# Example - 英雄管理系统

这是一个完整的 OkStdio 示例项目，演示了如何构建一个基于 JSON-RPC 的英雄管理和战斗系统。

## 项目结构

```
example/
├── __init__.py          # 包标识
├── server.py            # RPC 服务器
├── client.py            # RPC 客户端
├── schemas.py           # 数据模型定义
├── databases.py         # 数据库操作
├── assets/
│   ├── app.db          # SQLite 数据库
│   ├── app.log         # 服务器日志
│   └── client.log      # 客户端日志
└── README.md           # 本文档
```

## 功能特性

### 1. 英雄管理
- ✅ 创建英雄（唯一名称，初始等级 0）
- ✅ 查询英雄信息
- ✅ 等级限制：0-50 级

### 2. 副本战斗系统
- ✅ 进入副本开始战斗
- ✅ 实时推送战斗结果
- ✅ 经验增长和自动升级
- ✅ 随机怪物（史莱姆、哥布林、牛头）
- ✅ 战斗时间和经验奖励
- ✅ 停止战斗

### 3. 技术亮点
- 完整的异步支持
- 流式数据推送（IOWrite）
- 中间件日志记录
- SQLite 数据持久化
- 自动生成 API 文档
- UTF-8 编码支持（Windows/Linux）

## 快速开始

### 运行客户端（推荐）

客户端会自动启动服务器：

```bash
# 使用模块方式运行
python -m example.client
```

### 单独运行服务器

```bash
# 生成 API 文档并启动服务器
python -m example.server
```

服务器启动后会：
1. 生成 `example_server.md` API 文档
2. 监听 stdin，等待 JSON-RPC 请求

### 手动测试

在服务器运行时，可以手动输入 JSON-RPC 请求：

```bash
python -m example.server
```

然后输入：

```json
{"jsonrpc": "2.0", "method": "healthy", "params": {}, "id": 1}
{"jsonrpc": "2.0", "method": "hero.create", "params": {"hero": {"hero_name": "张三"}}, "id": 2}
```

## API 文档

运行服务器会自动生成 `example_server.md`，包含完整的 API 文档。

### 主要接口

#### 1. 健康检查

```json
请求: {"jsonrpc": "2.0", "method": "healthy", "params": {}, "id": 1}
响应: {"jsonrpc": "2.0", "result": {"status": "ok"}, "id": 1}
```

#### 2. 创建英雄

```json
请求: {
  "jsonrpc": "2.0",
  "method": "hero.create",
  "params": {"hero": {"hero_name": "heimi"}},
  "id": 2
}

成功响应: {
  "jsonrpc": "2.0",
  "result": {
    "hero_name": "heimi",
    "hero_id": 1,
    "level": 0
  },
  "id": 2
}

失败响应: {
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "英雄 heimi 已经存在,无法再次创建.",
    "data": null
  },
  "id": 2
}
```

#### 3. 进入副本战斗

```json
请求: {
  "jsonrpc": "2.0",
  "method": "hero.dungeon",
  "params": {"hero_name": "heimi"},
  "id": 3
}

响应: {
  "jsonrpc": "2.0",
  "result": {
    "task_id": "abc123...",
    "hero": {
      "hero_name": "heimi",
      "hero_id": 1,
      "level": 0
    }
  },
  "id": 3
}

后续流式消息 (使用 task_id):
{
  "jsonrpc": "2.0",
  "result": {
    "fighting_news": "heimi 击败了 史莱姆, 耗时 1",
    "rewards": "增加了 10 经验"
  },
  "id": "abc123..."
}
```

#### 4. 停止战斗

```json
请求: {
  "jsonrpc": "2.0",
  "method": "hero.stop_dungeon",
  "params": {"task_id": "abc123..."},
  "id": 4
}

响应: {
  "jsonrpc": "2.0",
  "result": true,
  "id": 4
}
```

## 代码解析

### schemas.py - 数据模型

定义了所有的数据结构：

```python
class PublicHero(BaseModel):
    """英雄信息"""
    hero_id: int | None = Field(None, description="英雄ID")
    hero_name: str = Field(description="英雄名称")
    level: int = Field(..., ge=0, le=50, description="等级 0-50")

class FightingTask(BaseModel):
    """战斗任务"""
    task_id: str = Field(default_factory=lambda: uuid4().hex, description="任务ID")
    hero: PublicHero = Field(..., description="英雄")

class FightingResult(BaseModel):
    """战斗结果"""
    fighting_news: str = Field(..., description="战斗信息")
    rewards: str = Field(..., description="战利品")
```

### databases.py - 数据库操作

使用 SQLite 存储英雄数据：

```python
class AppDB:
    def create_hero(self, hero_name: str):
        """创建英雄，初始等级为 0"""
        
    def get_hero(self, hero_name: str):
        """根据名称查询英雄"""
        
    def hero_upgrade(self, hero_name: str):
        """英雄升级（等级 +1）"""
```

**数据库表结构**：

```sql
CREATE TABLE hero (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_name TEXT NOT NULL UNIQUE,
    level INTEGER CHECK(level BETWEEN 0 AND 50)
)
```

### server.py - 服务器

#### 中间件

```python
@app.add_middleware(label="请求日志")
async def logmw(request: JSONRPCRequest, call_next):
    """记录所有请求到日志文件"""
    logger.info(f"收到请求: {request.model_dump_json()}")
    res = await call_next(request)
    return res
```

#### 路由分组

```python
# 创建路由分组
hero_router = RPCRouter(prefix="hero", label="英雄方法")

# 注册方法到路由
@hero_router.add_method(name="create", label="创建英雄")
def create(hero: CreateHero) -> PublicHero | JSONRPCServerErrorDetail:
    ...

# 将路由挂载到主应用
app.include_router(hero_router)
```

#### 异步战斗任务

```python
async def fighting(fighting_task: FightingTask, io_write: IOWrite):
    """后台战斗任务，不断推送战斗结果"""
    while True:
        # 随机选择怪物
        monster = random.choice(["史莱姆", "哥布林", "牛头"])
        
        # 模拟战斗时间
        await asyncio.sleep(fighting_time)
        
        # 推送战斗结果
        await io_write.write(JSONRPCResponse(
            id=fighting_task.task_id,
            result=FightingResult(...)
        ))
```

#### 流式响应

```python
@hero_router.add_method(name="dungeon", label="开始战斗")
async def dungeon(
    hero_name: Annotated[str, Field(..., description="英雄名称")],
    io_write: IOWrite,  # 注入 IOWrite 依赖
) -> FightingTask | JSONRPCServerErrorDetail:
    # 创建后台任务
    task = asyncio.create_task(fighting(fighting_task, io_write))
    tasks[fighting_task.task_id] = task
    
    # 立即返回任务信息
    return fighting_task
```

### client.py - 客户端

#### 连接服务器

```python
async with RPCClient("example_client") as client:
    # 启动服务器进程（模块方式）
    await client.start("example.server")
```

#### 发送请求

```python
# 发送请求并等待响应
future = await client.send("hero.create", {"hero": {"hero_name": "heimi"}})
response = await future

# 检查是否成功
if hasattr(response, 'result'):
    print("成功:", response.result)
else:
    print("错误:", response.error)
```

#### 监听流式消息

```python
# 添加监听队列
queue = client.add_listen_queue(task_id)

# 持续接收消息
for _ in range(10):
    response = await queue.get()
    print(response.result)  # 战斗结果

# 停止战斗
await client.send("hero.stop_dungeon", {"task_id": task_id})
```

## 运行流程

### 完整的客户端-服务器交互流程

```
1. 客户端启动
   ↓
2. 客户端启动服务器子进程
   ↓
3. 服务器初始化数据库和日志
   ↓
4. 客户端发送 "healthy" 请求
   ↓ 
5. 服务器响应 {"status": "ok"}
   ↓
6. 客户端发送 "hero.create" 请求
   ↓
7. 服务器创建英雄并返回
   ↓
8. 客户端发送 "hero.dungeon" 请求
   ↓
9. 服务器启动战斗任务并立即返回 task_id
   ↓
10. 服务器持续推送战斗结果 (流式消息)
    ↓
11. 客户端监听队列接收战斗结果
    ↓
12. 客户端发送 "hero.stop_dungeon" 请求
    ↓
13. 服务器取消战斗任务
    ↓
14. 客户端关闭，服务器进程退出
```

## 日志系统

### 服务器日志 (example/assets/app.log)

```
[11-13 00:47:02] INFO @server > 收到请求: {"jsonrpc":"2.0","method":"healthy","params":{},"id":"abc123"}
[11-13 00:47:02] INFO @server > 收到请求: {"jsonrpc":"2.0","method":"hero.create","params":{...},"id":"def456"}
[11-13 00:47:02] INFO @server > 战斗结果: heimi vs 史莱姆
```

### 客户端日志 (example/assets/client.log)

```
[11-13 00:47:02] DEBUG @example_client > {"jsonrpc":"2.0","result":{"status":"ok"},"id":"abc123"}
[11-13 00:47:02] DEBUG @example_client > {"jsonrpc":"2.0","result":{...},"id":"def456"}
```

**注意**：日志只写入文件，不会输出到 stdout，确保不干扰 JSON-RPC 通信。

## 数据库

### 位置
`example/assets/app.db`

### 查看数据

```bash
sqlite3 example/assets/app.db

sqlite> SELECT * FROM hero;
id|hero_name|level
1|heimi|5
2|zhangsan|3
```

### 清空数据

```bash
rm example/assets/app.db
# 下次运行会自动创建新数据库
```

## 常见问题

### Q: 为什么要用 `python -m example.client` 而不是 `python example/client.py`？

A: 使用模块方式运行可以正确处理包内导入。如果使用脚本方式，需要修改导入路径。

### Q: 如何调试服务器？

A: 单独运行服务器，然后手动输入 JSON-RPC 请求：

```bash
python -m example.server
# 输入 JSON 请求进行测试
```

### Q: 为什么日志看不到？

A: 日志写入文件而不是控制台。查看：
- 服务器日志：`example/assets/app.log`
- 客户端日志：`example/assets/client.log`

### Q: Windows 下中文显示乱码？

A: 框架已自动处理 Windows 编码问题，确保使用最新版本。

### Q: 如何停止长时间运行的战斗任务？

A: 调用 `hero.stop_dungeon` 方法，传入 `task_id`：

```python
await client.send("hero.stop_dungeon", {"task_id": task_id})
```

## 扩展建议

### 1. 添加更多英雄属性

```python
class PublicHero(BaseHero):
    hero_id: int | None = Field(None, description="英雄ID")
    hero_name: str = Field(description="英雄名称")
    level: int = Field(..., ge=0, le=50, description="等级 0-50")
    hp: int = Field(100, description="生命值")
    attack: int = Field(10, description="攻击力")
    defense: int = Field(5, description="防御力")
```

### 2. 实现装备系统

```python
class Equipment(BaseModel):
    name: str
    attack_bonus: int
    defense_bonus: int

@hero_router.add_method(name="equip")
def equip_item(hero_name: str, equipment: Equipment) -> PublicHero:
    ...
```

### 3. 添加英雄列表

```python
@hero_router.add_method(name="list")
def list_heroes() -> list[PublicHero]:
    heroes = app_db.get_hero_list()
    return [PublicHero(hero_id=h[0], hero_name=h[1], level=h[2]) for h in heroes]
```

### 4. 实现技能系统

```python
class Skill(BaseModel):
    name: str
    damage: int
    cooldown: int

@hero_router.add_method(name="use_skill")
async def use_skill(hero_name: str, skill: Skill) -> dict:
    ...
```

## 参考资料

- [OkStdio 文档](../README.md)
- [JSON-RPC 2.0 规范](https://www.jsonrpc.org/specification)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [SQLite 教程](https://www.sqlite.org/docs.html)

---

**提示**: 这个示例展示了 OkStdio 的核心功能，你可以基于此构建更复杂的应用！


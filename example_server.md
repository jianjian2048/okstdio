# EXAMPLE_SERVER API 文档

- 版本: `v0.1.0`

## 全局中间件
### logmw `请求日志`

> 日志文件路径: `/example/assets/app.log`
> 日志输出格式: `[%(asctime)s] %(levelname)s @%(name)s > %(message)s`


## 顶层方法
### healthy `健康`
> 返回服务器是否健康 `{"status": "ok"}`

**参数:**

> *无参数*

**返回:**

> **类型:** `HealthyResult`
>
> **说明:**
>> 健康响应
>
> **字段:**
>
>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>> | --- | --- | --- | --- | --- |
>> | `status` | string | 否 | `"ok"` | 健康状态常量 (常量: ok) |

## 路由 hero
### hero.create `创建英雄`
> 创建一个英雄:
> ```json
> {"jsonrpc": "2.0", "method": "hero.create", "params": {"hero": {"hero_name": "英雄名称"}}, "id": 1}
> ```

**参数:**

> | 参数名 | 类型 | 必填 | 默认值 | 描述 |
> | --- | --- | --- | --- | --- |
> | `hero` | CreateHero | 是 | - | - |
>
> **`hero` 字段:**
>
>
> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
> | --- | --- | --- | --- | --- |
> | `hero_name` | string | 是 | - | 英雄名称 |

**返回:**

> **类型:** `PublicHero`
>
> **说明:**
>> 英雄
>
> **字段:**
>
>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>> | --- | --- | --- | --- | --- |
>> | `hero_name` | string | 是 | - | 英雄名称 |
>> | `hero_id` | integer / null | 否 | `null` | 英雄ID |
>> | `level` | integer | 是 | - | 等级 0-50 (最小: 0, 最大: 50) |
>
> ---
> **类型:** `JSONRPCServerErrorDetail`
>
> **字段:**
>
>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>> | --- | --- | --- | --- | --- |
>> | `code` | integer | 否 | `-32000` | 错误码 (最小: -32099, 最大: -32000) |
>> | `message` | string | 是 | - | 错误信息 |
>> | `data` | object / array / null | 否 | `null` | 错误数据 |

### hero.dungeon `开始战斗`
> 进入一个副本, 打怪升级:
> ```json
> {"jsonrpc": "2.0", "method": "hero.dungeon", "params": {"hero_name": "英雄名称"}, "id": 1}
> ```

**参数:**

> | 参数名 | 类型 | 必填 | 默认值 | 描述 |
> | --- | --- | --- | --- | --- |
> | `hero_name` | str | 是 | - | 英雄名称 |

**返回:**

> **类型:** `FightingTask`
>
> **字段:**
>
>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>> | --- | --- | --- | --- | --- |
>> | `task_id` | string | 否 | - | 任务ID |
>> | `hero` | PublicHero | 是 | - | - |
>>
>> **引用模型: `PublicHero`**
>>
>>
>>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>>> | --- | --- | --- | --- | --- |
>>> | `hero_name` | string | 是 | - | 英雄名称 |
>>> | `hero_id` | integer / null | 否 | `null` | 英雄ID |
>>> | `level` | integer | 是 | - | 等级 0-50 (最小: 0, 最大: 50) |
>
> ---
> **类型:** `JSONRPCServerErrorDetail`
>
> **字段:**
>
>> | 字段名 | 类型 | 必填 | 默认值 | 描述 |
>> | --- | --- | --- | --- | --- |
>> | `code` | integer | 否 | `-32000` | 错误码 (最小: -32099, 最大: -32000) |
>> | `message` | string | 是 | - | 错误信息 |
>> | `data` | object / array / null | 否 | `null` | 错误数据 |

### hero.stop_dungeon `停止战斗`
> 通过战斗的ID停止

**参数:**

> | 参数名 | 类型 | 必填 | 默认值 | 描述 |
> | --- | --- | --- | --- | --- |
> | `task_id` | str | 是 | - | 战斗的ID |

**返回:**

> **类型:** `bool`
>
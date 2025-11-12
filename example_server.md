# EXAMPLE_SERVER API 文档

- 版本: `v0.1.0`

## 全局中间件
- **logmw** `请求日志`


## 顶层方法
### healthy `健康`
返回服务器是否健康

return :
```json
{"status": "ok"}
```

**参数**
*无参数*
**返回**
| 类型 | 说明 |
| --- | --- |
| dict | - |

## 路由 hero
### hero.create
创建一个英雄:
```json
{"jsonrpc": "2.0", "method": "hero.create", "params": {"hero": {"hero_name": "英雄名称"}}, "id": 1}
```

**参数**
| 参数名 | 类型 | 必填 | 默认值 |
| --- | --- | --- | --- |
| `hero` | CreateHero | 是 | - |

```json
{
  "properties": {
    "hero_name": {
      "description": "英雄名称",
      "title": "Hero Name",
      "type": "string"
    }
  },
  "required": [
    "hero_name"
  ],
  "title": "CreateHero",
  "type": "object"
}
```

**返回**
| 类型 | 说明 |
| --- | --- |
| example.schemas.PublicHero | okstdio.general.jsonrpc_model.JSONRPCServerErrorDetail | - |

### hero.dungeon
进入一个副本, 打怪升级:
```json
{"jsonrpc": "2.0", "method": "hero.dungeon", "params": {"hero_name": "英雄名称"}, "id": 1}
```

**参数**
| 参数名 | 类型 | 必填 | 默认值 |
| --- | --- | --- | --- |
| `hero_name` | typing.Annotated[str, FieldInfo(annotation=NoneType, required=True, description='英雄名称')] | 是 | - |

**返回**
| 类型 | 说明 |
| --- | --- |
| example.schemas.FightingTask | okstdio.general.jsonrpc_model.JSONRPCServerErrorDetail | - |
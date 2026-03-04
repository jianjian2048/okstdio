---
name: python-documentation
description: 审查并更新Python文档以匹配项目标准。在以下情况下使用：(1)编写需要文档的新代码，(2)审查现有代码的文档缺失情况，(3)代码更改后更新docstring，(4)为复杂逻辑添加内联注释，(5)组织导入语句。强制执行Google风格的docstring、初学者友好的内联注释和正确的导入结构。
---

# Python文档标准

审查并更新Python文档以匹配项目标准：Google风格的docstring、初学者友好的内联注释和组织良好的导入语句。

## 使用时机

- 编写新模块、类或函数
- 审查代码的文档完整性
- 修改代码后（docstring可能已过时）
- 使复杂代码易于理解
- 组织文件中的导入语句

## 文档检查清单

### 1. 模块级Docstring

每个Python文件都需要在顶部添加模块docstring：

```python
"""模块用途的简短描述。

较长的描述，解释：
- 此模块提供的内容
- 关键类/函数
- 使用上下文

示例：
    如果有帮助，提供基本用法示例。
"""
```

### 2. 类Docstrings

```python
class DataProcessor:
    """类用途的一行摘要。

    较长的描述，解释行为、使用模式
    和任何重要说明。

    属性:
        threshold: float
            处理的阈值。
        window: int
            回看窗口大小。

    示例:
        >>> processor = DataProcessor(threshold=0.5)
        >>> processor.run(data)
    """
```

### 3. 函数/方法Docstrings（Google风格）

```python
def process_data(
    data: list,
    threshold: float = 0.0,
    window: int = 14,
) -> list:
    """使用可配置参数处理输入数据。

    应用处理逻辑到输入数据，基于阈值进行过滤
    并使用滚动窗口进行计算。

    参数:
        data: 要处理的数值列表。
            不能为空。
        threshold: 输出中包含的最小值。
            正值更积极地过滤。默认为0.0。
        window: 滚动计算的项数。
            较大的窗口产生更平滑但更滞后的结果。
            默认为14。

    返回:
        与输入长度相同的处理值列表。
        低于阈值的值设置为None。

    异常:
        ValueError: 如果data为空或window小于1。
        TypeError: 如果data包含非数值。

    示例:
        >>> results = process_data([1, 2, 3, 4, 5], threshold=2.0)
        >>> filtered = [r for r in results if r is not None]
    """
```

### 4. 内联注释

**要：解释"为什么"和复杂逻辑**

```python
# 使用扩展窗口计算滚动平均值
# 我们使用expanding()而不是rolling()来处理预热期
# 而不会在开始时引入NaN值
average = values.expanding(min_periods=1).mean()

# 将结果向前移动以避免在计算中使用当前值
# 没有这个，我们会使用今天的数据来计算今天的结果
shifted = results[:-1]

# 对独立迭代使用并行执行
# 这在多核系统上提供约4倍的加速
for i in range(n_workers):
```

**不要：陈述显而易见的内容**

```python
# 错误：陈述代码做什么，而不是为什么
i = 0  # 将i设置为0
data = df['value']  # 获取value列

# 正确：解释目的或陷阱
i = 0  # 从预热期后的第一个有效项开始
data = df['value']  # 对于此计算，使用原始值（而非归一化值）
```

### 5. 导入组织

```python
# 标准库
import os
from datetime import datetime
from typing import Dict, List, Optional

# 第三方库
import numpy as np
import pandas as pd
import requests
from sqlalchemy import create_engine

# 第一方库
from myproject.core import DataManager
from myproject.utils import helpers
from myproject.config import settings
```

**规则：**
- 仅使用绝对导入（不要使用`from . import`）
- 在每个部分内按字母顺序排列
- 每个部分之间用一个空行分隔
- 使用`isort`维护结构

## 审查流程

### 步骤1：扫描缺失的文档

```bash
# 查找没有docstring的函数
grep -n "def " file.py | while read line; do
    # 检查下一个非空行是否是docstring
done
```

或手动检查：
- [ ] 模块有docstring
- [ ] 所有类都有带Attributes部分的docstrings
- [ ] 所有公共方法都有Args/Returns/Raises
- [ ] 所有私有方法至少有一行摘要
- [ ] 复杂逻辑有内联注释

### 步骤2：验证Docstring准确性

代码更改后，docstring通常会过时：

```python
# 错误：Docstring与签名不匹配
def calculate(data: list, window: int = 14) -> list:
    """计算结果。

    参数:
        data: 输入数据。
        period: 回看周期。  # 错误：参数是'window'，不是'period'
    """
```

**检查：**
- [ ] 所有参数与函数签名匹配
- [ ] docstring中的默认值与实际默认值匹配
- [ ] 返回类型描述与实际返回匹配
- [ ] Raises部分列出所有可能的异常

### 步骤3：添加缺失的内联注释

关注：
1. **算法细节** - 解释优化选择
2. **库模式** - 解释非显而易见的API用法
3. **领域逻辑** - 解释对不熟悉领域的读者的业务规则
4. **性能决策** - 为什么这个算法优于其他算法
5. **边缘情况** - 为什么存在某些检查

### 步骤4：组织导入

运行isort或手动组织：
```bash
isort --profile black --sections STDLIB,THIRDPARTY,FIRSTPARTY file.py
```

## 常见问题

### 问题1：缺少参数文档

```python
# 错误
def run(self, data_manager, config, **kwargs):
    """使用给定配置运行处理器。"""

# 正确
def run(self, data_manager, config, **kwargs):
    """使用给定配置运行处理器。

    参数:
        data_manager: 提供输入数据的DataManager实例。
        config: 包含处理参数的配置字典。
        **kwargs: 传递给处理函数的额外参数。
            常见的kwargs包括'window'、'threshold'。

    返回:
        具有可作为属性访问的结果的处理器实例。
    """
```

### 问题2：过时的默认值

```python
# 错误：Docstring说默认是14，但代码使用20
def calculate(window: int = 20) -> list:
    """计算结果。

    参数:
        window: 回看周期。默认为14。  # 错误！
    """

# 正确
def calculate(window: int = 20) -> list:
    """计算结果。

    参数:
        window: 回看周期。默认为20。
    """
```

### 问题3：缺少异常部分

```python
# 错误：函数抛出异常但没有记录
def validate(data):
    """验证输入数据。"""
    if data is None:
        raise ValueError("数据不能为None")

# 正确
def validate(data):
    """验证输入数据。

    参数:
        data: 要验证的输入数据。

    异常:
        ValueError: 如果data为None或为空。
    """
    if data is None:
        raise ValueError("数据不能为None")
```

### 问题4：没有解释复杂逻辑

```python
# 错误：没有解释
result = [
    v for i, v in enumerate(data)
    if i > window and data[i-1] > threshold and flags[i]
]

# 正确：逐步解释
# 根据多个条件过滤值：
# 1. 跳过预热期（前'window'项）
# 2. 前一个值必须超过阈值（趋势确认）
# 3. 必须设置标志（外部验证通过）
result = [
    v for i, v in enumerate(data)
    if i > window           # 跳过预热期
    and data[i-1] > threshold  # 趋势确认
    and flags[i]            # 外部验证
]
```

## 输出格式

审查文档时，报告：

```
## 文档审查：[文件名]

### 摘要
- 函数：X个总数，Y个缺少docstring
- 类：X个总数，Y个缺少docstring
- 内联注释：[充足/稀疏/缺失]
- 导入组织：[正确/需要修复]

### 发现的问题

#### 缺少Docstrings
1. 第X行的`function_name()` - 需要Args/Returns/Raises

#### 过时的文档
1. 第X行的`function_name()` - 默认值不匹配

#### 缺少内联注释
1. 第X-Y行：复杂操作需要解释

### 建议的修复
[提供要添加的特定docstring/注释文本]
```

## 快速参考

| 元素 | 必需部分 |
|---------|------------------|
| 模块 | 摘要、描述 |
| 类 | 摘要、属性 |
| 公共函数 | 摘要、参数、返回、异常（如适用） |
| 私有函数 | 至少一行摘要 |
| 复杂逻辑 | 解释为什么的内联注释 |

## 与其他技能的集成

- **code-reviewer**：作为审查的一部分检查文档
- **verification-before-completion**：在更改后验证docstring已更新
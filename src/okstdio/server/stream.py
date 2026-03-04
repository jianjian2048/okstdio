"""Stdio 流模块

提供跨平台的标准输入输出流读写实现。
支持 Windows、Linux 和 macOS 平台的异步 I/O 操作。
"""

import asyncio
import sys
import os
import json
from typing import Optional
import logging
import io

logger = logging.getLogger("okstdio.server.stream")


# 在 Windows 上强制使用 UTF-8 编码
if os.name == "nt":
    # 重新包装 stdin 和 stdout 为 UTF-8
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


class PackStreamReader:
    """PackStreamReader 是用于读取标准输入的类。
    
    在 Windows 上，它使用 asyncio.to_thread 来读取输入数据。
    在 Linux 和 macOS 上，它使用事件循环的 add_reader 方法来添加标准输入的读取事件。
    
    支持异步读取，通过 readline 方法读取一行数据。
    
    例子：
        ```python
        reader = PackStreamReader()
        line = await reader.readline()
        print(f"收到: {line}")
        ```
    """

    def __init__(self):
        """初始化 PackStreamReader
        
        根据操作系统选择不同的读取策略：
            - Windows: 使用 asyncio.to_thread
            - Linux/macOS: 使用 _loop.add_reader
        """
        self.stdin = sys.stdin
        self._queue = asyncio.Queue()
        self._loop = asyncio.get_event_loop()

        # 在 Linux 和 macOS 上，使用 _loop.add_reader 方法来添加标准输入的读取事件.
        if os.name != "nt":
            self._loop.add_reader(self.stdin.fileno(), self._on_stdin_ready)

    def _on_stdin_ready(self):
        """标准输入就绪回调
        
        在 Linux/macOS 上，当标准输入有数据时被调用。
        读取数据并放入队列。
        """
        line = self.stdin.readline()
        self._queue.put_nowait(line)

    async def readline(self):
        """读取一行数据
        
        在 Windows 上，使用 asyncio.to_thread 方法来读取输入数据。
        在 Linux/macOS 上，从队列中获取数据。
        
        Returns:
            str: 读取的一行数据
        """
        # 在 Windows 上，使用 asyncio.to_thread 方法来读取输入数据.
        if os.name == "nt":
            return await asyncio.to_thread(self.stdin.readline)
        return await self._queue.get()


class PackStreamWriter:
    """PackStreamWriter 是用于写入标准输出的类。
    
    在 Windows 上，它使用 asyncio.to_thread 来写入数据。
    在 Linux 和 macOS 上，它使用事件循环的 run_in_executor 方法来写入数据。
    
    支持异步写入，通过 write 方法写入数据。
    
    例子：
        ```python
        writer = PackStreamWriter()
        await writer.write("Hello\\n")
        await writer.write(JSONRPCResponse(result="ok"))
        ```
    """

    def __init__(self):
        """初始化 PackStreamWriter
        
        根据操作系统选择不同的写入策略：
            - Windows: 使用 asyncio.to_thread
            - Linux/macOS: 使用事件循环的 run_in_executor
        """
        self.stdout = sys.stdout
        self._loop = asyncio.get_event_loop()
        self._lock = asyncio.Lock()

    async def write(self, data):
        """写入数据
        
        在 Windows 上，使用 asyncio.to_thread 方法来写入数据。
        在 Linux/macOS 上，使用事件循环的 run_in_executor 方法来写入数据。
        
        Args:
            data: 要写入的数据，可以是字符串或字节
        
        例子：
            ```python
            # 写入字符串
            await writer.write("Hello\\n")
            
            # 写入字节
            await writer.write(b"Hello\\n")
            ```
        """
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        async with self._lock:
            if os.name == "nt":
                await asyncio.to_thread(self.stdout.write, data)
                await asyncio.to_thread(self.stdout.flush)
            else:
                await self._loop.run_in_executor(None, self.stdout.write, data)
                await self._loop.run_in_executor(None, self.stdout.flush)

    def close(self):
        """关闭 PackStreamWriter
        
        刷新标准输出缓冲区。
        注意：不会关闭标准输出本身，只做 flush 操作。
        """
        try:
            # 只做 flush 而不要关闭；或至少在捕获时记录日志、区分 IOError 等常见情况。
            self.stdout.flush()
        except Exception as e:
            logger.exception(f"PackStreamWriter 关闭错误: {e}")
            raise e


class StdioStream:
    """StdioStream 是用于读取和写入标准输入输出的类.
    
    封装了 PackStreamReader 和 PackStreamWriter，提供统一的异步 I/O 接口。
    支持跨平台（Windows、Linux、macOS）的异步标准输入输出操作。
    
    核心功能：
        - 异步读取一行数据
        - 异步写入一行数据
        - 关闭流
    
    例子：
        ```python
        stream = StdioStream()
        
        # 读取数据
        line = await stream.read_line()
        
        # 写入数据
        await stream.write_line("Hello\\n")
        
        # 关闭流
        stream.close()
        ```
    """

    def __init__(self):
        """初始化 StdioStream
        
        创建 PackStreamReader 和 PackStreamWriter 实例。
        """
        self.reader = PackStreamReader()
        self.writer = PackStreamWriter()

    async def read_line(self) -> str:
        """读取一行数据
        
        Returns:
            str: 读取的一行数据，如果读取失败则返回空字符串
        """
        line = await self.reader.readline()
        return line if line else ""

    async def write_line(self, line: str) -> None:
        """写入一行数据
        
        Args:
            line: 要写入的行数据
        
        Raises:
            Exception: 当写入失败时
        
        例子：
            ```python
            # 写入字符串
            await stream.write_line("Hello\\n")
            
            # 写入 JSON
            await stream.write_line(json.dumps({"result": "ok"}) + "\\n")
            ```
        """
        try:
            logger.debug(f"StdioStream 准备响应: {line}")
            await self.writer.write(line.encode("utf-8") + b"\\n")
            logger.debug(f"StdioStream 发送响应: {line}")
        except Exception as e:
            logger.exception(f"StdioStream 发送响应错误: {e}")
            raise e

    def close(self) -> None:
        """关闭 StdioStream
        
        关闭写入器。
        """
        self.writer.close()

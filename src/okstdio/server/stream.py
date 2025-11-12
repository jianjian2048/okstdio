"""Stdio 流"""

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
    """PackStreamReader 是用于读取标准输入的类.
    在 Windows 上，它使用 asyncio.to_thread 来读取输入数据.
    在 Linux 上，它使用 _loop.add_reader 方法来添加标准输入的读取事件.
    在 macOS 上，它使用 _loop.add_reader 方法来添加标准输入的读取事件.
    它还使用 readline 方法来读取输入数据.
    """

    def __init__(self):
        self.stdin = sys.stdin
        self._queue = asyncio.Queue()
        self._loop = asyncio.get_event_loop()

        # 在 Linux 和 macOS 上，使用 _loop.add_reader 方法来添加标准输入的读取事件.
        if os.name != "nt":
            self._loop.add_reader(self.stdin.fileno(), self._on_stdin_ready)

    def _on_stdin_ready(self):
        line = self.stdin.readline()
        self._queue.put_nowait(line)

    async def readline(self):
        # 在 Windows 上，使用 asyncio.to_thread 方法来读取输入数据.
        if os.name == "nt":
            return await asyncio.to_thread(self.stdin.readline)
        return await self._queue.get()


class PackStreamWriter:
    """PackStreamWriter 是用于写入标准输出的类.
    在 Windows 上，它使用 asyncio.to_thread 来写入数据.
    在 Linux 上，它使用 _loop.run_in_executor 方法来写入数据.
    在 macOS 上，它使用 _loop.run_in_executor 方法来写入数据.
    它还使用 write 方法来写入数据.
    """

    def __init__(self):
        self.stdout = sys.stdout
        self._loop = asyncio.get_event_loop()
        self._lock = asyncio.Lock()

    async def write(self, data):
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
        try:
            # 只做 flush 而不要关闭；或至少在捕获时记录日志、区分 IOError 等常见情况。
            self.stdout.flush()
        except Exception as e:
            logger.exception(f"PackStreamWriter 关闭错误: {e}")
            raise e


# region StdioStream
class StdioStream:
    """StdioStream 是用于读取和写入标准输入输出的类."""

    def __init__(self):
        self.reader = PackStreamReader()
        self.writer = PackStreamWriter()

    async def read_line(self) -> str:
        """读取一行数据"""
        line = await self.reader.readline()
        return line if line else ""

    async def write_line(self, line: str) -> None:
        """写入一行数据"""
        try:
            logger.debug(f"StdioStream 准备响应: {line}")
            await self.writer.write(line.encode("utf-8") + b"\n")
            logger.debug(f"StdioStream 发送响应: {line}")
        except Exception as e:
            logger.exception(f"StdioStream 发送响应错误: {e}")
            raise e

    def close(self) -> None:
        """关闭 StdioStream"""
        self.writer.close()

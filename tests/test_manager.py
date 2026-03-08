import asyncio
import sys
from pathlib import Path
from okstdio.client import RPCClient, ClientManager, BroadcastResult
from rich import print
import logging

# 添加环境父文件夹到 path
parent_path = Path(__file__).resolve().parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

logging.basicConfig(level=logging.INFO)

SERVER_MODULE = "tests.test_server"


async def test_add_remove():
    """测试添加/移除客户端"""
    manager = ClientManager()

    # add
    client = manager.add("s1", SERVER_MODULE)
    assert isinstance(client, RPCClient)
    assert "s1" in manager
    assert len(manager) == 1

    # add_client
    client2 = RPCClient("s2", app=SERVER_MODULE)
    manager.add_client(client2)
    assert len(manager) == 2
    assert manager.client_names == ["s1", "s2"]

    # get / __getitem__
    assert manager.get("s1") is client
    assert manager["s2"] is client2
    assert manager.get("nonexistent") is None

    # remove
    removed = manager.remove("s1")
    assert removed is client
    assert "s1" not in manager
    assert len(manager) == 1

    # remove nonexistent
    assert manager.remove("nope") is None

    # clients property
    all_clients = manager.clients
    assert "s2" in all_clients

    print("[green]test_add_remove PASSED[/green]")


async def test_start_stop_all():
    """测试 start_all / stop_all"""
    async with ClientManager() as manager:
        manager.add("a", SERVER_MODULE)
        manager.add("b", SERVER_MODULE)
        await manager.start_all()

        # 验证客户端已启动，能发送请求
        future_a = await manager.send_to("a", "healthy")
        resp_a = await future_a
        assert resp_a.result is not None

        future_b = await manager.send_to("b", "healthy")
        resp_b = await future_b
        assert resp_b.result is not None

    # async with 退出后 stop_all 已调用
    print("[green]test_start_stop_all PASSED[/green]")


async def test_broadcast():
    """测试广播请求"""
    async with ClientManager() as manager:
        manager.add("c1", SERVER_MODULE)
        manager.add("c2", SERVER_MODULE)
        await manager.start_all()

        # 广播到所有
        results = await manager.broadcast("healthy", timeout=10)
        assert len(results) == 2
        for r in results:
            assert isinstance(r, BroadcastResult)
            assert r.error is None
            assert r.result is not None
            print(f"  {r.client_name}: {r.result}")

        # 广播到指定 targets
        results = await manager.broadcast("healthy", targets=["c1"], timeout=10)
        assert len(results) == 1
        assert results[0].client_name == "c1"

    print("[green]test_broadcast PASSED[/green]")


async def test_send_to_and_call_to():
    """测试 send_to / call_to"""
    async with ClientManager() as manager:
        manager.add("srv", SERVER_MODULE)
        await manager.start_all()

        # send_to
        future = await manager.send_to("srv", "healthy")
        resp = await future
        assert resp.result is not None

        # call_to (链式调用)
        result = await manager.call_to("srv", "healthy")
        assert result is not None

        # send_to nonexistent raises KeyError
        try:
            await manager.send_to("nonexistent", "healthy")
            assert False, "should raise KeyError"
        except KeyError:
            pass

    print("[green]test_send_to_and_call_to PASSED[/green]")


async def test_remove_and_stop():
    """测试 remove_and_stop"""
    async with ClientManager() as manager:
        manager.add("to_remove", SERVER_MODULE)
        await manager.start_all()

        # 先验证能用
        future = await manager.send_to("to_remove", "healthy")
        resp = await future
        assert resp.result is not None

        # remove_and_stop
        await manager.remove_and_stop("to_remove")
        assert "to_remove" not in manager
        assert len(manager) == 0

    print("[green]test_remove_and_stop PASSED[/green]")


async def main():
    await test_add_remove()
    await test_start_stop_all()
    await test_broadcast()
    await test_send_to_and_call_to()
    await test_remove_and_stop()
    print("[bold green]All manager tests PASSED![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())

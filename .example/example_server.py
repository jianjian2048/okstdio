from rpcfast import RPCServer, BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


app = RPCServer()


@app.method("create_item")
async def create_item(item: Item):
    total = item.price + (item.tax or 0)
    return {"total": total}


if __name__ == "__main__":
    app.run()

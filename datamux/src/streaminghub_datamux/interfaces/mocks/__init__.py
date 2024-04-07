from asyncio import Server


async def start_server(name: str) -> Server:
    if name == "empatica_e4":
        from .empatica_e4ss import start_server

        srv = await start_server()
        return srv
    else:
        raise ValueError(name)

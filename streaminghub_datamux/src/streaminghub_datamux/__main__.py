import argparse
import asyncio
import logging

from streaminghub_datamux.remote import DataMuxServer


async def serve(
    host: str,
    port: int,
    rpc: str,
):
    server = DataMuxServer(rpc_name=rpc)
    await server.start(host, port)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(prog="DataMux", description="CLI for StreamingHub DataMux")

    parser.add_argument("command", choices=["serve", "init", "replay"])
    parser.add_argument("-H", "--host", type=str)
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-r", "--rpc", type=str)
    parser.add_argument("--data_dir", type=str)
    parser.add_argument("--meta_dir", type=str)

    args = parser.parse_args()

    # Serving Remote API
    if args.command == "serve":
        try:
            assert args.host is not None
            assert args.port is not None
            assert args.rpc is not None
            asyncio.run(serve(args.host, args.port, args.rpc))
        except KeyboardInterrupt:
            logging.warning("Interrupt received, shutting down.")

    # Initializing .streaminghubrc
    if args.command == "init":
        import json
        from pathlib import Path

        assert args.data_dir is not None
        assert args.meta_dir is not None
        config = dict(data_dir=args.data_dir, meta_dir=args.meta_dir)
        fp = Path("~/.streaminghubrc").expanduser().resolve()
        with open(fp, "w") as f:
            json.dump(config, f)
        logging.info("Updated ~/.streaminghubrc")

import argparse
import asyncio
import logging

from rich.logging import RichHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(prog="DataMux", description="CLI for StreamingHub DataMux")

    parser.add_argument("command", choices=["serve", "init", "replay"])
    parser.add_argument("-H", "--host", type=str)
    parser.add_argument("-p", "--port", type=int)
    parser.add_argument("-r", "--rpc", type=str, choices=["websocket"])
    parser.add_argument("-c", "--codec", type=str, choices=["avro", "json"])
    parser.add_argument("--data_dir", type=str)
    parser.add_argument("--meta_dir", type=str)
    
    args = parser.parse_args()

    # Serving Remote API
    if args.command == "serve":
        from .serve import serve

        try:
            assert args.host is not None
            assert args.port is not None
            assert args.rpc is not None
            assert args.codec is not None
            asyncio.run(serve(args.host, args.port, args.rpc, args.codec))
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

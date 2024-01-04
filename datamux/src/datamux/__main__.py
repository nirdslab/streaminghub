import argparse
import asyncio
import logging

from rich.logging import RichHandler

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(prog="DataMux", description="CLI for StreamingHub DataMux")

    parser.add_argument("command")
    parser.add_argument("-H", "--host", type=str)
    parser.add_argument("-p", "--port", type=int)

    args = parser.parse_args()

    if args.command == "serve":
        from .serve import serve

        try:
            asyncio.run(serve(args.host, args.port))
        except KeyboardInterrupt:
            logging.warning("Interrupt received, shutting down.")

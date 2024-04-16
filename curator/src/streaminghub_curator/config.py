import json
import logging
import os
import platform
import socket
from pathlib import Path

from flask import Flask
from flask_session import Session


class Config:
    def __init__(self):
        # get host information
        self.hostname = socket.gethostname()
        self.IPAddr = socket.gethostbyname(self.hostname)
        # Config file
        template_dir = Path(__file__).parent / "templates"
        static_dir = Path(__file__).parent / "static"
        fname = "config.json"
        if platform.system() == "Windows":
            fname = "config_win.json"
        config_fp = template_dir / fname
        with open(config_fp) as json_data_file:
            data = json.load(json_data_file)
        self.hidden_list: list[str] = data["hidden"]
        self.pwd_hash: str = data["pwd_hash"]
        self.base_dir = Path(data["base_dir"]).resolve()
        self.temp_dir = Path(data["temp_dir"]).resolve()
        self.temp_dir.mkdir(exist_ok=True)
        # supported file types dict
        tp_dict_fp = template_dir / "tp_dict.json"
        with open(tp_dict_fp) as json_data_file:
            tp_dict: dict[str, dict] = json.load(json_data_file)
        self.ext_dict = {str(ext): (tp, str(data["icon"])) for tp, data in tp_dict.items() for ext in data["exts"]}
        # default settings
        self.default_view = 1
        # define app
        self.app = Flask(
            "streaminghub-curator",
            template_folder=template_dir,
            static_folder=static_dir
        )
        self.app.secret_key = os.urandom(32)
        self.app.config["SESSION_TYPE"] = "filesystem"
        Session(self.app)
        # self.app.logger.handlers = [RichHandler()]
        self.app.logger.setLevel(logging.INFO)
        self.app.logger.info("Your Computer Name is: " + self.hostname)
        self.app.logger.info("Your Computer IP Address is: " + self.IPAddr)

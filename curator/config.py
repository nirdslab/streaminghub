import json
import logging
import socket
from pathlib import Path
import os
from flask import Flask
from flask_fontawesome import FontAwesome


class Config:
    def __init__(self):
        # get host information
        self.hostname = socket.gethostname()
        self.IPAddr = socket.gethostbyname(self.hostname)
        # define app
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(32)
        self.app.logger.setLevel(logging.INFO)
        self.app.logger.info("Your Computer Name is: " + self.hostname)
        self.app.logger.info("Your Computer IP Address is: " + self.IPAddr)
        # FoNT AWESOME
        self.fa = FontAwesome(self.app)
        # Config file
        config_fp = Path(__file__).with_name("config.json")
        with open(config_fp) as json_data_file:
            data = json.load(json_data_file)
        self.hidden_list: list[str] = data["Hidden"]
        self.pwdHash: str = data["pwdHash"]
        self.base_dir = Path(data["rootDir"]).resolve()
        self.temp_dir = Path(data["tempDir"]).resolve()
        self.temp_dir.mkdir(exist_ok=True)
        # supported file types dict
        tp_dict_fp = Path(__file__).with_name("tp_dict.json")
        with open(tp_dict_fp) as json_data_file:
            tp_dict: dict[str, dict] = json.load(json_data_file)
        self.ext_dict = {str(ext): (tp, str(data["icon"])) for tp, data in tp_dict.items() for ext in data["exts"]}
        # default settings
        self.default_view = 1

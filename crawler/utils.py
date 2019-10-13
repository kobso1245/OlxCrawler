import configparser
import os

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = 'config.ini'


def get_config():
    """Retrieve the content of the config file"""
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.join(DIR_PATH, CONFIG_FILE)))
    return config
import configparser
import os

class Config(object):
    def __init__(self, cfg_file):

    	self.cfg_file = cfg_file

    def get(self, section, key):
        config = configparser.ConfigParser()
        file_root = os.path.dirname(__file__)
        path = os.path.join(file_root, self.cfg_file)
        config.read(path)
        return config.get(section, key)

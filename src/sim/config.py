import os
import json
from copy import deepcopy

class ConfigList():

    def __init__(self, directory, filename):
        self._configs = [Config(directory, filename)]
        self._directory = directory
        self._index = 0

    def current(self):
        return self._configs[self._index]

    def copy(self, filename):
        new_config = Config.from_config(self._directory, filename, self._configs[-1].config())
        self._configs.append(new_config)

        return new_config
    
    def pop(self):
        self._configs = self._configs[:-1]

    def set_index(self, index):
        self._index = index

class Config(object):

    def __init__(self, directory, filename):
        self._directory = directory
        self.load(filename)

    @classmethod
    def from_config(cls, directory, filename, config_to_copy):
        obj = cls.__new__(cls)
        super(Config, obj).__init__()
        obj._directory = directory
        obj._filename = obj._add_ext(filename)
        obj._config = deepcopy(config_to_copy)

        return obj

    def filename(self):
        return self._filename

    def save(self, filename):
        self._filename = self._add_ext(filename)
        with open(os.path.join(self._directory, self._filename), "wt") as fid:
            json.dump(self._config, fid, indent=3)

    def load(self, filename):
        self._filename = self._add_ext(filename)
        with open(os.path.join(self._directory, self._filename), "rt") as fid:
            self._config = json.load(fid)
        # need to setText() on all fields of active scenario

    def _add_ext(self, filename):
        base, ext = os.path.splitext(filename)
        if ext == ".json":
            return base + ext
        else:
            return filename + ".json"
        
    def config(self):
        return self._config
        
        

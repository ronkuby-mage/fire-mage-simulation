import os
import json

class ConfigList():

    def __init__(self, directory, filenames):
        self._configs = [Config(directory, filename) for filename in filenames]
        self._filenames = filenames
        self._directory = directory

    def config(self, index):
        return self._configs[index]

class Config():

    def __init__(self, directory, filename):
        self._directory = directory
        self.load(filename)

    def filename(self):
        return self._filename

    def directory(self):
        return self._directory

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
        
        

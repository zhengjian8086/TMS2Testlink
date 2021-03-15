from configparser import ConfigParser


def simple_class(cls):
    _instance = []

    def wapper(*args, **kwargs):
        if not cls in _instance:
            _instance.append(cls(*args, **kwargs))
        return _instance[0]

    return wapper


class MainFUnction:
    def __init__(self):
        self.config = MyConfig()


@simple_class
class MyConfig:
    def __init__(self):
        self.conf = ConfigParser()
        self.conf.read("config.ini")
        self._config = self.create_config()

    def create_config(self):
        config = {}
        for item in self.conf.sections():
            if item == "mapping":
                config[item] = self._get_ini_config_for_mapping(item)
            else:
                config[item] = self._get_ini_config(item)
        return config

    def _get_ini_config(self, sections_name):
        result = {}
        for item in self.conf.items(sections_name):
            result[item[0]] = item[1]
        return result

    def _get_ini_config_for_mapping(self, sections_name):
        result = {}
        for item in self.conf.items(sections_name):
            result[item[0]] = item[1].split("$")
        return result

    def __setitem__(self, key, value):
        self._config[key] = value

    def __getitem__(self, key):
        return self._config[key]


if __name__ == '__main__':
    m=MainFUnction()
    print(m.config["case_info"])

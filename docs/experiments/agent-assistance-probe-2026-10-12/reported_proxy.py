"""Public two-test reproduction from pytest #15099."""


class Config:
    def __init__(self):
        object.__setattr__(self, "_data", {"debug": False})

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self._data[name] = value


cfg = Config()


def test_patch(monkeypatch):
    monkeypatch.setattr(cfg, "debug", True)
    assert cfg.debug is True


def test_restored():
    assert cfg.debug is False

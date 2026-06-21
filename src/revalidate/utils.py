# coding=utf-8

class UniqueDict(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise KeyError(f"duplicate key: {key}")

        super().__setitem__(key, value)

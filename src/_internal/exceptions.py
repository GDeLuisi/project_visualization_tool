class ObjectNotInTreeError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

class PathNotAvailableError(Exception):
    def __init__(self, *args):
        super().__init__(*args)
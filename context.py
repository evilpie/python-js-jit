class Context:
    GLOBAL = 0
    FUNCTION = 1

    def __init__(self, type, scope = None):
        self.type = type
        self.scope = scope
        self.object = {}


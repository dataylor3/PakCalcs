from py_ActionData import ActionData


class LoadCase:
    def __init__(self, id, title, K1, actions: ActionData):
        self.id = id
        self.title = title
        self.K1 = K1
        self.actions = actions

    def __repr__(self):
        return f"<LoadCase {self.id}: {self.title}>"
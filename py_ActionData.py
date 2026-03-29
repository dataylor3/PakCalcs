

class ActionData:
    def __init__(self, x, Mz, My, Vy, Vz, Ax):
        # lists of physicals for a load case, for a member
        self.x = x
        self.Mz = Mz
        self.My = My
        self.Vy = Vy
        self.Vz = Vz
        self.Ax = Ax

    def max_moment(self):
        return max(self.Mz)

    def max_shear(self):
        return max(self.Vy)
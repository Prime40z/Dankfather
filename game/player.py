class Player:
    def __init__(self, user):
        self.user = user
        self.role = None
        self.alive = True
        self.previous_target = None

    def __str__(self):
        return self.user.name

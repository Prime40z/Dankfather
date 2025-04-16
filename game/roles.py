class Role:
    def __init__(self, name, alignment, description):
        self.name = name
        self.alignment = alignment  # Town, Mafia, Neutral
        self.description = description

    def perform_action(self, game, actor, target):
        pass


# Town Roles
class Villager(Role):
    def __init__(self):
        super().__init__("Villager", "Town", "A simple townsperson without any special abilities.")


class Sheriff(Role):
    def __init__(self):
        super().__init__("Sheriff", "Town", "You can investigate one player each night to determine if they are suspicious.")

    def perform_action(self, game, actor, target):
        if target.role.alignment == "Mafia":
            return f"{target.name} is suspicious!"
        return f"{target.name} is not suspicious."


class Doctor(Role):
    def __init__(self):
        super().__init__("Doctor", "Town", "You can heal one player each night, preventing them from dying.")

    def perform_action(self, game, actor, target):
        game.save_player(target)


class Mayor(Role):
    def __init__(self):
        super().__init__("Mayor", "Town", "Your vote counts as 3 during the day phase.")


class Jailor(Role):
    def __init__(self):
        super().__init__("Jailor", "Town", "You can jail one player each night and execute them if necessary.")

    def perform_action(self, game, actor, target):
        game.jail_player(target)


class Bodyguard(Role):
    def __init__(self):
        super().__init__("Bodyguard", "Town", "You can protect one player each night, dying in their place if they are attacked.")

    def perform_action(self, game, actor, target):
        game.protect_player(target, actor)


class Investigator(Role):
    def __init__(self):
        super().__init__("Investigator", "Town", "You can investigate one player each night to learn a clue about their role.")

    def perform_action(self, game, actor, target):
        return f"{target.name} shows signs of being {target.role.name}."


# Add more town roles: Veteran, Vigilante, Escort, Medium, Lookout...


# Mafia Roles
class Godfather(Role):
    def __init__(self):
        super().__init__("Godfather", "Mafia", "You appear innocent to investigators and can order a kill each night.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Mafioso(Role):
    def __init__(self):
        super().__init__("Mafioso", "Mafia", "You carry out the Godfather's orders to kill.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Consigliere(Role):
    def __init__(self):
        super().__init__("Consigliere", "Mafia", "You can investigate one player each night to learn their exact role.")

    def perform_action(self, game, actor, target):
        return f"{target.name} is the {target.role.name}."


# Add more mafia roles: Consort, Framer, Janitor, Blackmailer...


# Neutral Roles
class SerialKiller(Role):
    def __init__(self):
        super().__init__("Serial Killer", "Neutral", "You can kill one player each night and must survive to the end.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Survivor(Role):
    def __init__(self):
        super().__init__("Survivor", "Neutral", "You must survive to the end of the game.")


class Executioner(Role):
    def __init__(self):
        super().__init__("Executioner", "Neutral", "You must get your target lynched during the day.")


class Jester(Role):
    def __init__(self):
        super().__init__("Jester", "Neutral", "You must get yourself lynched during the day to win.")


# Add more neutral roles: Arsonist, Witch...


class RoleFactory:
    ROLES = {
        "Villager": Villager,
        "Sheriff": Sheriff,
        "Doctor": Doctor,
        "Mayor": Mayor,
        "Jailor": Jailor,
        "Bodyguard": Bodyguard,
        "Godfather": Godfather,
        "Mafioso": Mafioso,
        "Consigliere": Consigliere,
        "Serial Killer": SerialKiller,
        "Survivor": Survivor,
        "Executioner": Executioner,
        "Jester": Jester,
        # Add more roles here
    }

    @staticmethod
    def create_role(name):
        role_class = RoleFactory.ROLES.get(name)
        if role_class:
            return role_class()
        return None

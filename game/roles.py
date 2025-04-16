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
        super().__init__("Sheriff", "Town", "Investigate one player each night to determine if they are suspicious.")

    def perform_action(self, game, actor, target):
        if target.role.alignment == "Mafia":
            return f"{target.name} is suspicious!"
        return f"{target.name} is not suspicious."


class Doctor(Role):
    def __init__(self):
        super().__init__("Doctor", "Town", "Heal one player each night, preventing them from dying.")

    def perform_action(self, game, actor, target):
        game.save_player(target)


class Mayor(Role):
    def __init__(self):
        super().__init__("Mayor", "Town", "Your vote counts as 3 during the day phase.")


class Jailor(Role):
    def __init__(self):
        super().__init__("Jailor", "Town", "Jail one player each night and execute them if necessary.")

    def perform_action(self, game, actor, target):
        game.jail_player(target)


class Bodyguard(Role):
    def __init__(self):
        super().__init__("Bodyguard", "Town", "Protect one player each night, dying in their place if they are attacked.")

    def perform_action(self, game, actor, target):
        game.protect_player(target, actor)


class Investigator(Role):
    def __init__(self):
        super().__init__("Investigator", "Town", "Investigate one player each night to learn a clue about their role.")

    def perform_action(self, game, actor, target):
        return f"{target.name} shows signs of being {target.role.name}."


class Veteran(Role):
    def __init__(self):
        super().__init__("Veteran", "Town", "Go on alert to kill anyone who visits you during the night.")


class Vigilante(Role):
    def __init__(self):
        super().__init__("Vigilante", "Town", "Kill one player at night. Be careful not to kill a fellow town member!")


class Escort(Role):
    def __init__(self):
        super().__init__("Escort", "Town", "Distract one player each night, preventing them from acting.")

    def perform_action(self, game, actor, target):
        game.block_player(target)


class Medium(Role):
    def __init__(self):
        super().__init__("Medium", "Town", "Communicate with dead players during the night.")


class Lookout(Role):
    def __init__(self):
        super().__init__("Lookout", "Town", "Watch one player's house to see who visits them at night.")

    def perform_action(self, game, actor, target):
        visitors = game.get_visitors(target)
        return f"{target.name} was visited by {', '.join([v.name for v in visitors])}."


# Mafia Roles
class Godfather(Role):
    def __init__(self):
        super().__init__("Godfather", "Mafia", "Order a kill each night and appear innocent to investigators.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Mafioso(Role):
    def __init__(self):
        super().__init__("Mafioso", "Mafia", "Carry out the Godfather's orders to kill.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Consigliere(Role):
    def __init__(self):
        super().__init__("Consigliere", "Mafia", "Investigate one player each night to learn their exact role.")

    def perform_action(self, game, actor, target):
        return f"{target.name} is the {target.role.name}."


class Consort(Role):
    def __init__(self):
        super().__init__("Consort", "Mafia", "Distract one player each night, preventing them from acting.")

    def perform_action(self, game, actor, target):
        game.block_player(target)


class Framer(Role):
    def __init__(self):
        super().__init__("Framer", "Mafia", "Make one player appear suspicious to investigators.")

    def perform_action(self, game, actor, target):
        game.frame_player(target)


class Janitor(Role):
    def __init__(self):
        super().__init__("Janitor", "Mafia", "Clean a player's role upon their death to hide it from others.")

    def perform_action(self, game, actor, target):
        game.clean_player(target)


class Blackmailer(Role):
    def __init__(self):
        super().__init__("Blackmailer", "Mafia", "Silence one player during the day, preventing them from speaking.")

    def perform_action(self, game, actor, target):
        game.silence_player(target)


# Neutral Roles
class SerialKiller(Role):
    def __init__(self):
        super().__init__("Serial Killer", "Neutral", "Kill one player each night. Survive to the end.")

    def perform_action(self, game, actor, target):
        game.kill_player(target)


class Survivor(Role):
    def __init__(self):
        super().__init__("Survivor", "Neutral", "Survive until the end of the game.")


class Executioner(Role):
    def __init__(self):
        super().__init__("Executioner", "Neutral", "Get your target lynched during the day.")


class Jester(Role):
    def __init__(self):
        super().__init__("Jester", "Neutral", "Get yourself lynched during the day to win.")


class Arsonist(Role):
    def __init__(self):
        super().__init__("Arsonist", "Neutral", "Douse players in gasoline and ignite them at night.")

    def perform_action(self, game, actor, target):
        game.douse_player(target)


class Witch(Role):
    def __init__(self):
        super().__init__("Witch", "Neutral", "Control one player each night and force them to act on another.")

    def perform_action(self, game, actor, target, secondary_target):
        game.control_player(target, secondary_target)


class RoleFactory:
    ROLES = {
        "Villager": Villager,
        "Sheriff": Sheriff,
        "Doctor": Doctor,
        "Mayor": Mayor,
        "Jailor": Jailor,
        "Bodyguard": Bodyguard,
        "Investigator": Investigator,
        "Veteran": Veteran,
        "Vigilante": Vigilante,
        "Escort": Escort,
        "Medium": Medium,
        "Lookout": Lookout,
        "Godfather": Godfather,
        "Mafioso": Mafioso,
        "Consigliere": Consigliere,
        "Consort": Consort,
        "Framer": Framer,
        "Janitor": Janitor,
        "Blackmailer": Blackmailer,
        "Serial Killer": SerialKiller,
        "Survivor": Survivor,
        "Executioner": Executioner,
        "Jester": Jester,
        "Arsonist": Arsonist,
        "Witch": Witch,
    }

    @staticmethod
    def create_role(name):
        role_class = RoleFactory.ROLES.get(name)
        if role_class:
            return role_class()
        return None

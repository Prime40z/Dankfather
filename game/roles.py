class Role:
    def __init__(self, name, has_night_action=False):
        self.name = name
        self.has_night_action = has_night_action
        self.previous_target = None  # Used for roles like Doctor

    def __str__(self):
        return self.name


# Example roles with diverse abilities
class Mafia(Role):
    def __init__(self):
        super().__init__(name="Mafia", has_night_action=True)

    def valid_targets(self, players):
        """Mafia can't target other Mafia members."""
        return [player for player in players if player.role.name != "Mafia" and player.alive]


class Doctor(Role):
    def __init__(self):
        super().__init__(name="Doctor", has_night_action=True)

    def valid_targets(self, players):
        """Doctor can target any living player except the one they healed last."""
        return [player for player in players if player.alive and player != self.previous_target]


class Villager(Role):
    def __init__(self):
        super().__init__(name="Villager", has_night_action=False)


class Detective(Role):
    def __init__(self):
        super().__init__(name="Detective", has_night_action=True)

    def valid_targets(self, players):
        """Detective can investigate any living player."""
        return [player for player in players if player.alive]


class Jester(Role):
    def __init__(self):
        super().__init__(name="Jester", has_night_action=False)


class SerialKiller(Role):
    def __init__(self):
        super().__init__(name="Serial Killer", has_night_action=True)

    def valid_targets(self, players):
        """Serial Killer can target any living player."""
        return [player for player in players if player.alive]


class Bodyguard(Role):
    def __init__(self):
        super().__init__(name="Bodyguard", has_night_action=True)

    def valid_targets(self, players):
        """Bodyguard can protect any living player."""
        return [player for player in players if player.alive]


class Spy(Role):
    def __init__(self):
        super().__init__(name="Spy", has_night_action=True)

    def valid_targets(self, players):
        """Spy can eavesdrop on any living player."""
        return [player for player in players if player.alive]


class Witch(Role):
    def __init__(self):
        super().__init__(name="Witch", has_night_action=True)

    def valid_targets(self, players):
        """Witch can control any living player."""
        return [player for player in players if player.alive]


class Arsonist(Role):
    def __init__(self):
        super().__init__(name="Arsonist", has_night_action=True)

    def valid_targets(self, players):
        """Arsonist can douse any living player."""
        return [player for player in players if player.alive]


class Mayor(Role):
    def __init__(self):
        super().__init__(name="Mayor", has_night_action=False)


class Veteran(Role):
    def __init__(self):
        super().__init__(name="Veteran", has_night_action=True)


class Escort(Role):
    def __init__(self):
        super().__init__(name="Escort", has_night_action=True)

    def valid_targets(self, players):
        """Escort can block any living player."""
        return [player for player in players if player.alive]


class Consort(Role):
    def __init__(self):
        super().__init__(name="Consort", has_night_action=True)

    def valid_targets(self, players):
        """Consort can block any living player."""
        return [player for player in players if player.alive]


class Framer(Role):
    def __init__(self):
        super().__init__(name="Framer", has_night_action=True)

    def valid_targets(self, players):
        """Framer can frame any living player."""
        return [player for player in players if player.alive]


class Forger(Role):
    def __init__(self):
        super().__init__(name="Forger", has_night_action=True)

    def valid_targets(self, players):
        """Forger can forge evidence against any living player."""
        return [player for player in players if player.alive]


class Executioner(Role):
    def __init__(self):
        super().__init__(name="Executioner", has_night_action=False)


class Survivor(Role):
    def __init__(self):
        super().__init__(name="Survivor", has_night_action=False)


class Amnesiac(Role):
    def __init__(self):
        super().__init__(name="Amnesiac", has_night_action=True)

    def valid_targets(self, players):
        """Amnesiac can remember the role of any dead player."""
        return [player for player in players if not player.alive]


class Blackmailer(Role):
    def __init__(self):
        super().__init__(name="Blackmailer", has_night_action=True)

    def valid_targets(self, players):
        """Blackmailer can silence any living player."""
        return [player for player in players if player.alive]


class Disguiser(Role):
    def __init__(self):
        super().__init__(name="Disguiser", has_night_action=True)

    def valid_targets(self, players):
        """Disguiser can disguise as any living player."""
        return [player for player in players if player.alive]


class Godfather(Role):
    def __init__(self):
        super().__init__(name="Godfather", has_night_action=True)

    def valid_targets(self, players):
        """Godfather can command Mafia to target any living player."""
        return [player for player in players if player.alive]


class Tracker(Role):
    def __init__(self):
        super().__init__(name="Tracker", has_night_action=True)

    def valid_targets(self, players):
        """Tracker can follow any living player."""
        return [player for player in players if player.alive]


class Lookout(Role):
    def __init__(self):
        super().__init__(name="Lookout", has_night_action=True)

    def valid_targets(self, players):
        """Lookout can watch over any living player."""
        return [player for player in players if player.alive]


class Vigilante(Role):
    def __init__(self):
        super().__init__(name="Vigilante", has_night_action=True)

    def valid_targets(self, players):
        """Vigilante can shoot any living player."""
        return [player for player in players if player.alive]


# Add more roles as necessary
ROLES = [
    Mafia(), Doctor(), Villager(), Detective(), Jester(), SerialKiller(),
    Bodyguard(), Spy(), Witch(), Arsonist(), Mayor(), Veteran(),
    Escort(), Consort(), Framer(), Forger(), Executioner(), Survivor(),
    Amnesiac(), Blackmailer(), Disguiser(), Godfather(), Tracker(),
    Lookout(), Vigilante()
]

class GamePlayer(db.Model):
    __tablename__ = 'game_players'

    id = db.Column(db.Integer, primary_key=True)
    # other fields here

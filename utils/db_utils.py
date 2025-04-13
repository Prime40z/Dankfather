"""
Database utility functions for the Mafia Discord bot.
"""
import logging
from datetime import datetime

from models import db, Guild, Player, Game, GamePlayer

logger = logging.getLogger('mafia_bot.db')

def get_or_create_guild(guild):
    """
    Get or create a Guild record.
    
    Args:
        guild: Discord guild object
    
    Returns:
        Guild: Database Guild object
    """
    db_guild = Guild.query.get(guild.id)
    if not db_guild:
        db_guild = Guild(id=guild.id, name=guild.name)
        db.session.add(db_guild)
        db.session.commit()
        logger.info(f"Created new guild record for {guild.name} ({guild.id})")
    return db_guild

def get_or_create_player(member):
    """
    Get or create a Player record.
    
    Args:
        member: Discord member object
    
    Returns:
        Player: Database Player object
    """
    db_player = Player.query.get(member.id)
    if not db_player:
        db_player = Player(
            id=member.id,
            name=member.display_name,
            discriminator=member.discriminator if hasattr(member, 'discriminator') else None
        )
        db.session.add(db_player)
        db.session.commit()
        logger.info(f"Created new player record for {member.display_name} ({member.id})")
    else:
        # Update the player's name if it changed
        if db_player.name != member.display_name:
            db_player.name = member.display_name
            db.session.commit()
    return db_player

def create_game_record(game_session):
    """
    Create a Game record for a new game.
    
    Args:
        game_session: GameSession object
    
    Returns:
        Game: Database Game object
    """
    guild = get_or_create_guild(game_session.channel.guild)
    
    # Create the game record
    db_game = Game(
        guild_id=guild.id,
        channel_id=game_session.channel.id,
        num_players=len(game_session.players),
        num_mafia=sum(1 for p in game_session.players if p.role.name == "Mafia"),
        num_town=sum(1 for p in game_session.players if p.role.name != "Mafia"),
        start_time=datetime.utcnow()
    )
    db.session.add(db_game)
    db.session.commit()
    
    # Add each player to the game
    for player in game_session.players:
        db_player = get_or_create_player(player.member)
        
        # Increment role count
        if player.role.name == "Mafia":
            db_player.times_mafia += 1
        elif player.role.name == "Detective":
            db_player.times_detective += 1
        elif player.role.name == "Doctor":
            db_player.times_doctor += 1
        elif player.role.name == "Villager":
            db_player.times_villager += 1
        
        # Create the game player record
        game_player = GamePlayer(
            game_id=db_game.id,
            player_id=db_player.id,
            role=player.role.name.lower(),
            was_host=(player.member.id == game_session.host.id)
        )
        db.session.add(game_player)
    
    db.session.commit()
    logger.info(f"Created new game record {db_game.id} in {guild.name}")
    return db_game

def end_game_record(game_session, db_game, winner):
    """
    Update a Game record when the game ends.
    
    Args:
        game_session: GameSession object
        db_game: Database Game object
        winner: String, 'town' or 'mafia'
    """
    # Update game record
    db_game.end_time = datetime.utcnow()
    db_game.days_lasted = game_session.day_num
    db_game.winner = winner
    
    # Update player records
    for player in game_session.players:
        db_player = Player.query.get(player.member.id)
        if db_player:
            # Update games played
            db_player.games_played += 1
            
            # Update wins
            player_alignment = "mafia" if player.role.name == "Mafia" else "town"
            if player_alignment == winner:
                db_player.games_won += 1
            
            # Update survival status
            game_player = GamePlayer.query.filter_by(
                game_id=db_game.id,
                player_id=player.member.id
            ).first()
            if game_player:
                game_player.survived = player.alive
    
    db.session.commit()
    logger.info(f"Updated game record {db_game.id} with winner: {winner}")

def get_player_stats(member):
    """
    Get a player's statistics.
    
    Args:
        member: Discord member object
    
    Returns:
        dict: Dictionary of player statistics
    """
    db_player = Player.query.get(member.id)
    if not db_player:
        return None
    
    # Get roles count
    roles_count = {
        'mafia': db_player.times_mafia,
        'detective': db_player.times_detective,
        'doctor': db_player.times_doctor,
        'villager': db_player.times_villager
    }
    
    # Get win rate
    win_rate = db_player.win_rate
    
    # Get recent games
    recent_games = GamePlayer.query.filter_by(player_id=member.id)\
        .join(Game)\
        .order_by(Game.start_time.desc())\
        .limit(5)\
        .all()
    
    return {
        'name': db_player.name,
        'games_played': db_player.games_played,
        'games_won': db_player.games_won,
        'win_rate': win_rate,
        'roles_count': roles_count,
        'recent_games': recent_games
    }

def register_guild_if_new(guild):
    """
    Register a guild in the database if it's not already present.
    Used when bot joins a new server.
    
    Args:
        guild: Discord guild object
    """
    get_or_create_guild(guild)
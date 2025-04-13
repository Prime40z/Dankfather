"""
Main entry point for the Discord Mafia bot.
Includes a simple Flask web interface for monitoring and database storage.
"""
import os
import asyncio
import logging
import threading
import discord
from flask import Flask, render_template_string
from bot import MafiaBot
from models import db, Guild, Player, Game, GamePlayer

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create the Flask app
app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

# Initialize the database with the app
db.init_app(app)

# Create all tables if they don't exist
with app.app_context():
    db.create_all()

# Create the bot instance
bot = MafiaBot()

# Get the bot token from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Bot status for web interface
bot_status = {
    "is_running": False,
    "guilds": 0,
    "active_games": 0,
    "last_error": None
}

# HTML template for the status page
STATUS_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mafia Bot Status</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            color: #2f5c8f;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .status {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .running {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .stopped {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        .info-box {
            background-color: #e2e3e5;
            border: 1px solid #d6d8db;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        footer {
            margin-top: 30px;
            font-size: 0.8em;
            text-align: center;
            color: #777;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }
    </style>
</head>
<body>
    <h1>🎭 Mafia Discord Bot</h1>
    
    <div class="status {{ 'running' if is_running else 'stopped' }}">
        Status: {{ 'Running' if is_running else 'Stopped' }}
    </div>
    
    <div class="info-box">
        <h3>Bot Information</h3>
        <ul>
            <li>Connected Servers: {{ guilds }}</li>
            <li>Active Games: {{ active_games }}</li>
            {% if last_error %}
            <li>Last Error: {{ last_error }}</li>
            {% endif %}
        </ul>
    </div>
    
    <div class="info-box">
        <h3>Commands</h3>
        <ul>
            <li><code>!mafia help</code> - Show help information</li>
            <li><code>!mafia create</code> - Create a new game</li>
            <li><code>!mafia join</code> - Join a game</li>
            <li><code>!mafia start</code> - Start a game</li>
            <li><code>!mafia vote</code> - Vote during day phase</li>
            <li><code>!mafia action</code> - Use night action</li>
        </ul>
    </div>
    
    <footer>
        &copy; 2025 Mafia Discord Bot
    </footer>
</body>
</html>
"""

@app.route('/')
def home():
    """Display bot status information."""
    bot_status["active_games"] = len(bot.active_games) if hasattr(bot, 'active_games') else 0
    return render_template_string(STATUS_PAGE, 
        is_running=bot_status["is_running"],
        guilds=bot_status["guilds"],
        active_games=bot_status["active_games"],
        last_error=bot_status["last_error"]
    )

@app.route('/stats')
def stats():
    """Display game statistics."""
    try:
        total_games = Game.query.count()
        total_players = Player.query.count()
        mafia_wins = Game.query.filter_by(winner='mafia').count()
        town_wins = Game.query.filter_by(winner='town').count()
        
        recent_games = Game.query.order_by(Game.start_time.desc()).limit(5).all()
        
        top_players = Player.query.order_by(Player.games_won.desc()).limit(5).all()
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mafia Bot Statistics</title>
            <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        </head>
        <body>
            <div class="container mt-4">
                <h1>🎭 Mafia Game Statistics</h1>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h3>Game Statistics</h3>
                            </div>
                            <div class="card-body">
                                <p>Total Games: {{ total_games }}</p>
                                <p>Total Players: {{ total_players }}</p>
                                <p>Mafia Wins: {{ mafia_wins }}</p>
                                <p>Town Wins: {{ town_wins }}</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h3>Top Players</h3>
                            </div>
                            <div class="card-body">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Player</th>
                                            <th>Games Played</th>
                                            <th>Win Rate</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for player in top_players %}
                                        <tr>
                                            <td>{{ player.name }}</td>
                                            <td>{{ player.games_played }}</td>
                                            <td>{{ player.win_rate }}%</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mt-4">
                    <div class="card-header">
                        <h3>Recent Games</h3>
                    </div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Server</th>
                                    <th>Date</th>
                                    <th>Players</th>
                                    <th>Winner</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for game in recent_games %}
                                <tr>
                                    <td>{{ game.guild.name }}</td>
                                    <td>{{ game.start_time.strftime('%Y-%m-%d') }}</td>
                                    <td>{{ game.num_players }}</td>
                                    <td>{{ game.winner|capitalize }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <a href="/" class="btn btn-primary mt-3">Back to Status</a>
            </div>
        </body>
        </html>
        """, 
        total_games=total_games,
        total_players=total_players,
        mafia_wins=mafia_wins,
        town_wins=town_wins,
        recent_games=recent_games,
        top_players=top_players
        )
    except Exception as e:
        return f"Error loading statistics: {str(e)}"

@app.route('/players')
def players():
    """Display player information."""
    try:
        all_players = Player.query.order_by(Player.games_played.desc()).all()
        
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mafia Bot Players</title>
            <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        </head>
        <body>
            <div class="container mt-4">
                <h1>🎭 Mafia Players</h1>
                
                <div class="card">
                    <div class="card-header">
                        <h3>All Players</h3>
                    </div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Player</th>
                                    <th>Games</th>
                                    <th>Wins</th>
                                    <th>Win Rate</th>
                                    <th>Mafia</th>
                                    <th>Detective</th>
                                    <th>Doctor</th>
                                    <th>Villager</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for player in all_players %}
                                <tr>
                                    <td>{{ player.name }}</td>
                                    <td>{{ player.games_played }}</td>
                                    <td>{{ player.games_won }}</td>
                                    <td>{{ player.win_rate }}%</td>
                                    <td>{{ player.times_mafia }}</td>
                                    <td>{{ player.times_detective }}</td>
                                    <td>{{ player.times_doctor }}</td>
                                    <td>{{ player.times_villager }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <a href="/" class="btn btn-primary mt-3">Back to Status</a>
                <a href="/stats" class="btn btn-secondary mt-3">View Statistics</a>
            </div>
        </body>
        </html>
        """, all_players=all_players)
    except Exception as e:
        return f"Error loading player information: {str(e)}"

# Run the bot
async def run_bot():
    """Start the Discord bot."""
    if not TOKEN:
        logging.error("No Discord token found in environment variables. Please set the DISCORD_TOKEN environment variable.")
        bot_status["last_error"] = "Missing Discord token"
        return
        
    try:
        bot_status["is_running"] = True
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        logging.error("Invalid Discord token. Please check your DISCORD_TOKEN environment variable.")
        bot_status["last_error"] = "Invalid Discord token"
    except Exception as e:
        logging.error(f"Error starting bot: {e}")
        bot_status["last_error"] = str(e)
    finally:
        bot_status["is_running"] = False

def start_bot_in_thread():
    """Start the bot in a separate thread."""
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.get_event_loop().run_until_complete(run_bot())

# Create a function to start the bot thread
def start_bot_thread():
    """Start the bot thread."""
    thread = threading.Thread(target=start_bot_in_thread)
    thread.daemon = True
    thread.start()
    logging.info("Started Discord bot in background thread")

# Create a startup route to trigger the bot startup
@app.route('/start-bot')
def start_bot_route():
    """Route to start the bot thread."""
    if not bot_status["is_running"]:
        start_bot_thread()
        return "Bot started"
    return "Bot is already running"
    
# Use with_appcontext to start the bot when the app is initialized
with app.app_context():
    # Start the bot when the application is initialized
    start_bot_thread()

# Updates for the bot to communicate status
async def on_ready_update():
    """Update status when bot is ready."""
    bot_status["guilds"] = len(bot.guilds)
    logging.info(f"Bot connected to {bot_status['guilds']} guilds")

# Add the update function to the bot's on_ready callback
original_on_ready = bot.on_ready

async def enhanced_on_ready():
    """Enhanced on_ready with status updates."""
    await original_on_ready()
    await on_ready_update()

bot.on_ready = enhanced_on_ready

# Direct execution - start both Flask and bot
if __name__ == "__main__":
    # Start the bot in a background thread
    bot_thread = threading.Thread(target=start_bot_in_thread)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Run the Flask app (if this script is called directly)
    app.run(host="0.0.0.0", port=5000, debug=False)
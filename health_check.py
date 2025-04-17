import asyncio
from aiohttp import web

async def health_check(request):
    """Respond to health check requests."""
    return web.Response(text="OK")

def start_health_check_server():
    """Start a lightweight HTTP server for health checks."""
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    loop.run_until_complete(site.start())

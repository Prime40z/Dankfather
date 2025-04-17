import asyncio
from aiohttp import web

async def health_check(request):
    """Respond to health check requests."""
    return web.Response(text="OK")

async def start_health_check_server():
    """Start a lightweight HTTP server for health checks."""
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Health check server started on http://0.0.0.0:8080")
    return runner, site  # Return these so they don't get garbage collected

"""MCP Tool: health_check for DesktopCommander."""
import json


def register_health_check(mcp):
    @mcp.tool()
    async def health_check():
        """Check DesktopCommander health status."""
        from surfaces.mcp_desktop_client import _get_client, _desktop_commander_client
        try:
            client = _get_client()
            result = await client.health_check()
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "protocol": _desktop_commander_client.protocol if _desktop_commander_client else "Unknown"
            })

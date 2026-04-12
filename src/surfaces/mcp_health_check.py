"""MCP Tool: health_check for DesktopCommander."""
import json


def register_health_check(mcp):
    @mcp.tool()
    async def health_check():
        """Check DesktopCommander health status."""
        from surfaces.mcp_desktop_client import _get_client
        try:
            client = _get_client()
            result = await client.health_check()
            result["protocol"] = client.protocol or "Unknown"
            return json.dumps(result)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "protocol": "Unknown"
            })

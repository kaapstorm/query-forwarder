"""Quart web application for query-forwarder."""
import asyncio
import json

from quart import Quart, render_template, websocket
from sqlalchemy import select

from query_forwarder.database import get_session
from query_forwarder.models import APILog

app = Quart(__name__)


@app.route("/")
async def index():
    """Display list of API logs with live updates."""
    async with get_session() as session:
        result = await session.execute(
            select(APILog).order_by(APILog.timestamp.desc()).limit(100)
        )
        logs = result.scalars().all()
    return await render_template("index.html", logs=logs)


@app.route("/log/<int:log_id>")
async def log_detail(log_id: int):
    """Display details of a specific API log entry."""
    async with get_session() as session:
        result = await session.execute(select(APILog).where(APILog.id == log_id))
        log = result.scalar_one_or_none()

        if not log:
            return "Log not found", 404

    return await render_template("detail.html", log=log)


@app.websocket("/ws/logs")
async def ws_logs():
    """WebSocket endpoint for live log updates."""
    last_id = 0

    while True:
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(APILog)
                    .where(APILog.id > last_id)
                    .order_by(APILog.id.asc())
                )
                new_logs = result.scalars().all()

                if new_logs:
                    for log in new_logs:
                        await websocket.send(
                            json.dumps(
                                {
                                    "id": log.id,
                                    "timestamp": log.timestamp.isoformat(),
                                    "request_url": log.request_url,
                                    "response_status_code": log.response_status_code,
                                }
                            )
                        )
                        last_id = log.id

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"WebSocket error: {e}")
            break


if __name__ == "__main__":
    app.run(debug=True)

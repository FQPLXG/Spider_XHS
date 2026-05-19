import json
import os
from urllib.parse import parse_qs

from aiohttp import web
from loguru import logger

from apis.xhs_pc_apis import XHS_Apis
from xhs_utils.common_util import load_env


def _json_response(payload: dict, status: int = 200) -> web.Response:
    return web.Response(
        text=json.dumps(payload, ensure_ascii=False),
        status=status,
        content_type="application/json",
    )


async def health(_: web.Request) -> web.Response:
    return _json_response({"ok": True, "service": "xhs-comment-crawler"})


async def comments(request: web.Request) -> web.Response:
    token = os.getenv("COMMENT_API_TOKEN", "")
    if token:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            return _json_response({"ok": False, "msg": "unauthorized"}, status=401)

    query = parse_qs(request.rel_url.query_string)
    note_url = (query.get("note_url") or [""])[0].strip()

    if not note_url:
        return _json_response({"ok": False, "msg": "missing note_url"}, status=400)

    cookies_str = os.getenv("COOKIES") or load_env()

    if not cookies_str:
        return _json_response({"ok": False, "msg": "missing COOKIES env"}, status=400)

    api = XHS_Apis()
    success, msg, data = api.get_note_all_comment(note_url, cookies_str)

    status = 200 if success else 502
    return _json_response({"ok": success, "msg": str(msg), "data": data}, status=status)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/comments", comments)
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    logger.info(f"Starting comment service on 0.0.0.0:{port}")
    web.run_app(create_app(), host="0.0.0.0", port=port)

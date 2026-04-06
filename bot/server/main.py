from quart import Blueprint, Response, request, render_template, redirect
from math import ceil
from re import match as re_match
import base64
import mimetypes
from .error import abort
from bot import TelegramBot
from bot.config import Telegram, Server
from bot.modules.telegram import get_message, get_file_properties

bp = Blueprint('main', __name__)

# --- CONFIGURATION (Ensure domains are correct) ---
ALLOWED_WEBSITES = [
    "heyswan.love", 
    "heyswan.site", 
    "moviesworld.com", 
    "filmypunjab.net"
]

@bp.route('/')
async def home():
    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}')

@bp.route('/dl/<int:file_id>')
async def transmit_file(file_id):
    # --- STRICT REFERER SECURITY ---
    bot_domain = request.host
    referer = request.headers.get("Referer") or request.headers.get("Origin") or ""
    
    if not referer:
        return abort(403, "Direct access is prohibited.")
    
    is_allowed = any(site in referer for site in ALLOWED_WEBSITES)
    if not is_allowed and bot_domain not in referer:
        return abort(403, "Unauthorized Domain.")

    file = await get_message(file_id) or abort(404)
    code = request.args.get('code') or abort(401)
    range_header = request.headers.get('Range')

    if code != file.caption.split('/')[0]:
        abort(403)

    file_name, file_size, mime_type = get_file_properties(file)
    
    # FIX: Force correct MIME Type for HQ Playback
    if not mime_type or 'octet-stream' in mime_type:
        mime_guess = mimetypes.guess_type(file_name)[0]
        mime_type = mime_guess if mime_guess else 'video/mp4'
    
    # MKV compatibility fix for browsers
    if file_name.endswith('.mkv') and 'video' not in mime_type:
        mime_type = 'video/webm' # Browsers often play MKV as webm tech

    start, end = 0, file_size - 1
    chunk_size = 2 * 1024 * 1024 # 2MB chunking for stability

    if range_header:
        range_match = re_match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            if start > end or start >= file_size:
                abort(416, 'Requested range not satisfiable')

    content_length = end - start + 1
    headers = {
        'Content-Type': mime_type,
        'Content-Disposition': f'inline; filename="{file_name}"',
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(content_length),
        'Access-Control-Allow-Origin': '*',
        'X-Content-Type-Options': 'nosniff',
    }
    status_code = 206 if range_header else 200

    async def file_stream():
        bytes_streamed = 0
        offset_chunks = start // (1024 * 1024) 
        async for chunk in TelegramBot.stream_media(file, offset=offset_chunks):
            if bytes_streamed == 0:
                trim = start % (1024 * 1024)
                if trim > 0: chunk = chunk[trim:]
            remaining = content_length - bytes_streamed
            if remaining <= 0: break
            if len(chunk) > remaining: chunk = chunk[:remaining]
            yield chunk
            bytes_streamed += len(chunk)

    return Response(file_stream(), headers=headers, status=status_code)

@bp.route('/stream/<int:file_id>')
async def stream_file(file_id):
    # --- PLAYER SECURITY ---
    bot_domain = request.host
    referer = request.headers.get("Referer") or request.headers.get("Origin") or ""
    if not referer: return abort(403)
    is_allowed = any(site in referer for site in ALLOWED_WEBSITES)
    if not is_allowed and bot_domain not in referer: return abort(403)

    code = request.args.get('code') or abort(401)
    original_link = f'{Server.BASE_URL}/dl/{file_id}?code={code}'
    masked_token = base64.b64encode(original_link.encode("utf-8")).decode("utf-8")
    
    return await render_template('player.html', token=masked_token)

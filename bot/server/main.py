from quart import Blueprint, Response, request, render_template, redirect
from math import ceil
from re import match as re_match
import base64
from .error import abort
from bot import TelegramBot
from bot.config import Telegram, Server
from bot.modules.telegram import get_message, get_file_properties

bp = Blueprint('main', __name__)

# --- CONFIGURATION (Apne 4 Domains Yahan Dalein) ---
ALLOWED_WEBSITES = [
    "heyswan.love", 
    "moviesworld.com", 
    "filmypunjab.net", 
    "bollyshow.org"
]

@bp.route('/')
async def home():
    return redirect(f'https://t.me/{Telegram.BOT_USERNAME}')

@bp.route('/dl/<int:file_id>')
async def transmit_file(file_id):
    # --- STRICT REFERER SECURITY ---
    bot_domain = request.host
    referer = request.headers.get("Referer") or request.headers.get("Origin") or ""
    
    # 1. Direct access block (Referer check)
    if not referer:
        return abort(403, "Direct access is strictly prohibited.")
    
    # 2. Check if referer is in allowed list
    is_allowed = any(site in referer for site in ALLOWED_WEBSITES)
    if not is_allowed and bot_domain not in referer:
        return abort(403, "Unauthorized Domain Access.")

    # --- TRANSMIT LOGIC ---
    file = await get_message(file_id) or abort(404)
    code = request.args.get('code') or abort(401)
    range_header = request.headers.get('Range')

    if code != file.caption.split('/')[0]:
        abort(403)

    file_name, file_size, mime_type = get_file_properties(file)
    start, end = 0, file_size - 1
    chunk_size = 1 * 1024 * 1024 

    if range_header:
        range_match = re_match(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
            if start > end or start >= file_size:
                abort(416, 'Requested range not satisfiable')

    offset_chunks = start // chunk_size
    total_bytes_to_stream = end - start + 1
    chunks_to_stream = ceil(total_bytes_to_stream / chunk_size)

    headers = {
        'Content-Type': mime_type,
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(total_bytes_to_stream),
        'X-Content-Type-Options': 'nosniff',
        'Access-Control-Allow-Origin': '*', # Allows player to fetch data
    }
    status_code = 206 if range_header else 200

    async def file_stream():
        bytes_streamed = 0
        chunk_index = 0
        async for chunk in TelegramBot.stream_media(file, offset=offset_chunks, limit=chunks_to_stream):
            if chunk_index == 0: 
                trim_start = start % chunk_size
                if trim_start > 0: chunk = chunk[trim_start:]
            remaining_bytes = total_bytes_to_stream - bytes_streamed
            if remaining_bytes <= 0: break
            if len(chunk) > remaining_bytes: chunk = chunk[:remaining_bytes]
            yield chunk
            bytes_streamed += len(chunk)
            chunk_index += 1

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
    
    # ORIGINAL LINK ENCRYPTION
    original_link = f'{Server.BASE_URL}/dl/{file_id}?code={code}'
    masked_token = base64.b64encode(original_link.encode("utf-8")).decode("utf-8")
    
    return await render_template('player.html', token=masked_token)

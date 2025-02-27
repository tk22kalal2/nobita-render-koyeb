from quart import Quart, jsonify, request
from database import Database
from bot.telegram_bot import process_telegram_link
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Quart(__name__)
db = Database(os.getenv("DATABASE_URL"))

@app.route('/process', methods=['POST', 'OPTIONS'])
async def process_link():
    if request.method == 'OPTIONS':
        return '', 200  # Handle CORS preflight
    
    data = await request.get_json()
    telegram_link = data['telegram_link']
    lecture_name = data['lecture_name']
    
    logger.info(f"Processing link: {telegram_link} for lecture: {lecture_name}")
    
    # Check if already processed
    existing = await db.get_stream_link(lecture_name)
    if existing and existing != "pending":
        logger.info(f"Link already exists: {existing}")
        return jsonify({"stream_link": existing})
    
    # Trigger bot processing
    await db.insert_file(
        file_name=lecture_name,
        telegram_link=telegram_link,
        stream_link="pending"
    )
    
    # Start background task
    stream_link = await process_telegram_link(telegram_link, lecture_name)
    
    logger.info(f"Generated stream link: {stream_link}")
    return jsonify({"stream_link": stream_link})

@app.route('/check-status/<lecture_name>')
async def check_status(lecture_name):
    link = await db.get_stream_link(lecture_name)
    logger.info(f"Checking status for {lecture_name}: {link}")
    return jsonify({"stream_link": link or "pending"})

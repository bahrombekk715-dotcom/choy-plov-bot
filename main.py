import asyncio
import uvicorn
from multiprocessing import Process
from bot import main as bot_main
from webapp import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """Bot processini ishga tushirish"""
    asyncio.run(bot_main())

def run_web():
    """Web server processini ishga tushirish"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    logger.info("Starting Choy Plov Bot & Web App...")

    # Bot va Web serverni parallel ishga tushirish
    bot_process = Process(target=run_bot)
    web_process = Process(target=run_web)

    bot_process.start()
    web_process.start()

    logger.info("Bot and Web App are running!")

    try:
        bot_process.join()
        web_process.join()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        bot_process.terminate()
        web_process.terminate()
        bot_process.join()
        web_process.join()
        logger.info("Stopped!")

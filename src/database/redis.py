import redis.asyncio as redis
from src.conf.config import config

redis_db = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=0,
    decode_responses=True,
)
import asyncio
from bilibili_api import live, user, Credential
import aioredis
import json
import os
import logging

# 你的凭证信息，参照bilibili_api的文档
CREDENTIAL = Credential(sessdata= "############",
                            bili_jct="############", 
                            buvid3="############")

# 一些Constant
follower_add = 10
club_add = 10
base_count = 2

# 连接redis
async def connect_to_redis():
    pool = aioredis.ConnectionPool.from_url("redis://ip:port/0", encoding="utf-8", decode_responses=True)
    client = aioredis.Redis(connection_pool=pool)
    await client.set("my-key", "value")
    value = await client.get("my-key")
    print(value)
    return client

#F 发送到ChatGPT redis队列
async def save_danmaku_to_redis(redis, queue_name, user_id, username, avatar_url, message, is_admin):
    danmaku_data = {
        'user_id': user_id,
        'username': username,
        'avatar_url': avatar_url,
        'message': message,
        'is_admin': is_admin
    }
    res = await redis.lpush(queue_name, json.dumps(danmaku_data))
    print(res)

#F 存入头像、用户名到redis
async def save_user_to_redis(redis,  user_id, username, avatar_url):
    await redis.hset(f"userinfo:{user_id}", 'username', username)
    await redis.hset(f"userinfo:{user_id}", 'avatar', avatar_url)

#F 发送到语音redis队列
async def direct_chat_to_redis(redis, user_id, username, message, reply):
    danmaku_data = {
        'user_id': user_id,
        'username': username,
        'message': message,
        'reply': reply
    }
    res = await redis.lpush("chat", json.dumps(danmaku_data))
    print(res)

# 获取用户名、头像
async def get_user_info(user_id):
    _user = user.User(user_id)
    user_info = await _user.get_user_info()
    return user_info['name'], user_info['face']

def filter_danmaku(message):
    # 过滤包含特定字符的弹幕
    if any(char in message for char in "[]{}\\"):
        return False
    return True

async def handle_danmaku(danmaku):
    user_id = danmaku["data"]["info"][2][0]
    message = danmaku["data"]["info"][1]
    room_id = danmaku["room_display_id"]

    #以下是指令集
    if message.startswith("\\查询"):
        point = await redis.hget(f"point:{room_id}", user_id)
        if int(point) is None:
            point = 0
        danmaku = live.Danmaku(f"[当前剩余功德:{point}]")
        await live_info.send_danmaku(danmaku)
        return
    elif message.startswith("\\喵"):
        count = await redis.hget(f"freeTimes:{room_id}", user_id)
        if count is None:
            count = 0
        if int(count) > 3:
            return
        
        await redis.hincrby(f"freeTimes:{room_id}", user_id)
        await redis.hsetnx(f"point:{room_id}", user_id, 0)
        point = await redis.hincrby(f"point:{room_id}",user_id, 10)
        danmaku = live.Danmaku(f"[当前剩余功德:{point}]")
        await live_info.send_danmaku(danmaku)
        return
    
    elif message.startswith("\\今日次数"):
        res = await redis.zrank(f"dahanghai:{room_id}",user_id)
        # 大航海无限次
        if res is not None:
            danmaku = live.Danmaku(f"[剩余次数:无限]")
            await live_info.send_danmaku(danmaku)
        else:
            if (await redis.sismember(f"fanclub:{room_id}", user_id)) == 0:
                c1 = club_add
            if (await redis.sismember(f"followers:{room_id}", user_id)) == 0:
                c2 = follower_add
            speech_count = await redis.hincrby(f"count:{room_id}",user_id)
            speech_rest = c1 + c2 + base_count - speech_count
            point = await redis.hget(f"point:{room_id}",user_id)
            danmaku = live.Danmaku(f"[剩余次数{speech_rest},剩余功德{point}]")
            await live_info.send_danmaku(danmaku)

    # 过滤弹幕
    if not filter_danmaku(message):
        return

    # 获取用户名和头像URL，存入redis
    username, avatar_url = await get_user_info(user_id)
    save_user_to_redis(redis, user_id, username, avatar_url)

    #获取用户是否是大航海
    res = await redis.zrank(f"dahanghai:{room_id}",user_id)
    if res is None:
        c1 = 0
        c2 = 0
        await redis.hsetnx(f"count:{room_id}",user_id, 0)
        count = await redis.hincrby(f"count:{room_id}",user_id)

        # 粉丝团，关注追加
        if (await redis.sismember(f"fanclub:{room_id}", user_id)) == 1:
            c1 = club_add
        if (await redis.sismember(f"followers:{room_id}", user_id)) == 1:
            c2 = follower_add
        
        # 超额屏蔽, 10功德对话一次
        if count > base_count + c1 + c2:
            point = await redis.hget(f"point:{room_id}", user_id)
            if point is None or int(point) <= 0:
                danmaku = live.Danmaku(f"[剩余次数不足，请关注主播增加次数]")
                await live_info.send_danmaku(danmaku)
                return
            else:
                await redis.hincrby(f"point:{room_id}", user_id, -10)
        
        queue_name = 'normal_danmaku'
        is_guard = True
    else:
        queue_name = 'guard_danmaku'
        is_guard = True
    logger.info(f"GET A MESSAGE TO {queue_name}, userid={user_id}, username={username}, message={message}")

    #发送到chatgpt处理队列
    await save_danmaku_to_redis(redis, queue_name, user_id, username, avatar_url, message, is_guard)

async def welcome(info):
    user_id = info["data"]["data"]["uid"]
    username = info["data"]["data"]["uname"]

    # 获取用户名和头像URL
    message = f""
    reply = f"欢迎{username}来到{room_owner}的直播间，喵。"
    logger.info(reply)

    #发送一个欢迎进入的语音
    await direct_chat_to_redis(redis, user_id, username, message, reply)


async def gift_heard(info):
    room_id = info["room_display_id"]
    user_id = info["data"]["data"]["uid"]
    avatar_url = info["data"]["data"]["face"]
    giftName = info["data"]["data"]["giftName"]
    username = info["data"]["data"]["uname"]
    giftNum = info["data"]["data"]['num']
    # 电池数
    value = int(info["data"]["data"]['price'] / 10) 
    save_user_to_redis(redis, user_id, username, avatar_url)

    # 获取用户名和头像URL
    message = f""
    reply = f"\\感谢{username}赠送的{giftNum}个{giftName}喵。"
    logger.info(reply)
    
    # 计算用户投喂
    await redis.hsetnx(f"point:{room_id}", user_id, 0)
    await redis.zincrby(f"cost:{room_id}", value, user_id)
    point = await redis.hincrby(f"point:{room_id}", user_id, value)

    #发送一个感谢投喂的语音
    await direct_chat_to_redis(redis, user_id, username, message, reply)

    #发送弹幕
    danmaku = live.Danmaku(f"[当前功德:{point}]")
    await live_info.send_danmaku(danmaku)


async def super_chat(info):
    room_id = info["room_display_id"]
    user_id = info["data"]["data"]["uid"]
    message = info["data"]["data"]["message"]
    username = info["data"]["data"]["user_info"]["uname"]
    avatar_url = info["data"]["data"]["user_info"]["face"]
    value = int(info["data"]["data"]["price"] * 100)
    save_user_to_redis(redis, user_id, username, avatar_url)
    is_guard = True
    queue_name = "superchat_danmaku"
    logger.info(f"GET A MESSAGE TO {queue_name}, userid={user_id}, username={username}, message={message}")
    
    # 计算用户投喂
    await redis.zincrby(f"cost:{room_id}", value, user_id)
    await redis.hsetnx(f"point:{room_id}", user_id, 0)
    await redis.hincrby(f"point:{room_id}", user_id, value)

    await save_danmaku_to_redis(redis, queue_name, user_id, username, message, is_guard)

async def main():
    # 直播间配置
    global live_info 
    global logger 
    global room_owner
    room_owner = "你的直播间名"
    room_id = 0 #你的直播间roomID
    live_room = live.LiveDanmaku(room_id)
    live_info = live.LiveRoom(room_id, credential=CREDENTIAL)

    # Log配置
    logger= logging.getLogger('my_logging')  
    logger.setLevel(logging.INFO)
    proDir = os.path.split(os.path.realpath(__file__))[0]
    logPath = os.path.join(proDir, "getDanmaku.log")
    fh = logging.FileHandler(logPath, encoding='utf8')
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # 连接到Redis
    global redis   
    redis = await connect_to_redis()

    # 监听弹幕事件
    live_room.add_event_listener("DANMU_MSG", handle_danmaku)
    live_room.add_event_listener("INTERACT_WORD", welcome)
    live_room.add_event_listener("SEND_GIFT", gift_heard)
    live_room.add_event_listener("SUPER_CHAT_MESSAGE", super_chat)

    # 连接到直播间
    await live_room.connect()

    # 无限循环
    while True:
        await asyncio.sleep(1)

asyncio.run(main())

import asyncio
import datetime
from bilibili_api import live, user, Credential
import logging
import aioredis
import configparser
import os

#更新redis中的大航海数据, 5秒定时batch
async def get_user_info(user_id):
    _user = user.User(user_id)
    user_info = await _user.get_user_info()
    return user_info['name'], user_info['face']

def getConfig(filename, section, option):
    proDir = os.path.split(os.path.realpath(__file__))[0]
    configPath = os.path.join(proDir, filename)
    conf = configparser.ConfigParser()
    conf.read(configPath)
    res = conf.get(section, option)
    return res

async def save_user_to_redis(redis,  user_id, username, avatar_url):
    await redis.hset(f"userinfo:{user_id}", 'username', username)
    await redis.hset(f"userinfo:{user_id}", 'avatar', avatar_url)

async def main():
    pool = aioredis.ConnectionPool.from_url("redis://ip:port/0", encoding="utf-8", decode_responses=True)
    client = aioredis.Redis(connection_pool=pool)
    value = await client.get("my-key")

    proDir = os.path.split(os.path.realpath(__file__))[0]
    logPath = os.path.join(proDir, "renewGuard.log")
    logging.FileHandler(logPath,encoding='utf8')
    nowDay = 1

    CREDENTIAL = Credential(sessdata= "###############",
                            bili_jct="###############", 
                            buvid3="###############")
    print(value)
    while True:
        # 日付变更处理        
        room_id = getConfig("renewGuard.config","room", "id")
        if nowDay != datetime.datetime.now().day:
            nowDay = datetime.datetime.now().day
            await client.delete(f"count:{room_id}")

        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        logging.info(f"update time : {now}")
        liveroom = live.LiveRoom(room_id, credential= CREDENTIAL)
        owner_info = await liveroom.get_room_info()
        owner = user.User(owner_info['room_info']["uid"], credential= CREDENTIAL)

        # 拉取舰长
        dahanghai = await liveroom.get_dahanghai()
        for item in dahanghai["top3"]:
            uid =item["uid"]
            rank = item["rank"]
            res = await client.zadd(f"dahanghai:{room_id}",{uid: rank})
            logging.info(f"result:{res} insert {uid}, {rank}")
        for item in dahanghai["list"]:
            uid =item["uid"]
            rank = item["rank"]
            res = await client.zadd(f"dahanghai:{room_id}",{uid: rank})
            logging.info(f"result:{res} insert {uid}, {rank}")
        
        # 拉取关注信息
        followers_count = (await owner.get_followers(0))["total"]
        i = 0
        while 20 * i < followers_count:
            followers = await owner.get_followers(i)
            i = i + 1
            for follower in followers["list"]:
                 res = await client.sadd(f"followers:{room_id}",follower["mid"])

        # 拉取粉丝团
        fanclub = await liveroom.get_fans_medal_rank()
        for item in fanclub["list"]:
            uid =item["uid"]
            res = await client.sadd(f"fanclub:{room_id}",uid)
        
        # 投喂用户信息获取
        top_users = await client.zrevrangebyscore(f"cost:{room_id}", '+inf', '-inf', start=0, num=50, withscores=True)
        for _, (user_id, _) in enumerate(top_users):
            username, avatar_url = await get_user_info(user_id)
            await save_user_to_redis(client, user_id, username, avatar_url)

        print(f"select : {room_id}")
        await asyncio.sleep(5)

asyncio.run(main())
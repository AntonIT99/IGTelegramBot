import asyncio
import json
import logging
import ssl
import time
from json import JSONDecodeError
from pathlib import Path

import httpcore
import telegram
from telegram.constants import ParseMode
from telegram.error import RetryAfter

import config
from instagram import fetch_posts_from_instagram, InstagramPost

logging.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logging.INFO)

bot = telegram.Bot(config.TOKEN)

filename = "posts.json"


async def update():
    images_codes = await read_images_codes()
    posts_from_all_authors = {}
    fetch_posts_from_instagram(posts_from_all_authors)
    for username in posts_from_all_authors:
        new_images = 0
        images_codes_sorted_by_date = sort_by_date_ascending(posts_from_all_authors)
        for code in images_codes_sorted_by_date:
            if username not in images_codes.keys() or code not in images_codes[username]:
                new_images = await post_image(posts_from_all_authors[username][code], images_codes, new_images)
        if new_images > 0:
            logging.info("[{}]: {} new image{} to post in telegram".format(username, new_images, "s" if new_images > 1 else ""))
        else:
            logging.info("[{}]: No new image to post in telegram".format(username))


def sort_by_date_ascending(posts: dict) -> list:
    flattened_posts_list = []
    for username in posts.keys():
        for code in posts[username].keys():
            flattened_posts_list.append(posts[username][code])
    flattened_posts_list.sort(key=lambda x: x.post_date)
    return [post.image_code for post in flattened_posts_list]


async def post_image(post: InstagramPost, images_codes: dict, counter: int) -> int:
    if config.POST_DATE_LIMIT is None or post.post_date >= config.POST_DATE_LIMIT:
        captions = process_long_desc("<a href=\"https://www.instagram.com/p/{}/\">Neuer Beitrag von @{}</a>\n{}".format(post.image_code, post.author.username, post.description))
        await exec_with_retry(bot.send_photo,
                              chat_id=config.CHANNEL,
                              photo=post.image_url,
                              caption=captions[0],
                              parse_mode=ParseMode.HTML)
        for i in range(1, len(captions)):
            await exec_with_retry(bot.send_message,
                                  chat_id=config.CHANNEL,
                                  text=captions[i],
                                  parse_mode=ParseMode.HTML)
        if post.author.username not in images_codes.keys():
            images_codes[post.author.username] = []
        images_codes[post.author.username].append(post.image_code)
        json.dump(images_codes, open(filename, "w"))
        return counter + 1
    return counter


async def exec_with_retry(func, **kwargs):
    exception = True
    while exception:
        try:
            await func(**kwargs)
            exception = False
            time.sleep(1)
        except (RetryAfter, ssl.SSLWantReadError, asyncio.exceptions.CancelledError, httpcore.ReadTimeout, telegram.error.TimedOut, telegram.error.BadRequest, TimeoutError) as error:
            exception = True
            logging.error(error)
            time.sleep(1)


def process_long_desc(long_desc: str) -> list:
    lines = long_desc.split("\n")
    char_count = 0
    char_limit = 1000
    message_captions = [""]
    caption_index = 0
    for line in lines:
        line += "\n"
        if char_count + len(line) < char_limit:
            message_captions[caption_index] += line
            char_count += len(line)
        else:
            message_captions.append(line)
            char_count = len(line)
            caption_index += 1
    return message_captions


async def read_images_codes() -> dict:
    images_codes = {}
    if not Path(filename).is_file():
        json.dump(images_codes, open(filename, "w"))
    try:
        images_codes = json.load(open(filename, "r"))
    except JSONDecodeError:
        logging.error("Could not decode {}".format(filename))
    return images_codes


async def loop(interval, task):
    while True:
        await asyncio.gather(task(), asyncio.sleep(interval))


if __name__ == '__main__':
    asyncio.run(update() if config.AUTO_EXIT else loop(config.UPDATE_INTERVAL_S, update))

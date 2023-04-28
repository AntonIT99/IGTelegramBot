import logging
import traceback
from datetime import date
from time import sleep
from typing import Optional

import requests

import config


class Author:

    def __init__(self, username: str, full_name: str, profile_pic_url: str):
        self.username = str(username)
        self.full_name = str(full_name)
        self.profile_pic_url = str(profile_pic_url)

    def __eq__(self, other):
        return (isinstance(other, Author) and
                self.username == other.username and
                self.full_name == other.full_name and
                self.profile_pic_url == other.profile_pic_url)


class InstagramPost:

    def __init__(self, author: Author, image_code: str, image_url: str, description: str, likes: int, comments: int, post_date: date):
        self.author = author
        self.image_code = str(image_code)
        self.image_url = str(image_url)
        self.description = str(description)
        self.likes = int(likes)
        self.comments = int(comments)
        self.post_date = post_date

    def __eq__(self, other):
        return (isinstance(other, InstagramPost) and
                self.author == other.author and
                self.image_code == other.image_code and
                self.image_url == other.image_url and
                self.description == other.description and
                self.likes == other.likes and
                self.comments == other.comments and
                self.post_date == other.post_date)


def fetch_posts_from_instagram(posts_from_all_authors: dict):
    for username in config.INSTAGRAM_ACCOUNTS:
        user_id, author = get_user_data(username)
        if user_id is not None and author is not None:
            posts_from_all_authors[username] = get_posts_from_instagram(user_id, author)
        else:
            logging.error("[{}]: Failed to update: can not retrieve account data".format(username))


# return an Author and its user id from the user data of the specified account
def get_user_data(username: str) -> (Optional[str], Optional[Author]):
    response = requests.get("https://www.instagram.com/{}/?__a=1&__d=dis".format(username), headers=config.HEADER, timeout=config.TIMEOUT)
    try:
        user_data = response.json()["graphql"]["user"]
        return user_data["id"], Author(username, user_data["full_name"], user_data["profile_pic_url_hd"])
    except Exception:
        traceback.print_exc()
        return None, None


# return a dict of InstagramPost from the data of the latest images available from the specified Author
def get_posts_from_instagram(user_id: str, author: Author) -> dict:
    images = {}
    json = {}

    try:
        logging.info("[{}]: fetching latest images...".format(author.username))
        json = get_json_from_graphql_query(user_id)
        images_count = int(json["data"]["user"]["edge_owner_to_timeline_media"]["count"])
        if config.FETCHING_LIMIT is not None and images_count > config.FETCHING_LIMIT:
            images_count = config.FETCHING_LIMIT
        step = len(json["data"]["user"]["edge_owner_to_timeline_media"]["edges"])
    except Exception:
        traceback.print_exc()
        if "message" in json:
            print(json["message"])
        return images

    fetched_images = 0

    end_cursor = str(json["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"])
    images_list = json["data"]["user"]["edge_owner_to_timeline_media"]["edges"]

    for i in range(0, images_count, step):

        for image_data in images_list:
            image_code = str(image_data["node"]["shortcode"])
            image_url = str(image_data["node"]["display_url"])
            description = ""
            caption_data = image_data["node"]["edge_media_to_caption"]["edges"]
            if len(caption_data) > 0:
                if "node" in caption_data[0].keys():
                    if "text" in caption_data[0]["node"].keys():
                        description = str(caption_data[0]["node"]["text"])
            likes = int(image_data["node"]["edge_media_preview_like"]["count"])
            comments = int(image_data["node"]["edge_media_to_comment"]["count"])
            timestamp = int(image_data["node"]["taken_at_timestamp"])
            images[image_code] = InstagramPost(author, image_code, image_url, description, likes, comments, date.fromtimestamp(timestamp))
            fetched_images += 1

        if fetched_images != images_count:
            try:
                logging.info("[{}]: fetching images {} to {}...".format(author.username, fetched_images,
                                                                        fetched_images + step - 1 if fetched_images + step - 1 < images_count else images_count - 1))
                json = get_json_from_graphql_query(user_id, end_cursor)
                end_cursor = str(json["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"])
                images_list = json["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
            except Exception:
                traceback.print_exc()
                logging.error("[{}]: failed to fetching images, retrying in 5s...".format(author.username))
                sleep(5)
                try:
                    logging.info("[{}]: retrying to fetch images {} to {}...".format(author.username,
                                                                                     fetched_images, fetched_images + step - 1 if fetched_images + step - 1 < images_count else images_count - 1))
                    json = get_json_from_graphql_query(user_id, end_cursor)
                    end_cursor = str(json["data"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"])
                    images_list = json["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
                except Exception:
                    traceback.print_exc()
                    logging.info("[{}]: abort the fetching process".format(author.username))
                    break

    logging.info("[{}]: {} images fetched from instagram".format(author.username, fetched_images))
    return images


def get_json_from_graphql_query(user_id: str, end_cursor=""):
    if end_cursor:
        response = requests.get("https://www.instagram.com/graphql/query/?query_id=17888483320059182&id={}&first=12&after={}".format(user_id, end_cursor),
                                headers=config.HEADER, timeout=config.TIMEOUT)
    else:
        response = requests.get("https://www.instagram.com/graphql/query/?query_id=17888483320059182&id={}&first=12".format(user_id),
                                headers=config.HEADER, timeout=config.TIMEOUT)
    return response.json()

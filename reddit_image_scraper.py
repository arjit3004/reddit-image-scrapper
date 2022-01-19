import time
import requests
import re
from bs4 import BeautifulSoup
import json
import os
from tqdm import tqdm
from argparse import ArgumentParser
from multiprocessing import Pool
import numpy as np

directory = None


def get_initial_id(subreddit):
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?sort=hot&show=all&t=all"
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response = json.loads(response.content)["data"]["children"][0]["data"]["name"]
        return response
    except Exception as e:
        print(str(e))
        print("ERROR IN get_initial_id()...")
        return None


def get_links(id_, subreddit):
    try:
        api = "https://gateway.reddit.com/desktopapi/v1/subreddits/{}?rtj=only&redditWebClient=web2x&app=web2x-client-production&allow_over18=1&include=prefsSubreddit&after={}&forceGeopopular=false&layout=card&sort=hot".format(
            subreddit, id_
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
        }
        response = requests.get(api, headers=headers)
        response = json.loads(response.content)

        id_ = response["postIds"][-1] if len(response["postIds"]) > 0 else None
        posts = response["posts"]

        links = []

        for postid in posts:
            media = posts[postid]["media"]

            if media is not None:
                if "resolutions" in media and media["resolutions"] is not None:
                    if posts[postid]["preview"] is not None:
                        link = posts[postid]["preview"]["url"]
                        links.append(link)
                if "mediaMetadata" in media and media["mediaMetadata"] is not None:
                    for _id in media["mediaMetadata"]:
                        link = media["mediaMetadata"][_id]["s"]["u"]
                        links.append(link)

        return id_, links
    except Exception as e:
        print(str(e))
        print("ERROR IN get_links()...")
        return None, []


def download_image(url):
    try:
        file = open(directory + "/" + url.split("/")[-1], "wb")
        file.write(requests.get(url).content)
        file.close()
    except Exception as e:
        print(str(e))
        print("ERROR in download_image()...")


def download_images(subreddit):
    try:
        id_ = get_initial_id(subreddit)
        image_url = []
        while id_:
            id_, links = get_links(id_, subreddit)
            image_url += links

        n = len(image_url)//100
        print(l'DOWNLOADING ...')
        if n!=0:
            split = np.array_split(image_url, n)
            for i in split:
                p = Pool(len(i))
                p.map(download_image, i)
                p.terminate()
                p.join()
        else:
            p = Pool(len(image_url))
            p.map(download_image, image_url)
            p.terminate()
            p.join()
        return True
    except Exception as e:
        print(str(e))
        print('ERROR IN download_images()...')
        return False


if __name__ == "__main__":

    parser = ArgumentParser()

    parser.add_argument(
        "-s",
        "--subreddit",
        dest="subreddit",
        type=str,
        help="Enter input subreddit with extention",
        required=True,
    )

    args = parser.parse_args()

    directory = args.subreddit
    os.mkdir(directory)
    if download_images(directory):
        print("DOWNLOADING COMPLETE")
    else:
        print("ERROR")
"""
okreddit
~~~~~~~~

:author: Sean Pianka
:reddit: cdrootrmdashrfstar
:email: me@seanpianka.com
:github: seanpianka
:twitter: seanpianka

"""
import configparser
import lxml
import praw
import requests
import sys
import threading
import time
from lxml import html


DEFINE_API = 'http://google-dictionary.so8848.com/meaning?word={}'

SLEEP_TIME = {
    "scan": 15,
    "delete": 1000,
}

GREEN_LIGHT = True  # used to prevent duplicate commenting
SUBREDDITS = ["codegress"]#, "all"]
POINT_THRESHOLD = 0
USER_AGENT = "OkReddit by /u/cdrootrmdashrfstar"
CONF_FILENAME = 'okreddit.conf'

config = configparser.ConfigParser()
config.read(CONF_FILENAME)

USERNAME = config.get('Authentication', 'username')
PASSWORD = config.get('Authentication', 'password')

PREDEFINED_POST = "Found \"{}\", so here's your definition:\n{}\nThanks for using [OkReddit](https://github.com/seanpianka/OkReddit)!\n\n[Contact the Creator](http://reddit.com/u/cdrootrmdashrfstar)."


def run():
    r = praw.Reddit(USER_AGENT)
    r.login(USERNAME, PASSWORD)
    print("Logged in as {}.".format(USERNAME))

    # Old comment scanner-deleter to delete <1 point comments every half hour
    t = threading.Thread(target=delete_downvoted_posts, args=(r, ))
    t.start()

    phrases_to_look_for = (
        "ok google define", "ok reddit define", "ok define",
        "okg define", "okr define",
    )

    while True:
        print("Initializing scanner...")
        scan_comments(r, phrases_to_look_for)
        print("Waiting {} seconds...".format(SLEEP_TIME['scan']))
        time.sleep(SLEEP_TIME['scan'])


def scan_comments(session, phrases):
    print("Fetching new comments...")

    kargs = {
        "reddit_session": session,
        "subreddit": '',
        "limit": None,
        "verbosity": 0,
    }
    comments = {}
    reply_count = 0

    for subreddit in SUBREDDITS:
        kargs['subreddit'] = subreddit
        comments[subreddit] = praw.helpers.comment_stream(**kargs)

    for subreddit in SUBREDDITS:
        for comment in comments[subreddit]:
            for phrase in phrases:
                print("Searching for phrases in comment...")
                if phrase in comment.body:
                    for reply in comment.replies:
                        if reply.author.name == USERNAME:
                            print("Ignoring comment, already replied.")
                            GREEN_LIGHT = False
                            break

                    if GREEN_LIGHT:
                        print("Found new comment, replying...")
                        definition = define_word(word)
                        post_definition_reply(reply_to, phrase, definition)
                        reply_count += 1
                        break

            if reply_count == 1000:
                return


def post_definition_reply(reply_to, phrase, definition):
    # post
    try:
        print("Posting reply...")
        reply_to.reply(PREDEFINED_COMMENT.format(phrase, definition))
    except Exception as e:
        try:
            print("Received error {}: {}".format(e.code, e))
        except Exception as e2:
            print("Unexpected exception: {}".format(e2))


def delete_downvoted_posts(session):
    belowstr = "Found comment with score below point threshold {}, deleting."
    waitstr = "Waiting {} seconds before deleting more downvoted replies..."

    while True:
        print("Deleting comments with a score equal to or below 0...")
        my_account = session.get_redditor(USERNAME)
        my_comments = my_account.get_comments(limit=25)

        for comment in my_comments:
            if comment.score <= POINT_THRESHOLD:
                print(belowstr.format(POINT_THRESHOLD))
                comment.delete()

        print(waitstr.format(SLEEP_TIME['delete']))
        time.sleep(SLEEP_TIME['delete'])


def define_word(word):
    res = requests.get(DEFINE_API.format(word))
    if res.status_code == 404:
        # The definition API is now invalid.
        # Do not run until a new API is provided.
        sys.exit()

    tree = html.fromstring(res.text)

    definition = ''
    return definition


if __name__ == '__main__':
    run()

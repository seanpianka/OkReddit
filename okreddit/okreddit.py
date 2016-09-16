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
import datetime
import lxml
import praw
import random
import re
import requests
import string
import sys
import threading
import time
from lxml import html


def print_log(msg, *args, **kwargs):
    now = datetime.datetime.now()
    time_format = (now.year, now.month, now.day,
                   now.hour, now.minute, now.second)
    print("[{:02}-{:02}-{:02} {:02}:{:02}:{:02}]: {}".\
          format(*time_format, msg), *args, **kwargs)


DEFINE_API = 'http://google-dictionary.so8848.com/meaning?word={}'

SLEEP_TIME = {
    "scan": 15,
    "delete": 1000,
}

OKREDDIT_CONF = 'okreddit.conf'

SUBREDDITS_CONF = 'subreddits.conf'
SUBREDDITS = {
    'allowed': [],
    'disallowed': [],
}

with open(SUBREDDITS_CONF, 'r') as f:
    for subreddit in f.read().splitlines():
        subreddit = str(subreddit).strip()
        if subreddit[0] != "-":
            SUBREDDITS['allowed'].append(subreddit)
        else:
            SUBREDDITS['disallowed'].append(subreddit)

print_log(SUBREDDITS)

POINT_THRESHOLD = 0
USER_AGENT = "OkReddit by /u/cdrootrmdashrfstar"

config = configparser.ConfigParser()
config.read(OKREDDIT_CONF)

USERNAME = config.get('Authentication', 'username')
PASSWORD = config.get('Authentication', 'password')

PREDEFINED_COMMENT = "Found \"{}\", so here's your definition(s):\n\n" \
                     "{}\n\nThanks for using [OkReddit]" \
                     "(https://github.com/seanpianka/OkReddit)!\n\n" \
                     "[Contact the Creator]" \
                     "(http://reddit.com/u/cdrootrmdashrfstar)."

BASE_PATTERN = r"\b{}.(\w+)"
PHRASES_TO_LOOK_FOR = [
    "ok google define", "ok reddit define", "ok define",
    "okg define", "okr define",
]
PHRASE_PATTERNS = {}

for phrase in PHRASES_TO_LOOK_FOR:
    PHRASE_PATTERNS[phrase] = re.compile(BASE_PATTERN.format(phrase))

MAX_DEFINITIONS = 5


def run(phrases):
    r = praw.Reddit(USER_AGENT)
    r.login(USERNAME, PASSWORD)
    print("Logged in as {}.".format(USERNAME))

    # Old comment scanner-deleter to delete <1 point comments every half hour
    t = threading.Thread(target=delete_downvoted_posts, args=(r, ))
    t.start()


    while True:
        print("Initializing scanner...")
        scan_comments(r, phrases)
        print("Waiting {} seconds...".format(SLEEP_TIME['scan']))
        time.sleep(SLEEP_TIME['scan'])


def scan_comments(session, phrases):
    print("Fetching new comments...")

    exclude = set(string.punctuation)

    kargs = {
        "reddit_session": session,
        "subreddit": '',
        "limit": None,
        "verbosity": 0,
    }
    comments = {}
    reply_count = 0

    for subreddit in SUBREDDITS['allowed']:
        kargs['subreddit'] = subreddit
        # comment_stream is a generator
        comment_stream = praw.helpers.comment_stream(**kargs)
        comments[subreddit] = comment_stream

    for subreddit in SUBREDDITS['allowed']:
        for comment in comments[subreddit]:
            comment.body = ''.join(ch for ch in comment.body if ch not in exclude)
            GREEN_LIGHT = True  # used to prevent duplicate commenting
            for phrase, pattern in phrases.items():
                print("Searching for phrases in {}'s comment, id: {}...".\
                      format(comment.author, comment.id))

                if phrase in comment.body:
                    print("Fetching comment replies...")
                    comment.refresh()
                    if str(comment.author.name).lower() == USERNAME.lower() or\
                    [x for x in comment.replies if x.author.name.lower() == USERNAME.lower()]:
                        print("Ignoring comment, already replied.")
                        GREEN_LIGHT = False

                    if GREEN_LIGHT:
                        try:
                            word = pattern.findall(comment.body)[0]
                        except:
                            print("Pattern: {}".format(pattern))
                            print("Unable to match comment pattern.",
                                  "Attmepting to match other patterns...")
                        else:
                            print("Found new comment, id: {}, replying...".\
                                  format(comment.id))
                            definition = define_word(word)
                            post_definition_reply(comment, word, definition)
                            reply_count += 1
                            print("Moving to next comment...")
                            break

            if reply_count == 1000:
                print("Returning...")
                return


def post_definition_reply(reply_to, word, definition):
    try:
        global PREDEFINED_COMMENT
        print("Posting reply...")
        reply_to.reply(PREDEFINED_COMMENT.format(word, definition))
    except Exception as e:
        print("Received error: {}".format(e))


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
        print("The definition API is now invalid.",
              "Do not run until a new API is provided.")
        sys.exit()

    tree = html.fromstring(res.text)

    data = {}
    # credit to @mmcdan for this xpath to find <b> OR <li> w/ class="std"
    # makes perfect use of xpath's `|` (union) operator
    defns_xpath = '//div[@id="forEmbed"]/b|//*[@class="std"]/ol/div/li'
    for element in tree.xpath(defns_xpath):
        if element.tag == 'b':
            last_category = element.text.strip()
            if last_category not in data:
                data[last_category] = []
        elif element.tag == 'li':
            if last_category:
                data[last_category].append(element.text.strip())
            else:
                print('Warning: li found before b... this shouldn\'t happen.')

    definition = ''

    for form, defns in data.items():
        word_meaning = "As a **{}**, {} can mean:\n\n".format(form, word)
        definition += word_meaning
        random.shuffle(defns)
        for i, defn in enumerate(defns):
            if i == MAX_DEFINITIONS:
                break
            definition += "\n{}: {}\n".format(i + 1, defn)
        definition += "\n"

    return definition


if __name__ == '__main__':
    run(PHRASE_PATTERNS)

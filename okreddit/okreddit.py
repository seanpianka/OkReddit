"""
okreddit
~~~~~~~~

:author: Sean Pianka
:reddit: cdrootrmdashrfstar
:email: me@seanpianka.com
:github: seanpianka
:twitter: seanpianka

"""
import random
import string
import sys
import threading
import time

import lxml
import requests
import praw
from lxml import html

import constants
import multithreading
from constants import (DEFINE_API, SLEEP_TIME, SUBREDDITS, POINT_THRESHOLD,
                       USER_AGENT, PREDEFINED_COMMENT, PHRASE_PATTERNS,
                       USERNAME, PASSWORD, MAX_DEFINITIONS, VERBOSITY_LEVEL,
                       MAX_REPLIES_PER_CYCLE, DISABLE_PRAW_WARNING,
                       MAX_THREAD_COUNT)
from helpers import print_log

print_log(SUBREDDITS)


def run(phrases):
    """

    """
    print_log("*** {} ***".format(USER_AGENT))
    print_log("Bot initializing...")
    r = praw.Reddit(USER_AGENT)
    try:
        r.login(USERNAME, PASSWORD, disable_warning=DISABLE_PRAW_WARNING)
    except Exception as e:
        print_log("Error while logging in: {}".format(e))
        sys.exit()
    print_log("Logged in as {}.".format(USERNAME))

    # Old comment scanner-deleter to delete <1 point comments every half hour
    t = threading.Thread(target=delete_downvoted_posts, args=(r, ))
    t.start()

    while True:
        print_log("Initializing scanner...")
        scan_comments(r, phrases)
        print_log("Waiting {} seconds...".format(SLEEP_TIME['scan']))
        time.sleep(SLEEP_TIME['scan'])

    print_log("Bot exiting...")


reply_count = 0


def scan_comments(session, phrases):
    """

    """
    pool = multithreading.ThreadPool(len(SUBREDDITS['allowed']))
    lock = multithreading.Lock()

    def watch_subreddit(subreddit, comment_generator):
        global reply_count

        print_log("Beginning to scan {}...".format(subreddit))

        for comment in comment_generator:
            comment.body = ''.join(ch for ch in comment.body\
                                   if ch not in exclude)
            GREEN_LIGHT = True  # used to prevent duplicate commenting
            for phrase, pattern in phrases.items():
                print_log("Searching for phrases in {}'s comment, id: {}...".\
                      format(comment.author, comment.id))

                if phrase in comment.body:
                    print_log("Fetching comment replies...")
                    comment.refresh()
                    if str(comment.author.name).lower() == USERNAME.lower() or\
                    [x for x in comment.replies\
                     if x.author.name.lower() == USERNAME.lower()]:
                        print_log("Ignoring comment, already replied.")
                        GREEN_LIGHT = False

                    if GREEN_LIGHT:
                        try:
                            word = pattern.findall(comment.body)[0]
                        except:
                            print_log("Pattern: {}".format(pattern))
                            print_log("Unable to match comment pattern.",
                                  "Attmepting to match other patterns...")
                        else:
                            print_log("Found new comment, id: {}, replying...".\
                                      format(comment.id))
                            definition = define_word(word)
                            post_definition_reply(comment, word, definition)
                            reply_count += 1
                            print_log("Moving to next comment...")
                            break
            with lock:
                if reply_count == MAX_REPLIES_PER_CYCLE:
                    print_log("Ending comment scan cycle...")
                    return

    exclude = set(string.punctuation)

    kargs = {
        "reddit_session": session,
        "subreddit": '',
        "limit": None,
        "verbosity": VERBOSITY_LEVEL,
    }

    for subreddit in SUBREDDITS['allowed']:
        kargs['subreddit'] = subreddit
        # comment_stream is a generator
        comment_generator = praw.helpers.comment_stream(**kargs)

        pool.add_task(
            watch_subreddit,
            subreddit,
            comment_generator,
        )

    print_log("Fetching new comments...")
    pool.wait_completion()


def post_definition_reply(reply_to, word, definition):
    """

    """
    try:
        reply_to.reply(PREDEFINED_COMMENT.format(word, definition))
        print_log("Posting reply...")
    except Exception as e:
        print_log("Received error: {}".format(e))


def delete_downvoted_posts(session):
    """

    """
    belowstr = "Found comment with score below point threshold {}, deleting."
    waitstr = "Waiting {} seconds before deleting more downvoted replies..."

    while True:
        print_log("Deleting comments with a score equal to or below 0...")
        my_account = session.get_redditor(USERNAME)
        my_comments = my_account.get_comments(limit=25)

        for comment in my_comments:
            if comment.score <= POINT_THRESHOLD:
                print_log(belowstr.format(POINT_THRESHOLD))
                comment.delete()

        print_log(waitstr.format(SLEEP_TIME['delete']))
        time.sleep(SLEEP_TIME['delete'])


def define_word(word):
    """

    """
    res = requests.get(DEFINE_API.format(word))
    if res.status_code == 404:
        print_log("The definition API is now invalid.",
                  "Do not run until a new API is provided.")
        sys.exit()

    tree = html.fromstring(res.text)
    word_forms_defns = {}
    # credit to @mmcdan for this xpath to find <b> OR <li> w/ class="std"
    # makes perfect use of xpath's `|` (union) operator
    defns_xpath = '//div[@id="forEmbed"]/b|//*[@class="std"]/ol/div/li'
    for element in tree.xpath(defns_xpath):
        if element.tag == 'b':
            last_category = element.text.strip()
            if last_category not in word_forms_defns:
                word_forms_defns[last_category] = []
        elif element.tag == 'li':
            if last_category:
                word_forms_defns[last_category].append(element.text.strip())
            else:
                print_log('Warning: li before b... this shouldn\'t happen.')

    definition = ''

    for form, defns in word_forms_defns.items():
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

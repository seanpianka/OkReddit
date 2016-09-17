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
import webbrowser

import lxml
import requests
import praw
from lxml import html

import constants
import multithreading
from constants import (DEFINE_API, SLEEP_TIME, SUBREDDITS, POINT_THRESHOLD,
                       USER_AGENT, PREDEFINED_COMMENT, PHRASE_PATTERNS,
                       MAX_DEFINITIONS, VERBOSITY_LEVEL, MAX_REPLIES_PER_CYCLE,
                       DISABLE_PRAW_WARNING, MAX_THREAD_COUNT, CLIENT_ID,
                       CLIENT_SECRET)
from helpers import print_log, lcstrcmp


print_log(SUBREDDITS)


def run(phrases):
    """

    """
    print_log("*** {} ***".format(USER_AGENT))
    print_log("Bot initializing...")
    r = praw.Reddit(USER_AGENT)
    try:
        r.set_oauth_app_info(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             redirect_uri='http://127.0.0.1:65010/authorize')
        url = r.get_authorize_url('OkRedditDefine',
                                  "read edit history identity submit",
                                  True)
        webbrowser.open(url)
        access_token = input('Access-token: ').strip()
        access_info = r.get_access_information(access_token)
        USERNAME = r.get_me().name
    except Exception as e:
        print_log("Error while logging in: {}".format(e))
        sys.exit()
    print_log("Logged in as {}.".format(USERNAME))

    # Old comment scanner-deleter to delete <1 point comments every half hour
    #t = threading.Thread(target=delete_downvoted_posts, args=(r, USERNAME, ))
    #t.start()

    print_log("Initializing scanner...")
    scan_comments(r, phrases, USERNAME)

    print_log("Bot exiting...")


def scan_comments(session, phrases, USERNAME):
    """

    """
    exclude = set(string.punctuation)

    kargs = {
        "reddit_session": session,
        "subreddit": '',
        "limit": None,
        "verbosity": VERBOSITY_LEVEL,
    }

    reply_count = 0
    comments = {}

    for subreddit in SUBREDDITS['allowed']:
        print_log("Fetching new comments...")
        kargs['subreddit'] = subreddit
        comments[subreddit] = praw.helpers.comment_stream(**kargs)

    for subreddit in SUBREDDITS['allowed']:
        comment_generator = comments[subreddit]
        print_log("Beginning to scan {}...".format(subreddit))

        for comment in comment_generator:
            print_log("Searching for phrases in {}'s comment, id: {}...".\
                  format(comment.author, comment.id))

            if str(comment.subreddit).lower() in SUBREDDITS['disallowed']:
                print_log("Ignoring comment from blacklisted subreddit: {}".\
                          format(comment.subreddit))
                continue

            GREEN_LIGHT = True  # used to prevent duplicate commenting
            comment.body = ''.join(ch.lower() for ch in comment.body\
                                   if ch not in exclude)

            for phrase, pattern in phrases.items():
                if phrase in comment.body:
                    print_log("Fetching comment replies...")
                    comment.refresh()
                    if lcstrcmp(comment.author.name, USERNAME) or \
                    [x for x in comment.replies\
                     if lcstrcmp(x.author.name, USERNAME)]:
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
            if reply_count == MAX_REPLIES_PER_CYCLE:
                print_log("Ending comment scan cycle...")
                print_log("Waiting {} seconds...".\
                          format(SLEEP_TIME['scan']))
                time.sleep(SLEEP_TIME['scan'])
        print_log("Returning...")



def post_definition_reply(reply_to, word, definition):
    """

    """
    print_log("Posting reply...")
    try:
        reply_to.reply(PREDEFINED_COMMENT.format(word, definition))
        print_log("Reply posted!")
    except Exception as e:
        print_log("Received error while posting: {}".format(e))


def delete_downvoted_posts(session, USERNAME):
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

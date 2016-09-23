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
                       CLIENT_SECRET, COMMENT_API, PULL_COUNT)
from helpers import print_log, lcstrcmp, RedditComment


def run(phrases):
    """

    """
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
        # for testing
        USERNAME = "OkDefine"
    except Exception as e:
        print_log("Error while logging in: {}".format(e))
        sys.exit()
    else:
        print_log("Logged in as {}.".format(USERNAME))

    # Old comment scanner-deleter to delete <1 point comments every half hour
    #t = threading.Thread(target=delete_downvoted_posts, args=(r, USERNAME, ))
    #t.start()

    print_log("Initializing bot's scanner...")

    while True:
        new_comments = scan_comments(r, phrases, USERNAME)
        reply_to_comments(new_comments)

        print_log("Ending comment scan cycle...")
        print_log("Waiting {} seconds...".\
                  format(SLEEP_TIME['scan']))
        time.sleep(SLEEP_TIME['scan'])

    print_log("Bot exiting...")


def scan_comments(session, phrases, USERNAME):
    """

    """

    def already_replied_to(comment):
        """

        """
        return lcstrcmp(comment['author'], USERNAME) or \
        bool([x for x in comment['object'].replies\
             if lcstrcmp(x.author.name, USERNAME)])

    def validate_comments(comment_list):
        """

        """
        print_log("Validating {} comments...".format(len(comment_list)))
        for comment in comment_list:
            comment.update({
                'msg_phrase': phrase
            })
            comment.update({
                'object': session.get_info(thing_id="t1_" + comment['id'])
            })
        print_log("Done.")

        return [c for c in comment_list if not already_replied_to(c)]

    raw_comments = []
    to_be_added_comments = []
    new_comments = {k: list() for k in SUBREDDITS['allowed'] if k != 'all'}

    checking_specific_subreddits = SUBREDDITS['allowed'][0] != 'all'

    print_log("Beginning scan...")

    if checking_specific_subreddits:
        print_log("Scanning {} subreddits from whitelist...".\
                  format(len(SUBREDDITS['allowed'])))
        for subreddit in SUBREDDITS['allowed']:
            print_log("Scanning \"{}\"...".format(subreddit))
            for phrase in phrases.keys():
                print_log("Querying for comments containing phrase: \"{}\"...".\
                          format(phrase))
                raw_comments = pull_n_comments(phrase, PULL_COUNT, subreddit)
                to_be_added_comments += validate_comments(raw_comments)

    else:
        print_log("Scanning all non-blacklisted subreddits...")
        for phrase in phrases.keys():
            print_log("Querying for phrase: \"{}\"...".format(phrase))
            raw_comments = pull_n_comments(phrase, PULL_COUNT, '')
            to_be_added_comments += validate_comments(raw_comments)

    print_log("Done.")

    print_log("Filtering comments from blacklisted subreddits...")

    for comment_dict in to_be_added_comments:
        c = RedditComment(session, comment_dict)
        if c.subreddit not in new_comments:
            new_comments[c.subreddit] = []
        new_comments[c.subreddit].append(c)

    print_log("Done.")

    return new_comments


def pull_n_comments(phrase, count, subreddit=''):
    """ returns a list of dicts of comments """
    exclude = set(string.punctuation)

    # this works because the API accepts a blank value for the subreddit
    # parameter, while still returning all subreddits (the intended behavior)
    print_log("Pulling list of matching comments...")
    res = requests.get(COMMENT_API.format(phrase, count, subreddit))
    # list of dicts of comments
    comment_json = res.json()['data']
    print_log("Done.")

    for comment_dict in comment_json:
        comment_dict.update( {
            'body': ''.join(ch.lower() for ch in comment_dict['body']\
                            if ch not in exclude)
        })

    # if searching through "all", make sure that disallowed subreddits
    # are not added to the list of comments
    print_log("Removing comments from blacklisted subreddits...")

    if not subreddit:
        comment_json = [c for c in comment_json\
                       if c['subreddit'] not in SUBREDDITS['disallowed']]

    comment_json = [c for c in comment_json\
                    if len(PHRASE_PATTERNS[phrase].findall(c['body'])) != 0]

    print_log("Done.")
    return comment_json


def reply_to_comments(comment_list):
    print_log("Reply to {} comments...".format(len(comment_list)))
    for comment in comment_list:
        pass


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

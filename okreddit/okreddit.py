"""
okreddit
~~~~~~~~

:author: Sean Pianka
:reddit: cdrootrmdashrfstar
:email: me@seanpianka.com
:github: seanpianka
:twitter: seanpianka

"""
import string
import sys
import threading
import time
import webbrowser

import requests
import praw

import constants
import multithreading
from constants import (SLEEP_TIME, SUBREDDITS, POINT_THRESHOLD, COMMENT_API,
                       USER_AGENT, PREDEFINED_COMMENT, PHRASE_PATTERNS,
                       VERBOSITY_LEVEL, MAX_REPLIES_PER_CYCLE, PULL_COUNT,
                       DISABLE_PRAW_WARNING, MAX_THREAD_COUNT,
                       CLIENT_ID, CLIENT_SECRET)
from helpers import print_log, lcstrcmp, RedditComment


def run(phrases):
    """ Manages the login sequence using OAuth1 via the Reddit PRAW api
    package. Defines the USERNAME of the bot for use later during checks.
    Initializes the scanner, retrieves a list of curated comments, and
    initializes reply sequence for those comments. Repeats until interrupt.

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
        author_check = lcstrcmp(comment['author'], USERNAME)

        # assume replied to avoid duplicates
        reply_check = True
        for reply in comment['object'].replies:
            try:
                if reply and lcstrcmp(reply.author.name, USERNAME):
                    break
            except AttributeError:
                # account who replied has been deleted, no username
                continue
        else:
            reply_check = False

        return author_check or reply_check

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
            # TODO: check for comment being deleted

            # pulling comment replies
            try:
                comment['object'].refresh()
            except IndexError:
                # there are no replies to this comment
                # that is the assumed meaning of this exception
                pass

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

    for comment_dict in to_be_added_comments:
        c = RedditComment(session, comment_dict)

        # if there is no definition available, don't reply to comment
        if not c.definition: continue

        # if the subreddit doesn't have kv pair in new_comments dict
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
    print_log("Beginning reply sequence...")
    for subreddit, comments in comment_list.items():
        print_log("Replying to comments from {}...".format(subreddit))
        for comment in comments:
            print_log("Replying to comment ID: {}".format(comment.id))
            if not comment.definition:
                continue
            post_definition_reply(comment.obj,
                                  comment.word,
                                  comment.definition)
            print_log("Replied.")



def post_definition_reply(reply_to, word, definition):
    """

    """
    print_log("Posting reply...")
    try:
        reply_to.reply(PREDEFINED_COMMENT.format(word, definition))
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


if __name__ == '__main__':
    run(PHRASE_PATTERNS)

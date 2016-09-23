import datetime
import string
from constants import SHOW_LOGS, PHRASE_PATTERNS


class RedditComment(object):
    def __init__(self, session, comment_dict):
        self.id = "t1_{}".format(comment_dict['id'])
        self.body = comment_dict['body']
        self.author = comment_dict['author']
        self.subreddit = comment_dict['subreddit'].lower()
        self.thread_id = comment_dict['link_id']
        self.phrase = comment_dict['msg_phrase']
        self.permalink = comment_dict['link_permalink']
        self.obj = comment_dict['object']

        try:
            self.word = PHRASE_PATTERNS[self.phrase].findall(self.body)[0]
            print_log("Comment contained \"{}\".".format(self.word))
        except IndexError:
            self.word = None
            print_log("Failed to find any word in the comment.")

    def __repr__(self):
        return 'https://reddit.com{}'.format(self.permalink)


def print_log(msg, *args, **kwargs):
    if SHOW_LOGS:
        now = datetime.datetime.now()
        time_format = (now.year, now.month, now.day,
                       now.hour, now.minute, now.second)
        print("[{:02}-{:02}-{:02} {:02}:{:02}:{:02}]: {}".\
              format(*time_format, msg), *args, **kwargs)


def lcstrcmp(str1, str2):
    return str1.lower() == str2.lower()

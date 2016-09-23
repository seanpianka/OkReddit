import datetime
import random
import string

import lxml
import requests
from lxml import html

from constants import SHOW_LOGS, PHRASE_PATTERNS, DEFINE_API, MAX_DEFINITIONS


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
        finally:
            self.definition = define_word(self.word)

    def __repr__(self):
        return 'https://reddit.com{}'.format(self.permalink)

    def __str__(self):
        return 'https://reddit.com{}'.format(self.permalink)


def define_word(word):
    """

    """
    definition = ''

    if not word: return definition

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

    added_a_defn = False

    for form, defns in word_forms_defns.items():
        word_meaning = "As a **{}**, \"{}\" can mean:\n\n".format(form, word)
        definition += word_meaning
        random.shuffle(defns)
        for i, defn in enumerate(defns):
            # if there is no valid definition, then don't add it to the list
            if not defn:
                i -= 1
                continue
            if i == MAX_DEFINITIONS:
                break
            definition += "\n{}: {}\n".format(i + 1, defn)
            added_a_defn = True
        definition += "\n"

    if not added_a_defn: definition = ''
    return definition


def print_log(msg, *args, **kwargs):
    if SHOW_LOGS:
        now = datetime.datetime.now()
        time_format = (now.year, now.month, now.day,
                       now.hour, now.minute, now.second)
        print("[{:02}-{:02}-{:02} {:02}:{:02}:{:02}]: {}".\
              format(*time_format, msg), *args, **kwargs)


def lcstrcmp(str1, str2):
    return str1.lower() == str2.lower()

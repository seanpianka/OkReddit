"""
constants
~~~~~~~~~

"""
import configparser
import re


#=============================================================================#
#    CONFIGURATION FILES                                                      #
#=============================================================================#
OKREDDIT_CONF = 'okreddit.conf'
PHRASES_CONF = 'phrases.conf'
SUBREDDITS_CONF = 'subreddits.conf'
config = configparser.ConfigParser()
config.read(OKREDDIT_CONF)

#=============================================================================#
#   SUBREDDITS                                                                #
#=============================================================================#
SUBREDDITS = {
    'allowed': [],
    'disallowed': [],
}

with open(SUBREDDITS_CONF, 'r') as f:
    found_all = False

    for subr in list(map(lambda x: x.strip().lower(), f.read().splitlines())):
        subreddit = subr  # PEP8 gimmick
        if '#' not in subreddit and subreddit:
            if subreddit[0] != "-" and not found_all:
                if subreddit == 'all':
                    # if all is selected, don't add any other allowed subs
                    SUBREDDITS['allowed'] = ['all']
                    found_all = True
                    continue
                SUBREDDITS['allowed'].append(subreddit.lower())
            elif subreddit[0] == '-':
                SUBREDDITS['disallowed'].append(subreddit.lower())

#=============================================================================#
#   DICTIONARY API                                                            #
#=============================================================================#
DEFINE_API = 'http://google-dictionary.so8848.com/meaning?word={}'

#=============================================================================#
#   REDDIT COMMENTS API                                                       #
#=============================================================================#
COMMENT_API = 'https://api.pushshift.io/reddit/search?'\
              'q="{}"&limit={}&subreddit={}'

#=============================================================================#
#   COMMENT PHRASES TO MATCH                                                  #
#=============================================================================#
BASE_PATTERN = r"\b{}.(\w+)"

PHRASES_TO_LOOK_FOR = []
with open(PHRASES_CONF, 'r') as f:
    for phrase in list(map(str.strip, f.read().splitlines())):
        if '#' not in phrase and phrase:
            PHRASES_TO_LOOK_FOR.append(phrase.lower())

PHRASE_PATTERNS = {}
for phrase in PHRASES_TO_LOOK_FOR:
    PHRASE_PATTERNS[phrase] = re.compile(BASE_PATTERN.format(phrase))

#=============================================================================#
#   REDDIT PRAW API VARIABLES                                                 #
#=============================================================================#
CLIENT_ID = str(config.get('Authentication', 'client_id'))
CLIENT_SECRET = str(config.get('Authentication', 'client_secret'))
USER_AGENT = "OkReddit by /u/cdrootrmdashrfstar"
POINT_THRESHOLD = 0
MAX_DEFINITIONS = 5
VERBOSITY_LEVEL = 0
DISABLE_PRAW_WARNING = True

#=============================================================================#
#   BOT CONFIGURATION VARIABLES                                               #
#=============================================================================#
SHOW_LOGS = bool(config.get('Configuration', 'show-log'))
SLEEP_TIME = {
    "scan": 15,
    "delete": 1000,
}
MAX_REPLIES_PER_CYCLE = 1000
MAX_THREAD_COUNT = 15
PULL_COUNT = 100
PREDEFINED_COMMENT = "Found \"{}\", so here's your definition(s):\n\n" \
                     "{}\n\n---\n\n^^Thanks ^^for ^^using [^^OkReddit]" \
                     "(https://github.com/seanpianka/OkReddit)^^!\n\n" \
                     "^^^// [^^^About](https://www.reddit.com/r/okredditbot/" \
                     "comments/546cm7/about_okredditbot_how_it_works_etc/) " \
                     "^^^// [^^^Creator](http://reddit.com/u/" \
                     "cdrootrmdashrfstar) ^^^//"

 ^^^// [^^^About]() ^^^// [^^^Creator](http://reddit.com/u/cdrootrmdashrfstar) ^^^//

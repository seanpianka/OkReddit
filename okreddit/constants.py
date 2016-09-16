import configparser
import re


"""
    configuration files
"""
OKREDDIT_CONF = 'okreddit.conf'
PHRASES_CONF = 'phrases.conf'
SUBREDDITS_CONF = 'subreddits.conf'
config = configparser.ConfigParser()
config.read(OKREDDIT_CONF)

"""
    subreddits
"""
SUBREDDITS = {
    'allowed': [],
    'disallowed': [],
}

with open(SUBREDDITS_CONF, 'r') as f:
    for subreddit in list(map(str.strip, f.read().splitlines())):
        if '#' not in subreddit and subreddit:
            if subreddit[0] != "-":
                SUBREDDITS['allowed'].append(subreddit.lower())
            else:
                SUBREDDITS['disallowed'].append(subreddit.lower())

"""
    dictionary api
"""
DEFINE_API = 'http://google-dictionary.so8848.com/meaning?word={}'

"""
    comment phrases to match
"""
BASE_PATTERN = r"\b{}.(\w+)"

PHRASES_TO_LOOK_FOR = []
with open(PHRASES_CONF, 'r') as f:
    for phrase in list(map(str.strip, f.read().splitlines())):
        if '#' not in phrase and phrase:
            PHRASES_TO_LOOK_FOR.append(phrase.lower())

PHRASE_PATTERNS = {}
for phrase in PHRASES_TO_LOOK_FOR:
    PHRASE_PATTERNS[phrase] = re.compile(BASE_PATTERN.format(phrase))

"""
    reddit praw api variables
"""
USERNAME = str(config.get('Authentication', 'username'))
PASSWORD = str(config.get('Authentication', 'password'))
USER_AGENT = "OkReddit by /u/cdrootrmdashrfstar"
POINT_THRESHOLD = 0
MAX_DEFINITIONS = 5
VERBOSITY_LEVEL = 0
DISABLE_PRAW_WARNING = True

"""
    bot configuration variables
"""
SHOW_LOGS = bool(config.get('Configuration', 'show-log'))
SLEEP_TIME = {
    "scan": 15,
    "delete": 1000,
}
MAX_REPLIES_PER_CYCLE = 1000
MAX_THREAD_COUNT = 15
PREDEFINED_COMMENT = "Found \"{}\", so here's your definition(s):\n\n" \
                     "{}\n\nThanks for using [OkReddit]" \
                     "(https://github.com/seanpianka/OkReddit)!\n\n" \
                     "[Contact the Creator]" \
                     "(http://reddit.com/u/cdrootrmdashrfstar)."

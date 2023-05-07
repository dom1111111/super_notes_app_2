
KEYWORDS = {                # even single word combos MUST be tuples - don't foget the comma
    'wake_words': ('computer', ),
    'get':      ('get', 'return', 'retrieve', 'show', 'display', 'read'),
    'what':     ('what', "what's", 'what is'),
    'search':   ('search', 'find', 'seek', 'look'),
    'create':   ('create','make', 'new'),   # 'write', 'start', 'compose'
    'exit':     ('exit', 'terminate', 'stop'),
    'end':      ('end', 'finish', 'complete'),
    'shutdown': ('shutdown', 'shut down', 'bye', 'goodbye', 'good bye'),
    'app':      ('app', 'application', 'system'),
    'calculate':('calculate', 'calculator', 'math'),
    'note':     ('note', 'text', 'entry', 'page'),
    'task':     ('task', 'todo'),
    'recent':   ('recent', 'latest', 'last'),
    'current':  ('current', 'present', 'now'),
    'time':     ('time', ),
    'date':     ('date', ),
    'today':    ('today', 'todays', "today's"),
    'sound':    ('sound', 'audio', 'noise')
}

def get_keywords_str(*keys:str, all:bool=False):
    keywords = ''
    if all:
        # brings all command keywords into a list, removes duplicates, and joins them into a single string
        return ' '.join(list(dict.fromkeys([word for word_tup in KEYWORDS.values() for word in word_tup])))
    for key in keys:
        for word in KEYWORDS.get(key):
            keywords += word + ' '
        #keywords += ' '
    return keywords

# check if the specified keywords are present in text
def match_keywords(keyword_keys:tuple, text:str):
    assert isinstance(keyword_keys, tuple)
    match_count = 0
    for key in keyword_keys:
        keywords = KEYWORDS.get(key)
        for word in keywords:
            if word in text.lower():
                match_count += 1
                break
    # only return True if each keyword group gets at least one match
    if match_count >= len(keyword_keys):
        return True
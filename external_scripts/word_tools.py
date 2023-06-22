from datetime import datetime, timedelta

#------------------------
# Word maps

KEYWORD_MAP = {                 # even single word combos MUST be tuples - don't foget the comma
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

NUMBER_WORD_MAP = {
    'zero':      0,
    'one':       1,
    'two':       2,
    'three':     3,
    'four':      4,
    'five':      5,
    'six':       6,
    'seven':     7,
    'eight':     8,
    'nine':      9,
    'ten':       10,
    'eleven':    11,
    'twelve':    12,
    'thirteen':  13,
    'fourteen':  14,
    'fifteen':   15,
    'sixteen':   16,
    'seventeen': 17,
    'eighteen':  18,
    'nineteen':  19, 
    # tens:
    'twenty':    20,
    'thirty':    30,
    'forty':     40,
    'fifty':     50,
    'sixty':     60,
    'seventy':   70,
    'eighty':    80,
    'ninety':    90,
    # grand
    'hundred':   100,
    'thousand':  1000,
    'million':   1000000,
    'billion':   1000000000,
    'trillion':  1000000000000,
}

ORDINAL_NUMBER_WORD_MAP = {
    'first':        1,
    'second':       2,
    'third':        3,
    'fourth':       4,
    'fifth':        5,
    'sixth':        6,
    'seventh':      7,
    'eighth':       8,
    'nineth':       9,
    'tenth':        10,
    'eleventh':     11,
    'twelfth':      12,
    'thirteenth':   13,
    'fourteenth':   14,
    'fifteenth':    15,
    'sixteenth':    16,
    'seventeenth':  17,
    'eighteenth':   18,
    'nineteenth':   19, 
    # tens:
    'twentieth':    20,
    'thirtieth':    30,
    'fortieth':     40,
    'fiftieth':     50,
    'sixtieth':     60,
    'seventieth':   70,
    'eightieth':    80,
    'ninetieth':    90,
    # grand
    'hundredth':    100,
    'thousandth':   1000,
    'millionth':    1000000,
    'billionth':    1000000000,
    'trillionth':   1000000000000,
}

MATH_OPERATOR_WORD_MAP = {
    'plus':     '+',
    'minus':    '-',
    'times':    'x',
    'divided':  '/'
}

#---
# word tuples

NUMBER_WORDS = tuple(NUMBER_WORD_MAP) + ('oh', 'point')

ORDINAL_NUMBER_WORDS = tuple(ORDINAL_NUMBER_WORD_MAP)

WEEK_WORDS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
MONTH_WORDS = ('january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december')
_MISC_TIME_WORDS = ('am', 'pm', "o'clock", 'midnight', 'hours')     # 'hours' is needed for recognizing 24 hour time speach
TIME_WORDS = WEEK_WORDS + MONTH_WORDS + _MISC_TIME_WORDS

DURATION_WORDS = ('year', 'month', 'week', 'day', 'hour', 'minute', 'second')
DURATION_WORDS += tuple(w + 's' for w in DURATION_WORDS)

#TIME_WORDS_NUMBERS = TIME_WORDS + NUMBER_WORDS + ORDINAL_NUMBER_WORDS

#------------------------
# Word functions

def get_keywords_str(*keys:str, all:bool=False):
    keywords = ''
    if all:
        # brings all command keywords into a list, removes duplicates, and joins them into a single string
        return ' '.join(list(dict.fromkeys([word for word_tup in KEYWORD_MAP.values() for word in word_tup])))
    for key in keys:
        for word in KEYWORD_MAP.get(key):
            keywords += word + ' '
        #keywords += ' '
    return keywords

# check if the specified keywords are present in text
def match_keywords(keyword_keys:tuple, text:str):
    assert isinstance(keyword_keys, tuple)
    match_count = 0
    for key in keyword_keys:
        keywords = KEYWORD_MAP.get(key)
        for word in keywords:
            if word in text.lower():
                match_count += 1
                break
    # only return True if each keyword group gets at least one match
    if match_count >= len(keyword_keys):
        return True

#------------------------
# Number and math word functions

def words_to_number(num_words:str) -> int|float:
    """convert number words to a matching float or integer"""

    def words_to_int_str(text_num:str) -> str:
        num_list = reversed([str(NUMBER_WORD_MAP.get(word)) for word in text_num.split()])
        num_list = [word for word in num_list if word != 'None']
        overall_num = None
        last_num = None
        for num in num_list:
            if overall_num == None:
                overall_num = num
            # if this number is longer than overall: add both together as ints
            # unless overall is a zero, in which case: concatenate this number to the left of overall
            elif len(num) > len(overall_num):
                if int(overall_num) == 0:
                    overall_num = num + overall_num
                else:
                    overall_num = str(int(overall_num) + int(num))
            # if this number is the same lenth or shorter than overall:
            elif len(num) <= len(overall_num):
                # if last number is a grand starting with one, replace leading digit ('1') of overall with this number
                if len(last_num) >= 3:
                    overall_num = num + overall_num.replace('1', '', 1)
                # if last number same is a single or double, concatenate this number to left of overall
                # minus the length of last number from the right, but only if this number is a tens or grand and the last number was smaller than this one
                else:
                    last_len = len(last_num)
                    if int(num) >= 20 and len(num) > last_len: 
                        overall_num = num[:-last_len] + overall_num
                    else:
                        overall_num = num + overall_num
            last_num = num
            
        return overall_num

    #---
    if 'point' in num_words:
        overall_num = ''
        nums = num_words.split('point')
        for n in nums:
            overall_num += words_to_int_str(n) + '.'
        if overall_num:
            return float(overall_num[:-1])                  # the indexing removes the last added period
    else:
        return int(words_to_int_str(num_words))

#------------------------
# Time word functions

def words_numbers_to_duration(words_nums:list) -> timedelta:
    
    time_unit_sec_val = {
        'second':   1,
        'minute':   60,
        'hour':     3600,
        'day':      86400,
        'week':     604800,
        'month':    x,
        'year:':    31536000
    }

    # TESTING
    def time_addition_with_delta():
        now = datetime.now().astimezone()
        td = timedelta(weeks=4)

        added_t = now + td

        print(now)
        print(td)
        print(added_t)

    def time_addition_with_dt_only():
        now = datetime.now().astimezone()
        added_now = now.replace(month=now.month+1)

        print(now)
        print(added_now)

    time_addition_with_delta()
    print('\n')
    time_addition_with_dt_only()

    # operations:

    # 
        #print(datetime())

        # you can just make a function which returns datetime objects, all in a standard string
        # it has all of the same args as datetime.datetime, but with default values which use the current time
        # if no arguments are passed, it just returns the current time
        # >>> https://docs.python.org/3/library/datetime.html#datetime.datetime.replace - this basically does this


def words_numbers_to_time(words_nums:list) -> datetime:

    def get_frmt_code(word:str|int|float) -> str:
        if word in WEEK_WORDS:
            return '%A'
        elif word in MONTH_WORDS:
            return '%B'
        elif word in ('am', 'pm'):
            return '%p'
    
    # https://docs.python.org/3/library/time.html#time.strftime
        # + strptime
    # convert words in a specific string format code + a value (ex: %A, Wednesday)
    # use the complete str frmt code to compare the current time against the provided one, and minus the future time from the current
    # the resulting float value then returned from these can then be converted into a struct_time
    

#------------------------
# Sentence/message processing

def get_words_only(message:str) -> list[str|int|float]:
    """returns a list containing only the words, numbers, and times within a string message"""

    def remove_punctuation(word:str) -> str:
        """remove all non-alpha-numeric characters from the beginning and end of a word"""
        while True:
            if word:                                # break if word is empty! (will happen if a word has no alpha numeric chars)
                if not word[0].isalnum():
                    word = word[1:]                 # remove first character and restart loop
                    continue
                elif not word[-1].isalnum():
                    word = word[:-1]                # remove last character and restart loop
                    continue
            break
        return word

    def convert_number_words(message_words:list) -> list:
        words_only = []                             # holds the words and numbers (converted from words) without punctuation
        current_number_words = []                   # temporary number words to be processed into numbers

        def convert_current_num_words():
            # if current_number_words has any items, then convert them into a number, and add them to words_only
            if current_number_words:
                words_only.append(words_to_number(' '.join(current_number_words)))
                current_number_words.clear()        # reset current_number_words to keep this as a single seperate number

        def is_next_word_num(index:int) -> bool:
            """determine if the next item in message_words is a number word"""
            try:
                return message_words[i+1] in NUMBER_WORDS
            except:
                return False

        # ---main loop---
        for i, word in enumerate(message_words):
            # if the word is 'and' and it's in between 2 number words, with the previous word being anything higher than a tens, then treat it as part of the current number
            if word == 'and' and ((current_number_words and (NUMBER_WORD_MAP.get(current_number_words[-1]) >= 100)) and is_next_word_num(i)):
                pass                                # no need to add anything!
            # if the word is not any sort of number word, append it to words_only
            elif not word in NUMBER_WORDS:
                convert_current_num_words()         # first check if there's number words to convert 
                words_only.append(word)
            # if the word IS a number word
            else:
                # if the word is a number word (but not 'oh', 'point'), add it to current_number_words
                if word not in ('oh', 'point'):
                    current_number_words.append(word)
                # if the word is 'point' and it's in between 2 number words, then treat it as part of the current number (will become a decimal)
                elif word == 'point' and (current_number_words and is_next_word_num(i)):
                    current_number_words.append(word)
                # if there is "oh" next to any number word, then treat it as part of the current number as a zero
                elif word == 'oh' and (current_number_words or is_next_word_num(i)):
                    current_number_words.append('zero')               

        convert_current_num_words()                 # check if there's still number words to convert 

        return words_only
    
    def convert_time_words(message_words_nums:list) -> list:
        words_only = []                             # holds the words and numbers and times (converted from words) without punctuation
        current_time_words = []                     # temporary time words to be processed into time objects

        for i, word in enumerate(message_words_nums):
            pass


    # ---main function script---
    message_split = [remove_punctuation(w).lower() for w in message.split()]    # remove the punctuation and make all letter characters lowercase
    words_nums = convert_number_words(message_split)        # convert all number words into numbers (ints/floats)
    words_nums_times = convert_time_words(words_nums)       # convert all time-related words/numbers into times ()
    return words_nums_times
#------------------------
# Data

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

NUMBER_WORD_MAP = {
    'oh':        0,
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

NUMBER_WORDS = tuple(NUMBER_WORD_MAP)

MATH_OPERATOR_WORD_MAP = {
    'plus':     '+',
    'minus':    '-',
    'times':    'x',
    'divided':  '/'
}

#------------------------
# Word functions

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

#------------------------
# Number and math word functions

def words_to_integer(text_num:str) -> int:
    num_list = reversed([str(NUMBER_WORD_MAP.get(word)) for word in text_num.split(' ')])
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
        
    return int(overall_num)

def words_to_number(text_num:str) -> int|float:
    """convert number words to a matching float or integer"""
    if 'point' in text_num:
        overall_num = ''
        nums = text_num.split('point')
        for n in nums:
            overall_num += str(words_to_integer(n)) + '.'
        if overall_num:
            return float(overall_num[:-1])                  # the indexing removes the last added period
    else:
        return words_to_integer(text_num)

#------------------------
# Sentence/message processing

def get_words_only(message:str) -> list:
    """returns a list containing only the words within a message, and excludes any other characters (like punctuation)"""

    words_only = []                 # holds the words and converterted number words without punctuation
    current_number_words = []       # temporary number words to be processed into numbers

    def remove_punctuation(word:str) -> str:
        """remove all non-alpha-numeric characters from the beginning and end of a word"""
        while True:
            if word:                            # break if word is empty! (will happen if a word has no alpha numeric chars)
                if not word[0].isalnum():
                    word = word[1:]             # remove first character and restart loop
                    continue
                elif not word[-1].isalnum():
                    word = word[:-1]            # remove last character and restart loop
                    continue
            break
        return word

    #---

    # rules for non-number word number processing:
    # - if there is "point" in between 2 numbers, then combine them as a decimal (and also not seperated by sentence ending punctuation)
    # - if there is 'and' after the word 'hundred' but before other numbers, then combine the two numbers
    # - if there is "oh" next to any number word (but not if any punctuation is between them!), add that to numbers

    for og_word in message.split():

        word = remove_punctuation(og_word).lower()      # remove the punctuation and make all letter characters lowercase

        if word in NUMBER_WORDS:
            current_number_words.append(word)
        
        # if the word is 'point' and there is currently number being process, add it to current_number_words
        elif word == 'point' and current_number_words:
            current_number_words.append(word)
        # undo the above action if this word is not a number word
        elif (current_number_words and current_number_words[-1] == 'point') and (word not in NUMBER_WORDS): 
            words_only.append(current_number_words.pop())
            words_only.append(word)

        # if the word is 'and' and the last word in current_number_words is a hundred or higher, add it to current_number_words
        elif word == 'and' and current_number_words[-1] in NUMBER_WORDS[-5:]:
            current_number_words.append(word)
        # undo the above action if this word is not a number word
        elif (current_number_words and current_number_words[-1] == 'and') and (word not in NUMBER_WORDS): 
            words_only.append(current_number_words.pop())
            words_only.append(word)

        #elif word == 'oh':
        #    pass

        # otherwise if the word is not any of the above, append it to words_only
        # but also, first check if current_number_words has any items, and process them into a number, and add them to words_only
        else:
            if len(current_number_words) > 1:
                words_only.append(words_to_number(' '.join(current_number_words)))
                current_number_words.clear()
            elif len(current_number_words) == 1:
                words_only.append(current_number_words.pop())
           
            words_only.append(word)

    return words_only

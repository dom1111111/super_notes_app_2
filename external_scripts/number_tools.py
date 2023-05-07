NUMBER_WORDS = {
    'o':         0,
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
MATH_OPERATOR_WORDS = {
    'plus':     '+',
    'minus':    '-',
    'times':    'x',
    'divided':  '/'
}

def words_to_number(text_num:str):
    num_list = reversed([str(NUMBER_WORDS.get(word)) for word in text_num.split(' ')])
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

def calculate_from_words(s):
    pass

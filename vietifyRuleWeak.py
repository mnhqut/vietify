COMBINE_ACUTE = "\u0301"
COMBINE_DOT = "\u0323"
COMBINE_GRAVE = "\u0300"

NULL_MAPPING = "_"


ENDING_VOWEL_MAPPING: dict[str, str] = {
    # exact 1-1 correspondant
    "a": "a",
    "aɪ": "ai",
    "ɑŋ": "ang",

    "e": "e",
    "eɪ": "ây",

    "i": "i",
    # "ih": "i",
    "ik": "ich",
    "im": "im",
    "in": "in",
    "ip": "ip",
    "it": "it",
    "iŋ": "inh",
    "iɛ": "ia",

    "o": "o",
    "oʊ": "âu",

    "u": "u",
    "um": "um",
    "un": "un",
    "up": "up",
    "ut": "ut",
    "uk": "uc",
    "uɛ": "ue", ##
    # "uh": "ơ",
    "uŋ": "ung",

    
    "ɔ": "o",
    "ɔh": "o",
    "ɔk": "oc",
    "ɔm": "om",
    "ɔn": "on",
    "ɔp": "op",
    "ɔt": "ot",
    "ɔŋ": "oong",
    "ɔɪ": "oi",

    "ə": "ơ",
    # "əh": "ơ",
    "əj": "ơi",
    "ək": "ơc",
    "əm": "ơm",
    "ən": "ơn",
    "əp": "ơp",
    "ət": "ơt",
    "əŋ": "ơng",

    "ɛ": "e",
    # "ɛh": "ê",
    "ɛk": "éc",
    "ɛm": "em",
    "ɛn": "en",
    "ɛp": "ep",
    "ɛt": "et",
    "ɛŋ": "eng",


    # not exact equivalence in vietnamese 
    "aʊ": "ao",

    "ub": "up",
    "ib": "ip",
    "iɡ": "ig",
    "uɡ": "ug",
    "ɑɡ": "ac",
    "ɔb": "ob",
    "ɔɡ": "oog",
    "əb": "ơb",
    "əɡ": "ơg",
    "ɛb": "eb",
    "ɛɡ": "eg",

    # "j": "j",
    # "jaʊ": "jau",
    # "jeɪ": "jây",
    # "ji": "ji",
    # "joʊ": "jau",
    # "ju": "ju",
    # "jæ": "ye",
    # "jɑ": "ya",
    # "jɔ": "yo",
    # "jə": "jơ",
    # "jɛ": "je",
    # "jɪ": "y",
    # "jʊ": "iu",
    # "jəŋ": "giâng",
    "j": "i",
    "jaʊ": "iau",
    "jeɪ": "iây",
    "ji": "i",
    "joʊ": "iau",
    "ju": "iu",
    "jæ": "iae",
    "jɑ": "ia",
    "jɔ": "io",
    "jə": "ia",
    "jɛ": "iê",
    "jɪ": "i",
    "jʊ": "iu",
    "jəŋ": "iêng",

    "æ": "ae",
    "æb": "aep",
    "æk": "aech",
    "æm": "aem",
    "æn": "aen",
    "æp": "aep",
    "æt": "aet",
    "æŋ": "aeng",
    "æɡ": "aec",

    "ɑ": "ä",
    "ɑb": "äp",
    # "ɑh": "a",
    "ɑk": "äc",
    "ɑm": "äm",
    "ɑn": "än",
    "ɑp": "äp",
    "ɑt": "ät",


    "ɑɛ": "ae",


    "eɪt": "âyt",
    "eɪn": "âyn",

    #very similar to /i/ and /u/ just mostly length, slightly less forward/backward
    "ɪ": "i",
    "ɪb": "ib",
    # "ɪh": "i",
    "ɪk": "ich",
    "ɪm": "im",
    "ɪn": "in",
    "ɪp": "ip",
    "ɪt": "it",
    "ɪŋ": "inh",
    "ɪɛ": "ie",
    "ɪɡ": "ig",


    "ʊ": "u",
    "ʊb": "ub",
    "ʊk": "uc",
    "ʊm": "um",
    "ʊn": "un",
    "ʊp": "up",
    "ʊt": "ut",
    "ʊŋ": "ung",
    "ʊɡ": "ug",
}


LETTER_MAPPING: dict[str, str] = {
    # exact 1-1 correspondant
    " ": "",
    ",": "",
    "/": "",
    "ˈ": " ",
    "ˌ": "",

    # t aspiration rule
   "ˈt": "th",
    "ˌt": "th",
    "t": "t",  

    "a": "a",
    "b": "b",
    "d": "đ",
    "e": "e",
    "o": "ô",
    "f": "ph",
    "h": "h",
    "i": "i",
    "k": "k",
    "kw": "qu",
    "m": "m",
    "n": "n",
    "p": "p",
    "s": "x",
    "tʃ": "ch",
    "u": "u",
    "v": "v",
    "w": "w",
    "ŋ": "ng",

    "ɔ": "o",
    "ə": "ơ",
    "ɛ": "ê",
    "l": "l",

    "tɹ": "tr",

    "z": "z",
    # not exact equivalence in vietnamese 
    "dʒ": "dʒ",
    "ʒ": "ʒ",  ##gi
    "j": "j",
 
    "æ": "ae",
    "ɑ": "ä",
    "ɪ": "i",
    "ʊ": "u",

    "ɝ": "ơr",

    "ɡ": "g",
    "ɫ": "l",
    "ɹ": "r",
    "ʃ": "sh",

    "θ": "ss",
    "ð": "zz",
}

from sudachipy import tokenizer
from sudachipy import dictionary
tokenizer_obj = dictionary.Dictionary(dict_type="full").create()
mode = tokenizer.Tokenizer.SplitMode.A
text = '隣の人は、たくさん柿が食べられる。'
morphemes = tokenizer_obj.tokenize(text, mode)
for m in morphemes:
    if len(m.dictionary_form()) < 4:
        print(f"{m.dictionary_form()} \t\t {m.part_of_speech()[0]}")
    else:
        print(f"{m.dictionary_form()}\t {m.part_of_speech()[0]}")
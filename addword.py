import pickle
import sys
# file = sys.argv[2] if len(sys.argv) > 2 else "table.pkl"
words = sys.argv[1:]
table = pickle.load(open("table.pkl", 'rb'))

def add_words(words):
    total = 0
    ok = 0
    exists = 0
    for word in words:
        word = romaji.katakana2hiragana(word[:-1])
        i0 = word[0]
        l = min(len(word), 8)
        print(f"{word} ({l}, {i0})...", end="", flush=True)
        if l == 1:
            continue
        row = table[i0][l]
        # print(row[:10])
        wn = word + "\n"
        if wn not in table[i0][l]:
            table[i0][l] += (wn,)
            print("OK")
        else:
            print("EXISTS")

    print(f"total: {total}, ok: {ok}, exists: {exists}")
    # pickle.dump(table, open("table.pkl", 'wb'))


if __name__ == "__main__":
    add_words(sys.argv[1:])

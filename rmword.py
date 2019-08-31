import pickle
import sys
# file = sys.argv[2] if len(sys.argv) > 2 else "table.pkl"
words = sys.argv[1:]
table = pickle.load(open("table.pkl", 'rb'))
for word in words:
    i0 = word[0]
    l = min(len(word) - 1, 8)
    print(f"{word}...", end="", flush=True)
    wn = word + "\n"
    if wn in table[i0][l]:
        table[i0][l] = tuple(i for i in table[i0][l] if i != wn)
        print("OK")
    else:
        print("404")

pickle.dump(table, open("table.pkl", 'wb'))

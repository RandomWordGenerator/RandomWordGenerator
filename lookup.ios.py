import pickle
import random
from romaji import mapping

from websocket import create_connection

def send_text(text):
    print(f"Sending {repr(text)}...", end="", flush=True)
    try:
        ws = create_connection("ws://192.168.0.104:8307/service")
        assert ws.recv()
        ws.send(text.strip())
        print("SENT...", end="", flush=True)
        result = ws.recv()
        print(result)
        ws.close()
    except Exception:
        print("FAILED")

with open("table.pkl", 'rb') as f:
    table = pickle.load(f)

conv = {'１': 1, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9, '０': 0}

last_cmd = ""

while True:
    cmd = input("COMMAND: ")
    if not cmd:
        exit(0)
    if cmd == '\x1b[A':
        cmd = last_cmd
    k0 = cmd[:-1]
    k1 = int(conv.get(cmd[-1], cmd[-1]))
    if k0 not in table:
        k0 = mapping.get(k0, k0)
    l = table[k0][k1]
    # words = random.sample(l, k=min(10, len(l)))
    word = random.choice(l)
    # print(word)
    send_text(word)
    last_cmd = cmd

# Xian-jie xi-li-tou-ri

import pickle
import random
import time
import os
from romaji import romaji2hiragana, kana2romaji
import subprocess
from io import BytesIO
from PIL import Image
import pytesseract
import struct

def send_text(text):
    # os.system("adb shell input tap 732 1205")
    time.sleep(0.01)
    rmj = kana2romaji(text)
    print(f"Sending {repr(text)} ({rmj})...", end="", flush=True)
    try:
        # os.system(f"adb shell input text {rmj}")
        # subprocess.run(["adb", "shell", "input", "text", rmj])
        print("OK")
    except Exception:
        print("FAILED")
    time.sleep(0.005+0.001*len(rmj))
    # os.system("adb shell input tap 1167 1140")
    # time.sleep(0.01)
    # os.system("adb shell input tap 1167 1140")


def clear_text():
    os.system("adb shell input tap 732 1205")
    time.sleep(0.01)
    os.system("adb shell input keyevent KEYCODE_MOVE_END")
    os.system("adb shell input keyevent --longpress" + " KEYCODE_DEL" * 250)
    time.sleep(0.01)
    os.system("adb shell input tap 732 1205")

with open("table.pkl", 'rb') as f:
    table = pickle.load(f)

conv = {'１': 1, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9, '０': 0}

last_cmd = ""

def issue_word(kana, count):
    count = int(conv.get(count, count))
    if kana not in table:
        kana = romaji2hiragana(kana)
    l = table[kana][count]
    # words = random.sample(l, k=min(10, len(l)))
    word = random.choice(l)
    # print(word)
    send_text(word.strip())

def main():
    while True:
        cmd = input("COMMAND: ")
        if not cmd:
            # exit(0)
            status = check_status()
            if status:
                # print("STATUS:", status)
                issue_word(*status)
                continue
            else:
                continue
        elif cmd == 'run':
            status = check_status()
            # 0: opponent
            # None: game ended
            pending = False
            while status is not None:
                if pending:
                    if status == 0:
                        pending = False
                else:
                    if status != 0:
                        print("status:", status)
                        issue_word(*status)
                        pending = True
                # time.sleep(0.125)
                status = check_status()
        elif cmd.startswith("cl"):
            clear_text()
        else:
            if cmd == '\x1b[A':
                cmd = last_cmd
            issue_word(cmd[:-1], cmd[-1])
            last_cmd = cmd

# Xian-jie xi-li-tou-ri

def load_image():
    # process = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True)
    # bio = BytesIO(process.stdout)
    # bio.seek(0)
    # return Image.open(bio)
    # process = subprocess.run(["adb", "exec-out", "screencap"], capture_output=True)
    process = subprocess.Popen(["adb", "exec-out", "screencap"], stdout=subprocess.PIPE)
    # bio = process.stdout
    width = struct.unpack('i', process.stdout.read(4))[0]
    height = struct.unpack('i', process.stdout.read(4))[0]
    process.stdout.read(4)
    # Read until mark pixel
    pic = process.stdout.read((588 * width + 10) * 4)
    mark = process.stdout.read(4)
    if mark == b'\x00\x00\x00\xff':
        process.terminate()
        process.wait()
        return 0
    if mark != b'\xbf\x07\x07\xff':
        print("NG!", mark)
        process.terminate()
        process.wait()
        return None
    pic += mark + process.stdout.read()
    # import pdb; pdb.set_trace() #F3EC37
    process.wait()
    return Image.frombytes('RGBA', (width, height), pic)

def bin_img(img):
    img = img.convert('L')
    pix = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            if pix[x, y] > 100:
                pix[x, y] = 255
            else:
                pix[x, y] = 0
    return img

def check_status():
    img = load_image()

    if not img:
        return img
    if img.getpixel((10, 588)) != (191, 7, 7, 255):
        print("Still NG!")
        return False

    kana_img = bin_img(img.crop((625, 668, 815, 796)))
    count_img = bin_img(img.crop((631, 824, 818, 940)))

    kana = pytesseract.image_to_string(kana_img, lang="kana", config="--user-words ./kana-words --psm 10")
    count = pytesseract.image_to_string(
        count_img, lang="kana", config="--user-words ./count-words --psm 8")
    # print(f"Got {kana} x {count}")
    
    return (kana, int(count[0]))

if __name__ == '__main__':
    main()

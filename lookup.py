import pickle
import random
import time
import os
from romaji import romaji2hiragana, kana2romaji
import subprocess
from io import BytesIO
from PIL import Image, ImageChops, ImageStat
import pytesseract
import struct
from screenpixel import ScreenPixel
from collections import deque
from uiautomator import Device

device = Device()

ki_base = Image.open("ki.pcx")
gi_base = Image.open("gi.pcx")
recent_words = deque()


def kigi(image):
    diff_ki = ImageChops.difference(image, ki_base)
    diff_gi = ImageChops.difference(image, gi_base)
    ki_val = ImageStat.Stat(diff_ki).sum[0]
    gi_val = ImageStat.Stat(diff_gi).sum[0]
    print("ki", ki_val, "gi", gi_val)
    return "き" if ki_val < gi_val else "ぎ"


def send_text(text, active=True):
    # if active:
        # time.sleep(0.0025)
    # rmj = kana2romaji(text)
    print(f"Sending {repr(text)}...", end="", flush=True)
    # try:
        # os.system("adb shell input tap 732 1205")
        # os.system('adb shell am start -n eu.micer.clipboardservice/eu.micer.clipboardservice.EmptyActivity')
        # os.system(f'adb shell am startservice -a eu.micer.ClipboardService -e text "{text}"')
        # os.system('adb shell input keyevent 279')
        # os.system(f"adb shell input text {rmj}")
        # subprocess.run(["adb", "shell", "input", "text", rmj])
        # os.system("adb shell 'input tap 1167 1140 && input tap 1167 1140'")

        # os.system(
        #     f'adb shell "input tap 732 1205 && '
        #     f'am startservice -a eu.micer.ClipboardService -e text {text} && '
        #     f'input keyevent 279 && '
        #     f'input tap 1167 1140 && input tap 1167 1140 && input tap 1167 1140"')  # 答える

    device.click(732, 1205)
    time.sleep(0.1)
    device(className="android.widget.EditText").set_text(text)
    # os.system(f"adb shell am broadcast -a ADB_INPUT_TEXT --es msg '{text}'")
    time.sleep(0.1)
    device.click(1167, 1200)
    device.click(1167, 1200)
    # device.click(1167, 1200)
    print("OK")
    # except Exception as e:
    #     print("FAILED")
    # time.sleep(0.005+0.00060*len(rmj))
    # time.sleep(0.01)
    # os.system("adb shell input tap 1167 1140")


def clear_text():
    # os.system("adb shell input tap 732 1205")
    # time.sleep(0.005)
    # os.system("adb shell input keyevent KEYCODE_MOVE_END")
    # os.system("adb shell input keyevent KEYCODE_MOVE_END" + " KEYCODE_DEL" * 50)
    # #time.sleep(0.01)
    # os.system("adb shell input tap 732 1205")

    device.click(732, 1205)
    time.sleep(0.1)
    device(className="android.widget.EditText").set_text("")
    # os.system(f"adb shell am broadcast -a ADB_INPUT_TEXT --es msg '{text}'")
    # time.sleep(0.1)
    device.click(732, 1205)


with open("table.pkl", 'rb') as f:
    table = pickle.load(f)

conv = {'１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
        '６': 6, '７': 7, '８': 8, '９': 9, '０': 0}

last_cmd = ""


def issue_word(kana, count, active=True):
    count = int(conv.get(count, count))
    if kana not in table:
        kana = romaji2hiragana(kana)
    l = table[kana][count]
    # words = random.sample(l, k=min(10, len(l)))
    word = random.choice(l)
    while word in recent_words:
        word = random.choice(l)
    recent_words.append(word)
    if len(recent_words) > 30:
        recent_words.popleft()
    # print(word)
    send_text(word.strip(), active=active)


def automate(single=False):
    try:
        while True:  # between games
            status = check_status()
            # 1. Send words
            # 0: opponent
            # -1: round ended
            # -2: finding match
            pending = False
            while status == 0 or isinstance(status, tuple):  # between rounds
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
            recent_words = deque()
            
            if single:
                break
            # 2. Accept result
            # if status != -1:
            #     print('Bad status', status)
            #     return
            print("Game ended, go to title")
            os.system("adb shell input tap 1110 1200")  # タイトルへ
            time.sleep(0.25)
            print("Looking for new matching")
            os.system("adb shell input tap 730 1590")  # ランダムマッチ
            time.sleep(2)
            status = check_status()
            while status == -2:
                try:
                    status = check_status()
                except ValueError:
                    status = None
            # Opponent found. Wait for game to start.
            print("Matching found, wait 4s to start")
            time.sleep(4.5)
            print('Start new game.')

    except KeyboardInterrupt:
        return


def main():
    while True:
        cmd = input("COMMAND: ")
        if cmd == 's':
            # exit(0)
            status = check_status()
            if isinstance(status, tuple):
                # print("STATUS:", status)
                issue_word(*status)
        elif cmd == 'run':
            automate(single=True)
        elif not cmd:
            automate(single=False)
        elif cmd.startswith("cl"):
            clear_text()
        else:
            if cmd == '\x1b[A':
                cmd = last_cmd
            issue_word(cmd[:-1], cmd[-1])
            last_cmd = cmd

# Xian-jie xi-li-tou-ri


scp = ScreenPixel()


def load_image():
    return scp.grab_image()


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


def same_pixel(a, b):
    return all(abs(i-j) < 5 for i, j in zip(a, b))


def check_status(print_mark=False):
    img = load_image()

    if not img:
        return img
    mark = img.getpixel((2022, 540))
    if print_mark:
        print("Mark:", mark)
    if same_pixel(mark, (0, 0, 0, 255)):
        # Not our round
        return 0
    if same_pixel(mark, (60, 63, 60, 255)):
        # Game ended
        print("Round endnd", mark)
        return -1
    if same_pixel(mark, (184, 186, 183, 255))\
            or same_pixel(mark, (246, 248, 245, 255))\
            or same_pixel(mark, (211, 214, 211, 255)):
        # print("Finding match", mark)
        return -2

    # os.system("adb shell input tap 732 1205")
    # time.sleep(0.01)

    kana_img = bin_img(img.crop((2453, 548, 2581, 655)))
    count_img = bin_img(img.crop((2474, 661, 2590, 751)))

    kana = pytesseract.image_to_string(
        kana_img, lang="kana", config="--user-words ./kana-words --psm 10")
    count = pytesseract.image_to_string(
        count_img, lang="kana", config="--user-words ./count-words --psm 8")
    # print(f"Got {kana} x {count}")

    if kana == 'き':
        # separate ki, gi
        kana = kigi(kana_img)
    elif kana == '':
        kana = 'ほ'
    return (kana, int(count[0]))


if __name__ == '__main__':
    main()

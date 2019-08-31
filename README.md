# RWG: an Experiment on Semi-Automated AI (?) Agent for Genkai Shiritori Mobile

Few days ago, a new game, *Genkai Shiritori Mobile (GSM)*, was released by Baton Co., Ltd. and a web media and YouTubers team QuizKnock. Shiritori is a traditional Japanese word game where each player says a new word that starts with the last letter (or rather *kana*) of the previous word. Genkai Shiritori is a game originated from QuizKnock where they added a few new rules on top of the simple Shiritori game, including:

- Including a random factor of playing cards: the next player must say a word with the number of  on the card drawn.
- Time limit: each player has a total of 5 minutes of time per game

After the Genkai Shiritori video series has gain popularity on YouTube, QuizKnock then modified the rules further and made into a mobile game. This article is introducing my analysis, attempts and thoughts on building a semi-automated AI (?) agent, which I later named it as *Random Word Generator*.

## Analysis of the game

Similar to other popular games like Scrabble and Boggles, Shiritori strongly relies on dictionaries. Luckily, a developer of the game, @imadake398yen has revealed the base dictionary used in a tweet.

[https://twitter.com/imadake398yen/status/1164291987169669120?s=09](https://twitter.com/imadake398yen/status/1164291987169669120?s=09)

The article in the tweet has linked to a GitHub repository of a dictionary used for NLP, [`mecab-ipadic-NEologd`](https://github.com/neologd/mecab-ipadic-neologd). We are only interested in the type of words and pronunciations.

For the common rule of Shiritori, only nouns are extracted from the dictionary. These words are then sent through a python script and doing some postprocessing:

- Convert to hiragana
- Filter out words that ends with ん
- Split into slots per starting word and length of words

## Iterations

### Iterations 0: Simple lookup script

At the beginning, I have

    cat Noun.csv Noun.adverbal.csv Noun.org.csv Noun.place.csv Noun.proper.csv Noun.verbal.csv mecab-user-dict-seed.* > words.csv
    cat words.csv | cut -d ’,’ -f12 > ./words-kana

After that, a pretty simple script is written to go through each line in the file, convert katakana to hiragana, then add words into respective slots in the table. The table is really easy to build, in Python type hint notation, it’s a `Dict[str, Dict[int, Tuple[str, ...]]]`. The outer dict is for kana, that shall only include valid kana as a beginning kana for a word, this can filter out some other invalid characters such as alphabets and numbers (although that is not common in this dataset). The inner dict is for the length of word, per the rule of GSM, the only valid lengths are 2 to 7 and “8+” where the latter takes any word that’s 8 kana or longer. The reason why tuple is used against other common options like set and list is that tuple is more memory saving when loaded for query and at the same time valid for random choice method in the standard library.

💡 *Fun fact*: different from common Shiritori rules, GSM included the uncommon ゔ as an option. Some players on Twitter even complained that their phone cannot type that kana due to outdated phone models. But in fact they can just install another keyboard like Gboard on Play Store instead of replacing their phone just for a game.

The table is then dumped into a file with pickle for later use.

For the lookup script, it’s even simpler. A script with an infinite loop keep query for a kana and a number, then print 5 random choices of valid words. I believe that should be really simple to write out, so I won’t post it out here.

In the first iteration, I was only querying words from the dictionary and typing out myself. Later on, I realised my typing speed on my iPad touchscreen is still not fast enough. So I moved on to the second iteration.

### Iteration 1: Auto typing (iOS)

I was trying to look for some ways to automate typing process. **USB HID** is too hard for me deal with for now as I don’t have any Arduino or similar device with me. I was also trying to look into **Bluetooth HID** solutions available for macOS like [`noble`](https://github.com/noble/noble) and [`bleno`](https://github.com/noble/bleno) until I realised I can just use a ready-made **type-over-Wi-Fi keyboard** and send web requests instead.

After some searches on the App Store, I found this nice and free [AirType](https://apps.apple.com/us/app/airtype-type-from-your-computer/id922932291) which does this job pretty nicely.

AirType fires up a web server listening at a port shown on the keyboard. Looking at the traffic of the web page hosted, it looks like AirType is using a websocket to send the text typed, without any encoding or formatting. Thus I just wrote a 4-liner using an one-off websocket client with [Python Websockets](https://pypi.org/project/websockets/) to “type” text into the game.

At this point of time, I was able to automate typing partially, but I still need to activate the text box and tap send manually.

As I almost gave up with my non-jailbroken iPad due to its lack of customisability, I found out that there is an Android version of the game. Then I started to move on to the next iteration.

### Iteration 2: Auto submission (Android)

Once I’m on Android, there are much more stuff that I can do with it. Of course I have tried stuff like ordinary decompilation and packet sniffing,  but the game is built with Unity + Firebase + certificate pinning, and I don’t want to dig into all of that hard binary/assembly stuff, then I just went back to automate Android which seems much easier to start with.

Surprisingly not surprising, Android has already provided a few commands for typing (`input text`) and screen tapping (`input touch`). With that, I can just read off the screen and type the next “command”, and the script will do the rest.

With that, it still takes about a few minutes of life to finish a game. I then looked into further automate the game.

### Iteration 3: Automate a full game

To automate a full game, there are 2 factors needed to be considered: when is my round, and what to type. Both of them relies on the current screen content. Fortunately, Android has also provided a command (`screencap`) to get the current screenshot.

To solve the first problem, we just need to monitor the colour of a specific pixel (marking pixel) on the screen, namely any pixel in the blinking box where your round is ready. We only start our round when the pixel is red.

To solve the second problem, which is harder that the first one, we need to know what word is given from the opponent, and what is the number of kana we need to send out. The first thing came to my mind is OCR (optical character recognition), and its most popular local solution, [Tesseract](https://github.com/tesseract-ocr/). Tesseract is a wonderful local OCR solution with a variety of strategies and language training data built in. But the sad thing is, the pre-trained Japanese language data of Tesseract doesn’t seem to play well with the font used in the game, [M+ Type-1 Heavy](https://mplus-fonts.osdn.jp/) ([Google Fonts](https://fonts.google.com/specimen/M+PLUS+1p)), in term of hiragana.

As the set of characters we need to recognise is rather small (just most hiragana, numerals and plus sign), I decided to train my own set of “language” for the game. While I was trying to build the Tesseract training toolkit my macOS, there’s always something wrong that prevented me from building it. I had no choice but to install Docker on my laptop and ran the training toolkit in a container. The training result ended up performing really well on the screenshots, except sometimes it messes up き with ぎ, and missing out ほ for some reason.

After the OCR engine is ready, I can just crop out the relevant boxes from the screenshot, and run Tesseract with [PSM 10](https://github.com/tesseract-ocr/tesseract/blob/master/doc/tesseract.1.asc) to get the set of data needed.

### Iteration 4: Speed up the automation

While I was trying to let my automation play a few games, I found out that the script is running really slow. The screenshot command is running only a few times every 10 seconds, same for input commands.

For screenshots, I have tried to let the command to emit raw image data instead of an encoded PNG picture. And in this way I can drop off rest of the picture when the marking pixel is not active. But when I try to do this, the unfinished `screencap` commands are quickly draining off my RAM and kicking off all other apps in my phone when it can. When I try to wait for the previous process to finish before issuing a new one, the process wouldn’t improve that much in turn.

Then I was looking into some ways to stream the screen to my computer. After some searches, I found [`scrcpy` from Genymobile](https://github.com/Genymobile/scrcpy), the company behind Genymotion, that can do a very decent streaming over ADB. Sadly, the app is written in C, and [didn’t plan to expose any API](https://github.com/Genymobile/scrcpy/issues/399). I then have to take screenshot from the OS instead. Using [PyObjC](https://pypi.org/project/pyobjc/) — Python’s wrapper for Objective C interfaces, the screenshot speed can reach around 15 fps on my laptop. I modified the code from [this answer](https://stackoverflow.com/questions/12978846/python-get-screen-pixel-value-in-os-x/13024603#13024603) a bit to [feed the raw image into `pillow`](https://stackoverflow.com/questions/3397157/how-to-read-a-raw-image-using-pil).

For the input part, every `input` command is in fact [firing up a Java applet](https://stackoverflow.com/a/34443868/1989455) in the background, which can be really slow for consecutive operations. Many have suggested to use `sendevent` instead, but that could be very tedious when issuing complex touch commands, and that doesn’t seem to work well with keyboard input. For keyboard inputs, I noticed that I can take a similar strategy as I did for iOS, using a special keyboard for typing. There’s an app called [ADBKeyBoard](https://github.com/senzhk/ADBKeyBoard) that is designed to feed text to a keyboard using ADB, it even emphasised on its Unicode support (`input text` is actually sending keycodes instead of strings, so it has to rely on the keyboard app to type Unicode stuff).

[senzhk/ADBKeyBoard](https://github.com/senzhk/ADBKeyBoard)

After some researches, I’ve found out an even better solution, [UI Automator](https://developer.android.com/training/testing/ui-automator) — a toolkit in Android to perform UI based automated tests. Using [a Python wrapper](https://github.com/xiaocong/uiautomator) of it, touch input could be really fast. UI Automator can also manipulate content in an EditText widget, that can even skip any keyboard overhead.

[UI Automator | Android Developers](https://developer.android.com/training/testing/ui-automator)

### Side note: A guess on GSM’s time lapse bug

During the game, I have also experienced the bug where the timing of game goes crazy: unexpected drop of 10+ seconds on each answer. Back then I was using a rather common name. I then changed my name to a rather uncommon one, and I didn’t encounter that strange bug after that. I’m guessing that somewhere in the server, the backend program is using one’s name as key to store their timer instead of unique IDs.

### Iteration 5: Automation between games

Since I’m already here, why can’t I go a step further to automate even between games? After paying about $2 to remove the ads between games, everything else becomes rather simple. The marker pixel I set above seems can also detect end of game state (when the pixel turns dark grey). Then the process will be like:

1. When marking pixel turns dark grey (match ended), tap “タイトルへ” (Back to home screen).
2. Wait until the pixel turn white (at the home screen), tap “ランダムマッチ” (Random match).
3. Wait until the pixel turn light grey (when it actually starts to look for matches).
4. Wait until the pixel changes colour once again to either black or dark red (that a match is found and ready to start)
5. Wait for 4 seconds and to play the new game.

This would completed a game cycle.

### Miscellaneous: Dictionary update

Despite the dictionary used is based what is GSM is also using, it seems that there are still a few words that are in my dictionary but not recognised by the game, on the other way, some words submitted by the opponents are not in my dictionary either. I’ve written a few scripts to add and remove words from the dictionary.

Digging into the storage section of the app, there is a particularly large preference file in the shared preference folder. It stores past 300 words used by each side of the game in a JSON string encoded using URL encoding as a preference value, and the preference file itself is an XML. Despite kinda strange, that’s still somewhat easy to process with all the standard libraries in Python. I wrote a script to retrieve the preference file using Root permission with ADB and automatically add unknown words from opponents to the table.

## Pitfalls

Due to the way the game interaction is designed, it is relatively hard to include a check of invalid word from using screenshot capture alone, as the error is only shown by a shaking text box. That is a reason why the agent is considered as “semi-automated”. It would just stuck there and do nothing once a word is not recognised by the game. The agent could also stuck during network congestion, and spitting a word that’s already used by the opponent. (Words used by the agent itself is already recorded to prevent collisions.)

## Possible future improvements

- A timer of 3-5 seconds could be set after sending out a word and check if it is still our round. This can be a workaround when we submitted a word that the game doesn’t recognise.
- We could OCR word from opponents while our round comes, so as to avoid collision with words from opponents.
- Typing strategy can be replaced with UIAnimator swipe commands once the new [in-game keyboard](https://mobile.twitter.com/imadake398yen/status/1164789183807778816) is released. (But why not just keep using the old version if they didn’t stop from the server-side? :P)

  [https://mobile.twitter.com/imadake398yen/status/1164789183807778816](https://mobile.twitter.com/imadake398yen/status/1164789183807778816)

- Observe the ads pattern between games in order to fully automate games without other ad-blocking strategies. (Or probably an ad blocker system-wide or on an router should be easier that that, and of course much faster)
- Use percentage on screen size rather than hardcoded coordinates for information retrieval from screenshots.
- Clean up code and add more comments for better readability.

## Trivia

- Name of this project, Random Word Generator, is originated from an item of a popular Virtual YouTuber, Kizuna AI. I simply found this name matching this project very well, thus choosing this name.
- The dominant strategy of the top rankers are using user dictionaries of their keyboard apps. The strategy utilises the fact where you can assign your typing sequence and text separately (more like a shortcut dictionary where “omw” can be assigned to “on my way”). Words with difficult beginning kana and length are added to the dictionary in a similar way like our *table*, e.g. “あま” gives “あんとにおいのき” (ま is on button 7 on a T9 layout). Disadvantage of this method is that it’s vulnerable to opponent’s attack on a single starting letter, and one could simply run out of words to go against with.

## Source code

Source code used in this project, and the table compiled, can be found in this code repository. Note that there are a lot of hardcoded values and the code is super messy to read. Try to refer back to this article when you are lost trying to follow the source.

### Files

- `lookup.py`: the main script
- `lookup.adb.py`: the main script at the last ADB-based iteration
- `lookup.ios.py`: the main script at the last iOS-based iteration
- `addword.py`: Add words to the table, use as `python3 addword.py たんごいち たんごに たんごさん`
- `rmword.py`: Delete words from the table, use as `python3 addword.py たんごいち たんごに たんごさん`
- `addxmlword.py`: Add words from the Android XML preference file.
- `table.pkl`: Lookup table of words.
- `count-words`, `kana-words`: Word list used by Tesseract for getting counts or kana
- `kana.traineddata`: Tesseract trained model (v3) on hiragana, numerals and plus sign on M+ 1c Heavy font.

\#ランワ生 \#ランダムワード生成器
import sys
import xml.etree.ElementTree as ET
import json
from urllib.parse import unquote
from addword import add_words


tree = ET.parse(sys.argv[1])
root = tree.getroot()
history = root.find("./string[@name='History']").text
json_data = unquote(history)
data = json.loads(json_data)
words = [i['_body'] for i in data['_opponents']]
# add_words(words)
print(f"add_words({words})")

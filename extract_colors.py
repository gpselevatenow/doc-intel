import requests
from bs4 import BeautifulSoup
import re

url = "https://elevatenow.tech"
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Find inline styles with colors
styles = soup.find_all('style')
css_text = " ".join([s.get_text() for s in styles])

# Extract hex colors
colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', css_text)
# Also look at inline style attributes in body
for el in soup.find_all(style=True):
    colors.extend(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', el['style']))

from collections import Counter
print("Most common colors:")
for c, count in Counter(colors).most_common(10):
    print(c, count)
    
print("Tailwind classes:")
body_html = str(soup.body)
# just looking for typical color classes like bg-blue-600, text-purple-500
bg_colors = re.findall(r'bg-[a-z]+-[0-9]{3}', body_html)
text_colors = re.findall(r'text-[a-z]+-[0-9]{3}', body_html)
print("BG:", Counter(bg_colors).most_common(5))
print("Text:", Counter(text_colors).most_common(5))

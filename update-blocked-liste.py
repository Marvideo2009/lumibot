from urllib.request import urlopen
import numpy as np

with urlopen("https://blocklistproject.github.io/Lists/everything.txt") as txtFile:
    content = txtFile.read().decode()

lines = content.split("\n")

lines = lines[16:]

index = 0

for line in lines:
    lines[index] = "https://" + line[8:]
    index += 1

lines = [
    "https://google.com",
    "https://www.google.com",
    "https://facebook.com",
    "https://www.facebook.com",
    "https://youtube.com",
    "https://www.youtube.com",
    "https://wikipedia.org",
    "https://www.wikipedia.org",
    "https://github.com",
    "https://www.github.com",
    "https://trustpilot.com",
    "https://www.trustpilot.com",

    # anti-tracking
    "https://doubleclick.net",
    "https://www.doubleclick.net",
    "https://googletagmanager.com",
    "https://www.googletagmanager.com",
    "https://google-analytics.com",
    "https://www.google-analytics.com",
    "https://twitter.com",
    "https://www.twitter.com",
    "https://instagram.com",
    "https://www.instagram.com",
    "https://linkedin.com",
    "https://www.linkedin.com",
    "https://tiktok.com"
    "https://www.tiktok.com"
] + lines

print(len(lines), " lignes")

content = '\n'.join(lines)

with open('blocked-site.txt','w') as output:
    output.write(content)
#!/usr/bin/env python3

import html
import os
import sys
import time
import bleach
import feedparser
import requests
from bs4 import BeautifulSoup

print("RSS-to-telega: Starting...")

# Set the channel ID's and Telegram API tokens
channel_id = -123
api_token = "123:xyz"
monitor_chat_id = 123
monitor_token = "123:xyz"

# Set the URL of the RSS feed
feed_url = "https://example.com/rss"

# Define a list of allowed tags https://core.telegram.org/bots/api#html-style
allowed_tags = ['a', 'b', 'i', 'u', 's', 'code', 'pre']

# Parse the RSS feed
feed = feedparser.parse(feed_url)

# Get the list of posts that have already been sent
sent_posts_file = "/path/to/file/sent_posts.txt"
sent_posts = []
if os.path.exists(sent_posts_file):
    with open(sent_posts_file, "r") as f:
        for line in f:
            sent_posts.append(line.strip())


# Truncate by word
# def smart_truncate(selftext, length=500, suffix='... '):
#    if len(selftext) <= length:
#        return selftext
#    else:
#        return selftext[:length].rsplit(' ', 1)[0] + suffix

# Truncate by paragraph
def truncate_html_text_by_paragraphs(html_text, num_paragraphs=2):
    # Create a BeautifulSoup object for parsing HTML
    soup = BeautifulSoup(html_text, 'html.parser')
    # Find all paragraphs in the HTML
    paragraphs = soup.find_all('p')
    # Keep only the first num_paragraphs paragraphs
    truncated_paragraphs = paragraphs[:num_paragraphs]
    # Reconstruct back into HTML
    truncated_html = ''.join(str(p) for p in truncated_paragraphs)
    return truncated_html


# Iterate through the posts in the RSS feed
for post in feed.entries:
    # Check if the post has already been sent
    if post.guid in sent_posts:
        continue

    print("RSS-to-telega: New post found", post.guid)
    # print(post.description)
    # Truncate by paragraph
    cleaned_descr = truncate_html_text_by_paragraphs(post.description, num_paragraphs=2)
    # Clean HTML-tags
    cleaned_descr = bleach.clean(cleaned_descr, allowed_tags, strip=True)
    # Some replaces if needed
    # cleaned_descr = re.sub(r'<br /><br />', '<br />', cleaned_descr)
    # Truncate by word
    # cleaned_descr = smart_truncate(cleaned_descr)
    # Decode HTML entities like &rsquo;, &rdquo;, &oacute;, &nbsp; etc.
    cleaned_descr = html.unescape(cleaned_descr)
    # Ellipsis at the end of a sentence
    cleaned_descr = cleaned_descr + ".."
    # print(cleaned_descr)

    # The content of tags in RSS feeds may vary. Replace if necessary.
    message = f"\n\n<b><a href=\"{post.link}\">{post.title}</a></b>\n\n{cleaned_descr}\n\n"

    response = requests.post(f'https://api.telegram.org/bot{api_token}/sendMessage', json={
        'chat_id': channel_id,
        'text': message,
        'parse_mode': 'HTML'
    })

    # Error monitoring
    if 200 <= response.status_code < 300:
        # The request was successful
        print("RSS-to-telega: Posted", post.guid, post.title)
    else:
        # There was an error
        error_info = f'RSS-to-telega: An error occurred: {response.json()} \n post.guid'
        print(error_info)
        url = f"https://api.telegram.org/bot{monitor_token}/sendMessage?chat_id={monitor_chat_id}&text={error_info}"
        requests.get(url)
        sys.exit(1)

    # Add the post to the list of sent posts
    with open(sent_posts_file, "a") as f:
        f.write(post.guid + "\n")
    print("RSS-to-telega: Wrote", post.guid, "to", sent_posts_file)

    # Not too fast (time in seconds before next post)
    # print("RSS-to-telega: sleep a little")
    time.sleep(7)

print("RSS-to-telega: Finished")

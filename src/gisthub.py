"""
gisthub.py - view and controller

GistRSS - Generates a valid RSS/Atom feed for a github user's gist history.

@author: Adam Thurlow <thurloat>
@contact: thurloat <at> gmail <dot> com
"""

import logging
import json

from dateutil.parser import parse
from google.appengine.api import memcache, urlfetch
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.formatters.html import escape_html
from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from time import gmtime, strftime

DATE_FORMAT = "%a, %d %b %Y %H:%M:%S +0000"
GIST_URL = "https://api.github.com/users/%s/gists"

def memoize(keyformat, time=60):
    """
    Decorator to memoize functions using memcache.
    """
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            key = keyformat % args[0:keyformat.count('%')]
            data = memcache.get(key)
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            memcache.set(key, data, time)
            return data
        return wrapper
    return decorator

#TODO: Optimize cache length
@memoize("raw: %s", time=1200)
def get_raw(files):
    """
    Head to GitHub and get the raw content of the gist

    @param files - `files` key of the gist API response.
    @return: some html to embed within the description of the RSS item.
    """

    raw = []
    formatter = HtmlFormatter(noclasses=True)

    max_i = 5
    for k, value in files.items():

        max_i -= 1
        if max_i is 0:
            break

        gist = value
        url = gist['raw_url']
        try:
            result = urlfetch.fetch(url)
        except urlfetch.DownloadError:
            # retry the download
            result = urlfetch.fetch(url)
            logging.error("Died on get_raw(%s)", url)

        if result.status_code == 200:
            try:
                lexer = get_lexer_for_filename(gist['filename'])
            except Exception:
                lexer = get_lexer_by_name('text')

            c = result.content
            content = "%s ....." % c[0:2999] if len(c) > 3000 else c 
                                    
            raw.append(FEED_GIST_TEMPLATE % {
                "raw_url": url,
                "filename": gist['filename'],
                "rendered_codes": highlight(content, lexer, formatter)
                })

    return ''.join(raw)

@memoize("feed: %s", time=600)
def get_feed(username):
    """
    Uses the github gist API and constructs an RSS feed for it
    """

    url = GIST_URL % username
    try:
        result = urlfetch.fetch(url)
    except urlfetch.DownloadError:
        result = urlfetch.fetch(url)
        logging.error("Died on get_feed(%s)", url)

    if result.status_code != 200 or result.content == 'error':
        return 'error'

    feed = [
        FEED_HEAD_TEMPLATE % {
            "username": username,
            "pub_date": strftime(DATE_FORMAT, gmtime())
        },
    ]

    obj = json.loads(result.content)

    for i in range(0, len(obj) if len(obj) < 10 else 10):
        gist = obj[i]
        date = parse(gist['created_at'])
        desc = gist['description']
        title = escape_html(
            ', '.join(
                map(lambda f: f[1]['filename'], gist['files'].items())
            ) if desc is None else desc)

        feed.append(ITEM_TEMPLATE %
            {
                "id": gist['id'],
                "author": username,
                "title": title,
                "post_date": date.strftime('%b %d, %Y'),
                "gist_url": gist['html_url'],
                "raw_gist": get_raw(gist['files']),
                "pub_date": date.strftime(DATE_FORMAT),
            }
        )
    feed.append(FEED_FOOT_TEMPLATE)
    return ''.join(feed)

FEED_HEAD_TEMPLATE = """
<rss version="2.0">
    <channel>
        <title>%(username)s</title>
        <link>http://gist.github.com/%(username)s</link>
        <description>
            A pretty RSS feed for %(username)s 's Github Gists
        </description>
        <pubDate>%(pub_date)s</pubDate>"""

FEED_FOOT_TEMPLATE = """
    </channel>
</rss>"""

ITEM_TEMPLATE = """
<item>
    <author>%(author)s</author>
    <title>%(title)s</title>
    <description>
        <div style="width: 100%%;">
        <span style="float:right;"> posted: %(post_date)s</span>
        <b>gist</b>: <a href="%(gist_url)s">%(id)s</a>
        </div>
        <hr />
        %(raw_gist)s
    </description>
    <link>%(gist_url)s</link>
    <pubDate>%(pub_date)s</pubDate>
    <comments>%(gist_url)s#comments</comments>
</item>"""

FEED_GIST_TEMPLATE = """
<table width="100%%">
    <tr>
        <th style="background-color:#DDD;">
            <h3>
            <a href="%(raw_url)s">%(filename)s</a>
            </h3>
        </th>
    </tr>
    <tr>
        <td style="background-color:#F8F8F8;color:#000">
            %(rendered_codes)s
        </td>
    </tr>
</table>
<hr />"""

"""
gisthub.py - view and controller

GistRSS - Generates a valid RSS/Atom feed for a github user's gist history.

@author: Adam Thurlow <thurloat>
@contact: thurloat <at> gmail <dot> com
"""
import jsonpickle
jsonpickle.load_backend('django.utils.simplejson', 'dumps', 'loads', ValueError)

import urllib2
from google.appengine.api import memcache
from google.appengine.api import urlfetch
from time import gmtime, strftime
from dateutil.parser import parse

def memoize(keyformat, time=60):
    """Decorator to memoize functions using memcache."""
    def decorator(fxn):
        """Decorator fxn"""
        def wrapper(*args, **kwargs):
            """wrapper that takes makes my key from the args"""
            key = keyformat % args[0:keyformat.count('%')]
            data = memcache.get(key)
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            memcache.set(key, data, time)
            return data
        return wrapper
    return decorator

def html_escape(text):
    """does a string replace on html characters"""
    text = text.replace('&', '&amp;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#39;')
    text = text.replace(">", '&gt;')
    text = text.replace("<", '&lt;')
    return text


@memoize("raw: %s %s", time=120)
def get_raw(files, repo):
    """
    Head to GitHub and get the raw content of the gist
    
    @return: excaped string of code
    """
    
    raw = []
    for i in range(0, len(files) if len(files) < 6 else 5):
        gist = files[i]
        url = "http://gist.github.com/raw/%s/%s" % (repo, urllib2.quote(gist))
        result = urlfetch.fetch(url)
        raw.append("""
            <table width='100%%'><tr><th style='background-color: #DDDDDD;'>
            """)
        raw.append("<h3><a href='%s'>%s</a></h3>" % (url, gist))
        raw.append("</th></tr>")
        if result.status_code == 200:
            raw.append("""
                <tr><td style='background-color: ghostWhite; color: black'>
                """)
            raw.append(u'<pre>')
            pre_str = unicode(
                              result.content 
                                if len(result.content) < 3000 
                                else "%s... more on github" 
                                    % result.content[0:2999], 
                              errors='ignore')
            raw.append(html_escape(pre_str))
            raw.append(u'</pre>')
            raw.append("</td></tr>")
        raw.append("</table>")
        raw.append("<hr />")
            
    return ''.join(raw)

@memoize("feed: %s", time=500)
def get_feed(username):
    """
    Uses the github gist API and constructs an RSS feed for it
    """
    
    url = "http://gist.github.com/api/v1/json/gists/%s" % username
    result = urlfetch.fetch(url)
    if result.status_code == 200 :
        feed = []
        feed.append("<rss version='2.0'>")
        feed.append("<channel>")
        feed.append("<title>%s's Gists</title>" 
                    % username)
        feed.append("<link>http://gist.github.com/%s</link>" 
                    % username)
        feed.append("""
                    <description>A pretty RSS list of %s 's Github Gists</description>
                    """ % username)
        feed.append("<pubDate>%s</pubDate>" 
                    % strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()))

        obj = jsonpickle.decode(result.content)
        for i in range(0, len(obj['gists']) if len(obj['gists']) < 10 else 10):
            gist = obj['gists'][i]
            date = parse(gist['created_at'])
            feed.append("<item>")
            feed.append("<author>%s</author>" % username)
            feed.append("<title>%s</title>" % 
                        gist['description'] 
                            if gist['description'] is not None 
                            else ', '.join(gist['files']))
            feed.append("""
                <description>
                    <div style="width: 100%%;">
                        <span style="float:right;"> posted: %s</span> 
                        <b>gist</b>: <a href="%s">%s</a>
                    </div>
                    <hr />
                    %s
                </description>
                """ % 
                    (date.strftime('%b %d, %Y'),
                     gist['repo'],
                     gist['repo'],
                     get_raw(gist['files'],gist['repo']),))
            feed.append("<link>http://gist.github.com/%s</link>" % gist['repo'])

            feed.append("<pubDate>%s</pubDate>"
                        % date.strftime("%a, %d %b %Y %H:%M:%S +0000"))
            feed.append("""
                <comments>http://gist.github.com/%s#comments</comments>
                """ % gist['repo'])
            feed.append("</item>")
        feed.append("</channel></rss>")
        return ''.join(feed)
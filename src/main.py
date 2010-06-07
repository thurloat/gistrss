"""
GistRSS - Generates a valid RSS/Atom feed for a github user's gist history.

@author: Adam Thurlow <thurloat>
@contact: thurloat <at> gmail <dot> com
"""

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import gisthub

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Usage: gistrss.appspot.com/feed/GITUSERNAME')

class MakeFeed(webapp.RequestHandler):
    def get(self, *args):
        self.response.headers.add_header('Content-Type','application/xml')
        self.response.out.write(gisthub.get_feed(args[0]))
        
URLS = [
        ('/', MainPage),
        ('/feed/(.*)/?', MakeFeed),
        ]
application = webapp.WSGIApplication(URLS, debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

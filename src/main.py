"""
main.py - Request delegation

GistRSS - Generates a valid RSS/Atom feed for a github user's gist history.

@author: Adam Thurlow <thurloat>
@contact: thurloat <at> gmail <dot> com
"""
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
import gisthub
import os

class HomeHandler(webapp.RequestHandler):
    """Request handler for home page with form to sign up for feed"""
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
        self.response.out.write(template.render(path, {}))

class FeedHandler(webapp.RequestHandler):
    """Request handler to generate the RSS feed"""
    def get(self, *args):
        try:
            feed = gisthub.get_feed(args[0])
        except Exception:
            self.response.headers.add_header('Content-Type', 'text/html')
            self.response.out.write("<h1>GitHub API is slow...</h1>")
        if feed is not 'error':
            self.response.headers.add_header('Content-Type', 'application/xml')
            self.response.out.write(gisthub.get_feed(args[0]))
        else:
            self.response.headers.add_header('Content-Type', 'text/html')
            self.response.out.write("<h1>Errorz. Bad Username?</h1>")

class Redir(webapp.RequestHandler):
    """Form does a post to here with the github username.
    Redirect to the feed"""
    def post(self):
        self.redirect("/feed/%s" % self.request.get('bleep_bloop'))

URLS = [
        ('/', HomeHandler),
        ('/feed/(.*)/?', FeedHandler),
        ('/redir', Redir),
        ]
APPLICATION = webapp.WSGIApplication(URLS, debug=True)

def main():
    """entrypt"""
    run_wsgi_app(APPLICATION)

if __name__ == "__main__":
    main()

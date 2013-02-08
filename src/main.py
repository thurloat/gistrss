"""
main.py - Request delegation

GistRSS - Generates a valid RSS/Atom feed for a github user's gist history.

@author: Adam Thurlow <thurloat>
@contact: thurloat <at> gmail <dot> com
"""

import os
import gisthub
from webapp2 import WSGIApplication, RequestHandler, cached_property
from webapp2_extras import jinja2

jinja2.default_config['template_path'] = os.path.join(os.path.dirname(__file__), "templates")

class HomeHandler(RequestHandler):
    """
    Request handler for home page with form to sign up for feed
    """

    @cached_property
    def jinja2(self):
        return jinja2.get_jinja2(app=self.app)

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        rv = self.jinja2.render_template('index.html')
        self.response.write(rv)

    def head(self):
        return

class FeedHandler(RequestHandler):
    """
    Request handler to generate the RSS feed
    """
    def get(self, *args):
        try:
            feed = gisthub.get_feed(args[0])
        except Exception:
            self.response.headers.add_header('Content-Type', 'text/html')
            self.response.out.write("<h1>GitHub API is slow...</h1>")
            return
        if feed is not 'error':
            self.response.headers.add_header('Content-Type', 'application/xml')
            self.response.out.write(gisthub.get_feed(args[0]))
        else:
            self.response.headers.add_header('Content-Type', 'text/html')
            self.response.out.write("<h1>Error. Bad Username?</h1>")

class Redir(RequestHandler):
    """Form does a post to here with the github username.
    Redirect to the feed"""
    def post(self):
        self.redirect("/feed/%s" % self.request.get('bleep_bloop'))

app = WSGIApplication([
    ('/', HomeHandler),
    ('/feed/(.*)/?', FeedHandler),
    ('/redir', Redir),
], debug=True)

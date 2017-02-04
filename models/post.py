from google.appengine.ext import db
from helpers import *

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.IntegerProperty(required=True)
    likes = db.IntegerProperty(required=False)
    unlikes = db.IntegerProperty(required=False)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        self._idIneed = self.key().id_or_name()
        return render_str("post.html", p=self)


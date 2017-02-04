from google.appengine.ext import db
from helpers import *
from models.post import Post

class Comment(db.Model):
    post = db.ReferenceProperty(Post, collection_name='comments')

    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.IntegerProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def by_id(cls, cid):
        key = db.Key.from_path('Comment', long(cid))
        c = db.get(key)
        return c

    @classmethod
    def exists(cls, cid):
        c = cls.by_id(cid)
        if c:
            return c
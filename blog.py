import webapp2
from google.appengine.ext import db
import time
from helpers import *


# Models
from models.user import User
from models.post import Post
from models.comment import Comment


# Handlers
from handlers.blog import BlogHandler
from handlers.blogfront import BlogFront
from handlers.likeorunlikepost import LikePost, UnlikePost
from handlers.posting import NewPost, EditPost, DeletePost
from handlers.commenting import NewComment, EditComment, DeleteComment
from handlers.signup import Signup, Register
from handlers.logonoff import Login, Logout

#Routing
app = webapp2.WSGIApplication([('/', BlogFront),
                               ('/blog/?', BlogFront),
                               ('/info?', BlogFront),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/blog/newpost', NewPost),
                               ('/blog/deletepost/([0-9]+)', DeletePost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/likepost/([0-9]+)',
                                LikePost),
                               ('/blog/unlikepost/([0-9]+)',
                                UnlikePost),
                               (r'/blog/newcomment/([0-9]+)/([0-9]+)',
                                NewComment),
                               ('/blog/editcomment/([0-9]+)',
                                EditComment),
                               ('/blog/deletecomment/([0-9]+)',
                                DeleteComment),
                               ],
                              debug=True)

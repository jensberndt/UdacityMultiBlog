from google.appengine.ext import db
from handlers.blog import BlogHandler
import time
from helpers import *


class LikePost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            # make sure that (un)liker is not same as author
            if not self.user_owns_post(post):
                newlikes = post.likes
                post.likes = newlikes + 1
                post.put()
                time.sleep(.300)
                self.redirect('/blog')
            else:
                error = "You are not allowed to like/unlike your  \
                         own posts!"
                self.render("info.html", subject=post.subject, error=error)
        else:
            self.redirect("/login")


class UnlikePost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            # make sure that (un)liker is not same as author
            if not self.user_owns_post(post):
                newunlikes = post.unlikes
                post.unlikes = newunlikes + 1
                post.put()
                time.sleep(.300)
                self.redirect('/blog')
            else:
                error = "You are not allowed to like/unlike your  \
                         own posts!"
                self.render("info.html", subject=post.subject, error=error)
        else:
            self.redirect("/login")

from google.appengine.ext import db
from handlers.blog import BlogHandler
import time
from helpers import *
from models.like import Like


class LikePost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            # make sure that liker is not same as author
            if not self.user_owns_post(post):
                user_id = self.user.key().id()
                post_id = post.key().id()
                key = db.Key.from_path('Post', int(post_id), parent=blog_key())

                like = Like.all().filter('user_id =', user_id).filter('post_id =', post_id).get()

                if not like:
                    like = Like(parent=key,
                                user_id=self.user.key().id(),
                                post_id=post.key().id())

                    post.likes += 1
                    like.put()
                    post.put()
                    time.sleep(.200)

                self.redirect('/blog')
            else:
                error = "You are not allowed to like your  \
                         own posts!"
                self.render("info.html", subject=post.subject, error=error)
        else:
            self.redirect("/login")


class UnlikePost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            # make sure that unliker is not same as author
            if not self.user_owns_post(post):
                user_id = self.user.key().id()
                post_id = post.key().id()
                key = db.Key.from_path('Post', int(post_id), parent=blog_key())

                like = Like.all().filter('user_id =', user_id).filter('post_id =', post_id).get()

                if not like:
                    like = Like(parent=key,
                                user_id=self.user.key().id(),
                                post_id=post.key().id())

                    post.unlikes += 1
                    like.put()
                    post.put()
                    time.sleep(.200)

                self.redirect('/blog')
            else:
                error = "You are not allowed to unlike your  \
                         own posts!"
                self.render("info.html", subject=post.subject, error=error)
        else:
            self.redirect("/login")

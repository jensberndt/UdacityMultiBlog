from google.appengine.ext import db
from handlers.blog import BlogHandler
import time
from helpers import *
from models.post import Post


class NewPost(BlogHandler):
    def get(self, post_id=None):
        if self.user:
            # display form for new blog entry
            self.render("postform.html", action='new')

        else:
            self.redirect("/login")

    def post(self, post_id=None):
        if self.user:
            # save new post if all data provided or show error
            subject = self.request.get('subject')
            content = self.request.get('content')
            author = int(self.read_secure_cookie('user_id'))

            if subject and content:
                p = Post(parent=blog_key(), subject=subject,
                         content=content, author=author,
                         likes=0, unlikes=0)
                p.put()
                time.sleep(.300)
                self.redirect('/blog')
            else:
                error = "subject and content, please!"
                self.render("postform.html", subject=subject,
                            content=content, error=error,
                            action=str(action))
        else:
            self.redirect("/login")


class EditPost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            if not self.user_owns_post(post):
                error = "You are not allowed to edit/delete this post, \
                         cause you are not the author of this post!"
                self.render("info.html",
                            subject=post.subject, error=error)
            else:
                self.render("postform.html",
                            subject=post.subject, content=post.content,
                            action='edit')
        else:
            self.redirect("/login")

    @check_if_valid_post
    def post(self, post_id, post):
        if self.user:
            if not self.user_owns_post(post):
                error = "You are not allowed to edit/delete this post, \
                         cause you are not the author of this post!"
                self.render("info.html",
                            subject=post.subject, error=error)
            else:
                subject = self.request.get('subject')
                content = self.request.get('content')

                if subject and content:
                    post.subject = subject
                    post.content = content
                    post.put()
                    time.sleep(.300)
                    self.redirect('/blog')
                else:
                    error = "subject and content, please!"
                    self.render("postform.html", subject=subject,
                                content=content, error=error,
                                action='edit')
        else:
            self.redirect("/login")


class DeletePost(BlogHandler):
    @check_if_valid_post
    def get(self, post_id, post):
        if self.user:
            if not self.user_owns_post(post):
                error = "You are not allowed to edit/delete this post, \
                         cause you are not the author of this post!"
                self.render("info.html", subject=post.subject, error=error)
            else:
                db.delete(db.Key.from_path('Post', long(post_id),
                          parent=blog_key()))
                time.sleep(.300)
                self.redirect('/blog')
        else:
            self.redirect("/login")

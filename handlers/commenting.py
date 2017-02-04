from google.appengine.ext import db
from handlers.blog import BlogHandler
import time
from helpers import *

from models.post import Post
from models.comment import Comment


class NewComment(BlogHandler):
    def get(self, post_id=None, comment_id=None):
        if self.user:
            # show form for new comment
            key = db.Key.from_path('Post', long(post_id),
                                   parent=blog_key())
            post = db.get(key)
            self.render("commentform.html", postsubject=post.subject,
                        postcontent=post.content, action='new')
        else:
            self.redirect("/login")

    def post(self, post_id=None, comment_id=None):
        if self.user:
            # save the new comment and show it on blogpost
            c = self.request.get('comment')
            a = int(self.read_secure_cookie('user_id'))

            if c and c != '':
                key = db.Key.from_path('Post', long(post_id),
                                       parent=blog_key())
                post = db.get(key)
                Comment(post=post,
                        comment=c,
                        author=a).put()
                time.sleep(.300)
                self.redirect('/blog')
            else:
                error = "Please make this comment useful and fill in \
                some words!"
                self.render("postform.html", subject=subject,
                            content=content, error=error,
                            action='new')
        else:
            self.redirect('/login')


# Edit a comment
class EditComment(BlogHandler):
    def get(self, comment_id):
        if self.user:
            c = Comment.exists(comment_id)
            if c:
                if not self.user_owns_comment(c):
                    error = "You are not allowed to edit this comment, \
                    cause you are not the author of this comment!"
                    self.render("info.html", subject=c.comment,
                                error=error)
                else:
                    self.render("commentform.html",
                                postsubject="",     # later improvement .post.subject,
                                postcontent="",     # later improvement .post.content,
                                comment=c.comment,
                                action='edit')
            else:
                self.redirect("/")
        else:
            self.redirect("/login")

    def post(self, comment_id):
        if self.user:
            c = Comment.exists(comment_id)
            if c:
                if not self.user_owns_comment(c):
                    error = "You are not allowed to edit this comment, \
                             cause you are not the author of this comment!"
                    self.render("info.html", subject=c.comment,
                                error=error)
                else:
                    comment = self.request.get('comment')
                    if comment:
                        c.comment = comment
                        c.put()
                        time.sleep(.300)
                        self.redirect('/blog')
                    else:
                        error = "Please make this comment useful and fill in \
                        some words!"
                        self.render("commentform.html", subject="",  # later improvement subjec
                                    content="", comment=comment,     # and content of post
                                    action='edit')
            else:
                self.redirect('/')
        else:
            self.redirect('/login')


# Delete a comment
class DeleteComment(BlogHandler):
    def get(self, comment_id):
        if self.user:
            c = Comment.exists(comment_id)
            if c:
                if not self.user_owns_comment(c):
                    error = "You are not allowed to delete this comment, \
                             cause you are not the author of this comment!"
                    self.render("info.html", subject=c.comment, error=error)
                else:
                    key = db.Key.from_path('Comment', long(comment_id))
                    db.get(key).delete()
                    time.sleep(.300)
                    self.redirect('/blog')
            else:
                self.redirect('/')
        else:
            self.redirect("/login")

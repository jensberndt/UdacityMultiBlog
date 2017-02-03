import os
import re
import random
import hashlib
import hmac
from string import letters
import webapp2
import jinja2
from google.appengine.ext import db
import time
from functools import wraps
import logging

######
# General stuff
######
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

secret = 'justasecret'


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


# regex for validation functions
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')


# validator functions
def valid_username(username):
    return username and USER_RE.match(username)


def valid_password(password):
    return password and PASS_RE.match(password)


def valid_email(email):
    return not email or EMAIL_RE.match(email)


def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def users_key(group='default'):
    return db.Key.from_path('users', group)


def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)


######
# User Class
######
class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent=users_key(),
                    name=name,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


def blog_key(name='default'):
    return db.Key.from_path('blogs', name)


def check_if_valid_post(function):
    @wraps(function)
    def wrapper(self, post_id):
        logging.warning("insife check if valid" + str(post_id))
        key = db.Key.from_path('Post', long(post_id), parent=blog_key())
        post = db.get(key)
        if post:
            return function(self, post_id, post)
        else:
            logging.warning("bei 404 ausgestiegen" + str(post_id))

            self.error(404)
            return
    return wrapper


def check_if_valid_comment(f):
    @wraps(f)
    def wrapped(self, comment_id):
        logging.warning("insife check if valid comment" + str(comment_id))
        key = db.Key.from_path('Comment', long(comment_id))
        comment = db.get(key)
        if comment:
            return f(self,comment_id, comment)
        else:
            logging.warning("bei 404 ausgestiegen" + str(comment_id))

            self.error(404)
            return
    return wrapped


######
# Post Class
######
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


######
# Comment Class
######
class Comment(db.Model):
    post = db.ReferenceProperty(Post, collection_name='comments')

    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    author = db.IntegerProperty(required=True)
    last_modified = db.DateTimeProperty(auto_now=True)


######
# Main Blog Handler
######
class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def user_owns_post(self, post):
        logging.warning("user_owns_post" + str(post.author) +" - "+ str(self.read_secure_cookie('user_id')))
        return long(self.read_secure_cookie('user_id')) == long(post.author)

    def user_owns_comment(self, comment):
        logging.warning("user_owns_pcomment" + str(comment.author) +" - "+ str(self.read_secure_cookie('user_id')))
        return long(self.read_secure_cookie('user_id')) == long(comment.author)

######
# Request-Handlers
######


# Blog / /blog/?
class BlogFront(BlogHandler):
    def get(self):
        posts = greetings = Post.all().order('-created')
        self.render('front.html', posts=posts)


# like / unlike existing Blogpost /blog/likeornotpost/([0-9]+)
class LikeUnlikePost(BlogHandler):
    def get(self, action=None, post_id=None):

        if self.user:
            if post_id:
                key = db.Key.from_path('Post', long(post_id),
                                       parent=blog_key())
                post = db.get(key)

                # make sure that (un)liker is not same as author
                if str(post.author) != self.read_secure_cookie('user_id'):
                    if str(action) == 'like':
                        newlikes = post.likes
                        post.likes = newlikes + 1

                    elif str(action) == 'unlike':
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


# Create Blogpost '/blog/newpost'
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


# Edit Blogpost /blog/adminpost/(.*)/([0-9]+)
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


# delete existing Blogpost /blog/deletepost/([0-9]+)
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


# create comment on post '/blog/newcomment/(.*)/([0-9]+)
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
            self.redirect('/')




# create, edit or delete comment on post '/blog/comment/(.*)/([0-9]+)
@check_if_valid_comment
class EditComment(BlogHandler):
    def get(self, comment_id, comment):
        if self.user:
            if not user_owns_comment(comment):
                error = "You are not allowed to edit this comment, \
                cause you are not the author of this comment!"
                self.render("info.html", subject=comment.comment,
                            error=error)
            else:
                self.render("commentform.html",
                            postsubject=post.subject,
                            postcontent=post.content,
                            comment=comment.comment,
                            action='edit')
        else:
            self.redirect("/login")


    def post(self, post_id=None, comment_id=None):
        if self.user:
            key = db.Key.from_path('Comment', long(comment_id))
            c = db.get(key)
            comment = self.request.get('comment')
            if str(c.author) == self.read_secure_cookie('user_id'):
                if comment:
                    c.comment = comment
                    c.put()
                    time.sleep(.300)
                    self.redirect('/blog')
                else:
                    error = "Please make this comment useful and fill in \
                    some words!"
                    self.render("commentform.html", subject=post.subject,
                                content=post.content, comment=comment,
                                action='edit')
            else:
                error = "You are not allowed to edit this comment, \
                cause you are not the author of this comment!"
                self.render("info.html", subject=c.comment,
                            error=error)
        else:
            self.redirect('/')


# Delete an comment
class DeleteComment(BlogHandler):
    def get(self, comment_id=None):

        if self.user:
            key = db.Key.from_path('Comment', long(comment_id))
            c = db.get(key)

            if str(c.author) == self.read_secure_cookie('user_id'):
                db.get(key).delete()
                time.sleep(.300)

                self.redirect('/blog')
            else:
                error = "You are not allowed to delete this comment, \
                cause you are not the author of this comment!"
                self.render("info.html", subject=c.comment, error=error)
        else:
            self.redirect("/login")


# new user signup /signup
class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username,
                      email=self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(Signup):
    def done(self):
        # make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login(u)
            self.redirect('/blog')


# User logs in /login
class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error=msg)


# User logs out /logout
class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/')


######
# Routes
######
app = webapp2.WSGIApplication([('/', BlogFront),
                               ('/blog/?', BlogFront),
                               ('/info?', BlogFront),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/blog/newpost', NewPost),
                         #      (r'/blog/adminpost/(.*)/([0-9]+)',
                          #      AdministratePost),
                               ('/blog/deletepost/([0-9]+)', DeletePost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               (r'/blog/likeornotpost/(.*)/([0-9]+)',
                                LikeUnlikePost),
                          #     (r'/blog/comment/(.*)/([0-9]+)/([0-9]+)',
                          #      AdministrateComment),
                               (r'/blog/newcomment/([0-9]+)/([0-9]+)',
                                NewComment),
                               ('/blog/editcomment/([0-9]+)',
                                EditComment),
                               (r'/blog/deletecomment/([0-9]+)',
                                DeleteComment),
                               ],
                              debug=True)

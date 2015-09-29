#!/usr/bin/env python

import webapp2
import os
import jinja2
import re
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import mail


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class Photo(db.Model):
    comments = db.StringProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
    avatar = db.BlobProperty()
    stream_name = db.StringProperty()
    date_accessed = db.DateTimeProperty(auto_now=True)
    tag  = db.StringProperty()
    total_pics = db.IntegerProperty()
    owner = db.EmailProperty()
    root = db.BooleanProperty()
    views = db.IntegerProperty()

class Subscribers(db.Model):
    subscriber = db.EmailProperty()
    stream_name = db.StringProperty()


class MainHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/index.html')
            self.response.write(template.render())
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Manage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        #current_stream = self.request.get('current_stream')

        if user:
            streams1 = Photo.all()
            total_pics_root = Photo.all()

            #to try and make number of pics accurate
            total_pics_root.filter("root", True).filter("owner", user.email())
            #for each_root in total_pics_root:
            #    total_pics = Photo.all()
            #    total_pics.filter("root", False).filter("stream_name", each_root.stream_name)
            #    each_root.total_pics = total_pics.count()
            #    each_root.put()

            streams1.filter("root", True).filter("owner", user.email())

            sub_streams_data = Subscribers.all()
            sub_streams_data.filter("subscriber", user.email()).order("stream_name")

            streams_new = []
            if sub_streams_data.count() != 0:
                for s in sub_streams_data:

                    sub_streams = Photo.all()
                    sub_streams.filter("stream_name", s.stream_name).filter("root", True)
                    streams_new.append(sub_streams.get())
            else:
                streams_new = None


            template_data = {"streams": streams1,
                             "sub_streams": streams_new}
            template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
            self.response.write(template.render(template_data))
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Create(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/create.html')
            self.response.write(template.render())
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class View(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        current_stream = self.request.get("current_stream")

        streams = Photo.all()
        streams.filter("stream_name", current_stream).filter("root", True)

        if streams.count() > 0: #if stream was clicked to view from Manage Page
            print "found matching stream name"
            stream_obj = streams.get()
            key = stream_obj.key()
        else:  # If View tab was clicked then find most recently accessed stream
            print "View tab was clicked"
            streams2 = Photo.all()
            streams2.order("-date_accessed").filter("owner", user.email())
            stream_obj = streams2.get()


        #stream_obj has root entity to find if stream is empty
        if stream_obj != None: #if user clicked on view tab
            photos_in_stream = Photo.all()
            photos_in_stream.filter("root", False).filter("stream_name", stream_obj.stream_name)
            photos_in_stream.order("-date_accessed")

        else:
            photos_in_stream = None

        #incrementing stream views
        stream_obj.views += 1
        stream_obj.put()

        template_data = {"current_stream": current_stream,
                         "photos_in_stream": photos_in_stream}
        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/view.html')
            self.response.write(template.render(template_data))
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class ViewAll(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        all_streams = Photo.all()
        all_streams.filter("root", True).filter("owner", user.email())
        most_recent = []
        for streams in all_streams:
            latest_photo = Photo.all()
            latest_photo.filter("stream_name", streams.stream_name).filter("root", False).order("-date_accessed")
            latest_photo_obj = latest_photo.get()
            if latest_photo_obj != None:
                most_recent.append(latest_photo_obj)

        template_data = {"photos_in_stream": most_recent}
        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/viewAll.html')
            self.response.write(template.render(template_data))
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Search(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        search_word = self.request.get("search_word")

        if user:
            find_root = Photo.all()
            find_root.filter("root", True)
            matched_searches = []
            tags = []
            for stream in find_root:
                #print stream.tag
                ###p = re.compile('%s'%search_word)
                ###sub_string = p.findall(stream.tag)
                ###if sub_string != None:
                ###    print "found a match"
                ###    print stream.stream_name
                ###    matched_searches.append(stream.stream_name)
                ###else:
                ###    print "did not find a match"
                if search_word in stream.tag:
                    matched_searches.append(stream)
            if search_word != '':
                for stream in matched_searches:
                    tag_list = Photo.all()
                    tag_list.filter("stream_name", stream.stream_name).filter("root", False).order("-date_accessed")
                    for tag in tag_list:
                        tags.append(tag)

            num_results = len(tags)
            print "results: %d" % num_results
            template_data = {"tags": tags,
                             "num_results": num_results,
                             "search_word": search_word}
            template = JINJA_ENVIRONMENT.get_template('templates/search.html')
            self.response.write(template.render(template_data))
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Trending(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/trending.html')
            self.response.write(template.render())
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Social(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            template = JINJA_ENVIRONMENT.get_template('templates/manage.html')
            self.response.write(template.render())
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class AddStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        stream_name = self.request.get("stream_name")
        stream_tags = self.request.get("tags")
        #TODO: add subscribers and cover img
        subscribers = self.request.get("subscribers")
        cover_image_url = self.request.get("cover_image_url")
        optional_message = self.request.get("optional_message")
        if user:
            streams = Photo.all()
            sub_streams = Subscribers.all()
            streams.filter("stream_name", stream_name)

            if streams.count() > 0:
                error_string = "you tried to create a new stream whose name is the same as an existing stream, operation did not complete."
                self.redirect('/error?error_message=' + error_string)
                #self.redirect('/error')
            else:
                print "new stream: %s" % stream_name
                new_stream = Photo(key_name=stream_name,
                                   stream_name = stream_name,
                                   root = True,
                                   tag = stream_tags,
                                   total_pics = 0,
                                   views = 0,
                                   owner = user.email()
                                   )
                new_stream.put()

                subscriber_list = unicode.split(subscribers)
                for subscriber in subscriber_list:
                    p = re.compile('\w+@\w+\.\w+')
                    s = p.search(subscriber)
                    if s != None:
                        print "printing s %s" % s
                        new_subscribers = Subscribers(stream_name = stream_name,
                                                      subscriber=s.group(0)
                                                      )
                        new_subscribers.put()
                        #TODO test if email is sent
                        sender = user.email()
                        to = s.group(0)
                        subject = "Please Subscribe to " + user.nickname() + "'s Stream: " + stream_name
                        body = optional_message
                        mail.send_mail(sender, to, subject, body)

                self.redirect('/manage')
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class DeleteStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        stream_name = self.request.get_all("stream")

        if user:
            if stream_name:
                print "Found stream. Deleting...."
                for p in stream_name:
                    print p
                    streams = Photo.all()
                    streams.filter("stream_name", p)
                    for photo in streams:
                        key = photo.key()
                        db.delete(key)
                self.redirect('/manage')

                    #TODO: checker user before deleting
            else:
                print "did not find stream"
                self.redirect('/manage')
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Upload(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        New_Image = self.request.get("img")
        current_stream = self.request.get("current_stream")
        streams = Photo.all()
        streams.filter("root", True).filter("stream_name", current_stream)

        if user:
            if streams.count() == 0: #if current_stream is empty
                streams2 = Photo.all()
                streams2.order("-date_accessed")
                stream_obj = streams2.get()
                streams2.filter("root", True).filter("stream_name", stream_obj.stream_name)
                stream_obj = streams2.get()
            else:
                stream_obj = streams.get()

            if New_Image == '':
                error_string = "No image provided!"
                self.redirect('/error?error_message=' + error_string)
            else:
                comments = self.request.get("comments")
                avatar = images.resize(New_Image, 500, 300)
                new_photo = Photo(parent=db.Key.from_path('Photo', user.email() ),
                                  stream_name = stream_obj.stream_name,
                                  comments = comments,
                                  avatar = db.Blob(avatar),
                                  root = False
                                  )
                if stream_obj.owner == user.email():
                    new_photo.put()
                else:
                    error_string = "You are attempting to modify another user's stream!"
                    self.redirect('/error?error_message=' + error_string)
                streams3 = Photo.all()
                streams3.filter("root", False).filter("stream_name", stream_obj.stream_name)
                stream_obj.total_pics = streams3.count()
                stream_obj.put()
                self.redirect('/view?current_stream=' + stream_obj.stream_name)
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)

class DisplayPhoto(webapp2.RequestHandler):
    def get(self):
        photo = self.request.get('png')

        photo_obj = db.get(photo)
        if photo_obj.avatar:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(photo_obj.avatar)


class Logout(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            #self.response.out.write('<html><body><a href=users.create_logout_url(/)></a></body></html>')
            #users.create_logout_url('/manage')
            self.response.out.write("""Hello, %s. <a href='%s'>Logout</a>""" % (user.nickname(), users.create_logout_url("/")))

            #greeting = ('<a href="%s">Sign in or register</a>.' %
            #            users.create_login_url('/'))
            #self.response.out.write('<html><body>%s</body></html>' % greeting)
        else:
            print "did not find user"
            self.redirect('/')


class SubStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        stream_name = self.request.get("current_stream")

        if user:
            if stream_name:
                #checking if user is subscribing to their own stream
                streams2 = Photo.all()
                streams2.filter("stream_name", stream_name).filter("root", True)
                stream_obj2 = streams2.get()
                if stream_obj2.owner == user.email():
                    error_string = "Cannot subscribe to your own stream!"
                    self.redirect('/error?error_message=' + error_string)

                streams = Subscribers.all()
                streams.filter("stream_name", stream_name)
                stream_obj = streams.get()
                if streams.count() == 0: #new subscription


                    new_subscribers = Subscribers(stream_name = stream_name,
                                                  subscriber = user.email()
                                                  )
                    new_subscribers.put()
                    self.redirect('/view?current_stream=' + stream_name)
                else: #previously subscribed
                    error_string = "Previously subscribed to this stream!"
                    self.redirect('/error?error_message=' + error_string)
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class UnsubStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        stream_name = self.request.get_all("stream")

        if user:
            if stream_name:
                for p in stream_name:
                    streams = Subscribers.all()
                    streams.filter("stream_name", p)
                    for photo in streams:
                        key = photo.key()
                        db.delete(key)
                    #TODO: check user before deleting
                self.redirect('/manage')

            else:
                self.redirect('/manage')

        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))
            self.response.out.write('<html><body>%s</body></html>' % greeting)


class Error(webapp2.RequestHandler):
  def get(self):
    user = users.get_current_user()
    error_message = self.request.get("error_message")
    print "received error message %s" % error_message
    if user:
        template_data = {"error_message": error_message}
        template = JINJA_ENVIRONMENT.get_template('templates/error.html')
        self.response.write(template.render(template_data))
    else:
        greeting = ('<a href="%s">Sign in or register</a>.' %
                    users.create_login_url('/'))
        self.response.out.write('<html><body>%s</body></html>' % greeting)


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/manage', Manage),
    ('/create', Create),
    ('/view', View),
    ('/viewall', ViewAll),
    ('/search', Search),
    ('/trend', Trending),
    ('/social', Social),
    ('/add_stream', AddStream),
    ('/delete_stream', DeleteStream),
    ('/subscribe', SubStream),
    ('/unsub_stream', UnsubStream),
    ('/upload', Upload),
    ('/display', DisplayPhoto),
    ('/error', Error),
    ('/logout', Logout)
], debug=True)

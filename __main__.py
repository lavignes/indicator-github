#!/usr/bin/env python

from github import Github
#import gtk as Gtk
from gi.repository import Gtk, GObject, Notify
from gi.repository import AppIndicator3 as AppIndicator
import os
#import pynotify
import exceptions
import webbrowser
import urllib
import datetime

client_id = '17d74debb1b3ef6337e6'
request_string = 'https://github.com/login/oauth/authorize?client_id=%s&scope=%s'
scope = 'repo:status,notifications'
token = ''
app_folder = os.path.expanduser(os.path.join('~','.indicator-github',''))
feed_time = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
icon = os.path.join(os.path.dirname(os.path.realpath(__file__)),'gh.png')
print icon
old_events = []

events = {
  'CommitCommentEvent': 'commented on',
  'CreateEvent': 'created',
  'FollowEvent': 'started following',
  'ForkEvent': 'forked',
  'PublicEvent': 'open sourced',
  'PullRequestEvent': 'pull request',
  'WatchEvent': 'starred'
  }

def initialize(gh):
  read_events(gh)
  # Check for updates every 2 minutes
  GObject.timeout_add_seconds(2*60, read_events, gh)
  return False

def about(menu_item):
  dialog = Gtk.AboutDialog()
  dialog.set_program_name('Indicator GitHub')
  dialog.set_version('alpha')
  dialog.set_comments('An indicator applet for GitHub')
  dialog.set_authors(['Scott LaVigne'])
  with open('LICENSE.txt','r') as f:
    dialog.set_license(f.read())
  dialog.show_all()
  dialog.run()
  dialog.destroy()

def credential_prompt():
  dialog = Gtk.MessageDialog(
    parent=None,
    flags=0,
    type=Gtk.MESSAGE_QUESTION,
    buttons=Gtk.BUTTONS_OK_CANCEL,
    message_format='Please enter your GitHub credentials.')

  dialog.set_title('GitHub Login')
  box = dialog.get_content_area()
  password = Gtk.Entry()
  password.set_visibility(False)
  username = Gtk.Entry()
  box.add(username)
  box.add(password)
  dialog.show_all()
  dialog.run()
  auth = (username.get_text(), password.get_text())
  dialog.destroy()
  return auth

def read_events(gh):
  print('Fetching events from GitHub')
  global feed_time
  for event in gh.get_user(gh.get_user().login).get_received_events():
    if event.created_at > feed_time:
      # A repository could be deleted or something
      try:
        if event.type == 'PullRequestEvent':
          message = "%s %s %s#%i" % (
            event.payload['action'],
            events[event.type],
            event.repo.full_name,
            event.payload['number']
            )
        else:
          message = "%s %s" % (events[event.type], event.repo.full_name)
        Notify.Notification.new(event.actor.login, message, icon).show()
      except: pass
    else:
      # If I reached an event that isn't new, then I know
      # there are no new event past it
      break

  feed_time = datetime.datetime.utcnow()
  return True

if not os.path.exists(app_folder): os.makedirs(app_folder)

# Check if user has authenticated app
if not os.path.isfile(os.path.join(app_folder,'oauth')):
  # Authorize indicator-github
  webbrowser.open(request_string % (urllib.quote(client_id), urllib.quote(scope)))
  # Get oauth token
  gh = Github(*credential_prompt(), client_id=client_id, user_agent=client_id)
  for auth in gh.get_user().get_authorizations():
    if auth.app.name == 'indicator-github':
      token = auth.token
      break
  else:
    raise KeyError
  # Save token to file
  token_file = open(os.path.join(app_folder,'oauth'), 'w+')
  token_file.write(token)
  token_file.close()

# Auth token already exists
else:
  token_file = open(os.path.join(app_folder,'oauth'), 'r')
  token = token_file.read()

gh = Github(login_or_token=token, client_id=client_id, user_agent=client_id)

indicator = AppIndicator.Indicator.new(
  'indicator-github',
  icon,
  AppIndicator.IndicatorCategory.COMMUNICATIONS
  )
indicator.set_label('GitHub','test')
indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()
menu_item = Gtk.MenuItem(gh.get_user().name)
menu.append(menu_item)

menu.append(Gtk.SeparatorMenuItem())

repo_item = Gtk.MenuItem("Your Repositories")
repo_menu = Gtk.Menu()
repo_item.set_submenu(repo_menu)
for repo in gh.get_user().get_repos():
  menu_item = Gtk.MenuItem(repo.name)
  repo_menu.append(menu_item)
menu.append(repo_item)

menu.append(Gtk.SeparatorMenuItem())

menu_item = Gtk.MenuItem("About...")
menu_item.connect("activate", about)
menu.append(menu_item)
menu_item = Gtk.MenuItem("Quit")
menu_item.connect("activate", Gtk.main_quit)
menu.append(menu_item)
menu.show_all()
indicator.set_menu(menu)

# Initialize App in 1 second
GObject.timeout_add_seconds(1, initialize, gh)

Notify.init('indicator-github')
Notify.Notification.new('GitHub', 'Logged in', icon).show()
Gtk.main()

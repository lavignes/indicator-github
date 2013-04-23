#!/usr/bin/python

from github import Github
import webbrowser
import gtk
import appindicator

def login():
    dialog = gtk.MessageDialog(
                parent=None,
                flags=0,
                type=gtk.MESSAGE_QUESTION,
                buttons=gtk.BUTTONS_OK_CANCEL,
                message_format="Please enter your gitub credentials.")

    dialog.set_title("Github login")

    box = dialog.get_content_area()
    password = gtk.Entry()
    password.set_visibility(False)
    password.set_invisible_char("*")
    box.pack_end(password, False, False, 0)

    username = gtk.Entry()
    username.set_visibility(True)
    box.pack_end(username, False, False, 0)

    dialog.show_all()
    dialog.run()

    gh = Github(username.get_text(), password.get_text())
    dialog.destroy()
    return gh

def on_repo_clicked(menu_item, repo):
  webbrowser.open(repo.html_url)

def on_name_clicked(menu_item, user):
  webbrowser.open(user.html_url)

def create_menu(gh, ind):
    menu = gtk.Menu()

    menu_item = gtk.MenuItem(gh.get_user().name)
    menu_item.connect("activate", on_name_clicked, gh.get_user())
    menu.append(menu_item)

    menu.append(gtk.SeparatorMenuItem())
    
    for repo in gh.get_user().get_repos():
        menu_item = gtk.MenuItem(repo.name)
        menu_item.connect("activate", on_repo_clicked, repo)
        menu.append(menu_item)

    menu.show_all()
    ind.set_menu(menu)

if __name__ == "__main__":
    indicator = appindicator.Indicator ("indicator-brightness", \
        "/home/pyrated/src/indicator-github/gh.png",\
        appindicator.CATEGORY_COMMUNICATIONS)
    
    indicator.set_status(appindicator.STATUS_ACTIVE)
    gh = login()
    create_menu(gh, indicator)
    gtk.main()

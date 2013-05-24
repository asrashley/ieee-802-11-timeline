Unless you are a member of the IEEE 802.11 executive, this is not the git
repository you are looking for.

The application is based upon the model, view, controller paradigm. It uses
databases to hold information on the IEEE 802.11 projects, ballots and meeting
reports. Scripts are used to control the “business logic” of viewing and
modifying this data, and HTML templates that render the data that you see in
your web browser.

The main advantage of this approach is that it allows changes to the visual
appearance without requiring any change to the data or control logic.

The IEEE 802.11 timeline tool is a web application that is currently being
hosted by the Google App Engine. The URL for the site is <http://ieee80211timeline.appspot.com/>

To ensure that this application stays within the free usage quota, access to all
parts of the website, apart from the front page, requires a username and
password. Contact me if you would like to request access.

Details of how to use the application can be found on the [IEEE document server][doc]
  [doc]: https://mentor.ieee.org/802.11/dcn/10/11-10-1349-03-0000-ieee-802-11-timeline-ballot-tool.docx
  
Application Environment
-----------------------
The application is written in the [Python][python] programming language and is based upon
the [Django][django] web development framework. As the application is hosted on the Google
App Engine [GAE][GAE], a database abstraction layer is required because Django
requires the use of a relational database, but the GAE datastore is a
non-relational database. The timeline tool uses the [django-nonrel][nonrel] abstraction
layer to allow Django to use the GAE datastore.

  [python]: http://www.python.org/
  [GAE]: http://code.google.com/appengine/
  [django]: http://www.djangoproject.com/
  [nonrel]: http://www.allbuttonspressed.com/projects/django-nonrel

To run the timeline tool locally, you need to install Python, the GAE
development environment, download the timeline tool source code and then place the
django-nonrel source code in the same directory as the timeline tool source
code, as described below. At the time of writing, GAE requires the use of
Python v2.7.

Download the following:
* Google App Engine for Python <http://code.google.com/appengine/>
* django-nonrel: <https://github.com/django-nonrel/django>
* djangoappengine: <https://github.com/django-nonrel/djangoappengine>
* djangotoolbox: <https://github.com/django-nonrel/djangotoolbox>
* django-dbindexer: <https://github.com/django-nonrel/django-dbindexer>
* django-autoload: <https://bitbucket.org/twanschik/django-autoload>

Make sure you select the 1.4 branch for all of the django repositories. The
following commands should do the job:

    git clone https://github.com/django-nonrel/django -b nonrel-1.4
    git clone https://github.com/django-nonrel/djangoappengine -b appengine-1.4
    git clone https://github.com/django-nonrel/djangotoolbox -b toolbox-1.4
    git clone https://github.com/django-nonrel/django-dbindexer -b dbindexer-1.4
    hg clone https://bitbucket.org/twanschik/django-autoload

Install the Google App Engine. Copy or symbolic link the following folders into the same 
directory where you have downloaded the source code:
* django-nonrel/django => <timeline_dir>/django
* djangotoolbox/djangotoolbox => <timeline_dir>/djangotoolbox
* django-dbindexer/dbindexer => <timeline_dir>/dbindexer
* djangoappengine => <timeline_dir>/djangoappengine
* django-autload/autoload => <timeline_dir>/autoload

Once finished, you should have a directory that contains:

    <SYMLINKD>     autoload [..\django-autoload\autoload]
    <DIR>          ballot
    <SYMLINKD>     dbindexer [..\django-dbindexer\dbindexer]
    <SYMLINKD>     django [..\django\django]
    <SYMLINKD>     djangoappengine [..\djangoappengine\djangoap
    <SYMLINKD>     djangotoolbox [..\djangotoolbox\djangotoolbo
    <DIR>          media
    <DIR>          project
    <DIR>          report
    <DIR>          templates
    <DIR>          timeline
    <DIR>          util
    .gitignore
    app.yaml
    cron.yaml
    index.yaml
    indexes.py
    LICENSE-2.0.txt
    manage.py
    queue.yaml
    README.md
    robots.txt
    runtests.bat
    runtests.sh
    settings.py
    test.bat
    urls.py
    __init__.py

To test that the code is working correctly, run the unit tests.

If using Windows, by typing the following in a command prompt window:

    runtests.bat

If you are running the software on a Unix platform, use:

    sh ./runtests.sh

This should produce “OK” after running all the tests.

Before you can use the development web server, you need to create the local
databases and create a super-user account.

    python manage.py syncdb
    python manage.py createsuperuser

The local development web server can be started using:

    python manage.py runserver

and then opening <http://localhost:8000/> in a web browser.

 

DestiNet
========

Zope 6 / Python 3 pip installation for destinet.eu, configured in
``site.cfg`` (pins in ``versions.cfg``). The shared Naaya configuration
(``base.cfg``, ``zope6-versions.cfg``, ``pip/``, migration scripts) comes from
the ``pip`` branch of https://github.com/eaudeweb/naaya.buildout.naaya,
checked out in ``src/naaya.buildout.naaya``.

Prerequisites
-------------

* Python 3.12 with the ``venv`` module
* git, and access to github.com/eaudeweb/naaya.buildout.naaya
* a C compiler (``build-essential`` on Debian), used to build haproxy

Installation
------------

1. Create ``secret.cfg`` next to ``site.cfg``::

    [secrets]
    GOOGLE_AUTH_CLIENT_ID =
    GOOGLE_AUTH_CLIENT_SECRET =
    GOOGLE_MAPS_API_KEY =
    GOOGLE_GEOLOCATION_API_KEY =
    SENTRY_DSN =

2. Clone ``src/naaya.buildout.naaya`` and ``src/NaayaBundles-DESTINET``
   (https://github.com/eaudeweb/naaya.bundles.NaayaBundles-DESTINET)::

    make bootstrap

   Without SSH access to GitHub::

    make bootstrap NAAYA_REPO=https://github.com/eaudeweb/naaya.buildout.naaya.git \
        BUNDLES_REPO=https://github.com/eaudeweb/naaya.bundles.NaayaBundles-DESTINET.git

3. Create ``.venv``, install the packages, write the instance files
   (``parts/``, ``bin/``) and build haproxy::

    make install

   After a change in ``site.cfg``, ``make config`` rewrites the instance files.

Data, logs and the ZEO socket are in ``var/`` (``var/filestorage/Data.fs``,
``var/blobstorage``, ``var/log``).

Running
-------

::

    bin/zeoserver start
    bin/zope-instance-0 start    # also -1, -2, -3, -async
    bin/haproxy -D -f haproxy.cfg

haproxy listens on 127.0.0.1:8080 and balances ``zope-instance-0`` to
``zope-instance-2``. ``init_destinet`` is the init script used in production.

Python 2 Data.fs migration
--------------------------

::

    make migrate

Defaults: ``INSTANCE=zope-instance-0``, ``DATAFS=var/filestorage/Data.fs``.

The last step rebuilds every catalog and packs the database. To rebuild the
catalogs again later (Data.fs opened directly, ``zeoserver`` stopped)::

    make reindex

Step 1 is skipped when ``var/filestorage/.zodbupdate-done`` exists; delete it
before migrating a new copy of the Python 2 Data.fs.

The migration needs ``pdftotext`` (``poppler-utils``) to index PDF files and
``catdoc`` for .doc/.xls/.ppt files; without them those files are not
indexed.

CentOS 7
--------

CentOS 7 has no Python 3.12 and an old gcc. Build Python and install as in the
"CentOS 7" section of the naaya.buildout.circabe README
(https://github.com/eaudeweb/naaya.buildout.circabe): vault.centos.org
repositories, ``openssl11-devel``, ``devtoolset-11``, Python 3.12 in
``/opt/python3.12``, then::

    sudo yum install -y poppler-utils catdoc
    scl enable devtoolset-11 -- make install PYTHON=/opt/python3.12/bin/python3.12

Test install next to production
-------------------------------

``local.cfg`` (read after ``site.cfg`` and ``secret.cfg``) moves a test
install off the production ports and keeps its errors out of Sentry::

    [instance:zope-instance-0]
    http-address = 127.0.0.1:17090
    # the same for -1, -2, -3 (17091-17093), -async (17095),
    # -translations-test (17098), -dev (17099)

    [haproxy]
    frontend-bind = 127.0.0.1:17080
    backends =
        backend Zopes
            balance roundrobin
            option httpchk GET /health_check
            server Zope1 127.0.0.1:17090 check
            server Zope2 127.0.0.1:17091 check
            server Zope3 127.0.0.1:17092 check

    [secrets]
    SENTRY_DSN =

Run ``make config`` after editing it. Images moved out of the content by the
migration are linked as ``/images/<id>``, relative to the domain root; through
an SSH tunnel open the site with a virtual host URL, e.g.
``http://localhost:17090/VirtualHostBase/http/localhost:17090/demo-design/VirtualHostRoot/``.

Production migration
--------------------

The Python 2 production runs from ``/var/local/destinet/buildout``, with its
data in ``/var/local/destinet/var``; the new install is
``/var/local/destinet/destinet.eu`` (``PREFIX`` in ``init_destinet``). A
trial migration on a copy took about 30 minutes (2.2 million objects). Run the
long steps in ``tmux``.

1. Stop the Python 2 production (instances, haproxy, ``zeoserver``), so the
   copy is consistent::

    sudo /etc/init.d/destinet stop

2. Copy the data into the new install::

    cd /var/local/destinet/destinet.eu
    bin/zeoserver stop; bin/zope-instance-0 stop    # if the test install runs
    rm -f var/filestorage/Data.fs* var/filestorage/.zodbupdate-done
    cp /var/local/destinet/var/filestorage/Data.fs var/filestorage/
    rsync -a --delete /var/local/destinet/var/blobstorage/ var/blobstorage/

3. Migrate::

    make migrate

4. Remove the test ports and the ``[secrets]`` override from ``local.cfg``
   (or delete ``local.cfg``), then::

    make config

5. Install the new init script and start::

    sudo cp /etc/init.d/destinet /etc/init.d/destinet.py2
    sudo cp init_destinet /etc/init.d/destinet
    sudo /etc/init.d/destinet start

6. Change the cron jobs of the ``edw`` user (``crontab -e``) to the new
   install; repozo writes to a new directory, so the Python 2 backups are kept
   apart::

    * * * * * /var/local/destinet/destinet.eu/bin/mail-sender /var/local/destinet/destinet.eu/var/naaya-mail-queue
    */15 * * * * /var/local/destinet/destinet.eu/bin/zope-instance-async run /var/local/destinet/destinet.eu/bin/heartbeat
    0 2 * * * /var/local/destinet/destinet.eu/.venv/bin/repozo -Bz -r /var/local/repozo-py3/ -f /var/local/destinet/destinet.eu/var/filestorage/Data.fs > /dev/null 2>&1
    00 04 * * Tue /var/local/destinet/destinet.eu/bin/zeopack

   The ``lynx`` jobs (catalog rebuild, LinkChecker) call https://destinet.eu
   and stay unchanged. Create ``/var/local/repozo-py3`` first.

7. Check the site, the map, the search and the mail queue.

Rollback: stop the new install, copy ``/etc/init.d/destinet.py2`` back to
``/etc/init.d/destinet``, restore the old cron jobs and start it; the Python 2
data is not changed by the migration.

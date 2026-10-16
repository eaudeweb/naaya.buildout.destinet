DestiNet buildout
=================

Zope 6 / Python 3 buildout for destinet.eu. Shared Naaya configuration
(``base.cfg``, ``zope6-versions.cfg``, migration scripts) comes from
https://github.com/eaudeweb/naaya.buildout.naaya, checked out in
``src/naaya.buildout.naaya``.

Prerequisites
-------------

* Python 3 with the ``venv`` module
* git, and access to github.com/eaudeweb/naaya.buildout.naaya
* a C compiler (``build-essential`` on Debian), used to build haproxy

Installation
------------

1. Create ``secret.cfg`` next to ``buildout.cfg``::

    [secrets]
    GOOGLE_AUTH_CLIENT_ID =
    GOOGLE_AUTH_CLIENT_SECRET =
    GOOGLE_MAPS_API_KEY =
    GOOGLE_GEOLOCATION_API_KEY =
    SENTRY_DSN =

2. Clone ``src/naaya.buildout.naaya`` and create the venv with
   ``zc.buildout`` and ``setuptools`` from ``requirements.txt``::

    make bootstrap

   Without SSH access to GitHub::

    make bootstrap NAAYA_REPO=https://github.com/eaudeweb/naaya.buildout.naaya.git

3. Run buildout and add the Naaya ZCML overrides::

    make install

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

    make migrate DATAFS=<path to Data.fs> INSTANCE=zope-instance-0

The last step rebuilds every catalog and packs the database. To rebuild the
catalogs again later (with ``zeoserver`` running for ZEO client instances)::

    bin/zope-instance-0 run src/naaya.buildout.naaya/migration/migrate_zodb.py --reindex-only

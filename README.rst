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
catalogs again later (with ``zeoserver`` running for ZEO client instances)::

    bin/zope-instance-0 run src/naaya.buildout.naaya/migration/migrate_zodb.py --reindex-only

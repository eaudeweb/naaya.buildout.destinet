INSTANCE ?= zope-instance-0
DATAFS ?= var/filestorage/Data.fs
NAAYA_BUILDOUT := src/naaya.buildout.naaya
NAAYA_REPO ?= git@github.com:eaudeweb/naaya.buildout.naaya.git
NAAYA_BRANCH ?= pip
BUNDLES_REPO ?= git@github.com:eaudeweb/naaya.bundles.NaayaBundles-DESTINET.git
BUNDLES_BRANCH ?= python3

.PHONY: bootstrap fix-permissions

bootstrap:
	test -d $(NAAYA_BUILDOUT) || git clone --branch $(NAAYA_BRANCH) $(NAAYA_REPO) $(NAAYA_BUILDOUT)
	test -d src/NaayaBundles-DESTINET || git clone --branch $(BUNDLES_BRANCH) $(BUNDLES_REPO) src/NaayaBundles-DESTINET

# '-include' so 'make bootstrap' works before src/naaya.buildout.naaya exists
-include $(NAAYA_BUILDOUT)/pip/site.mk
-include $(NAAYA_BUILDOUT)/migration/migrate.mk

install: haproxy fix-permissions

# The edw group edits these
fix-permissions:
	chmod -fR g+w bin parts src || true

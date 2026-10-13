INSTANCE ?= zope-instance-0
DATAFS ?= ../var/filestorage/Data.fs
NAAYA_BUILDOUT := src/naaya/buildout/Naaya
NAAYA_REPO ?= git@github.com:eaudeweb/naaya.git
NAAYA_BRANCH ?= python3
PYTHON ?= python3

.PHONY: bootstrap install

bootstrap:
	test -d src/naaya || git clone --branch $(NAAYA_BRANCH) $(NAAYA_REPO) src/naaya
	test -x bin/pip || $(PYTHON) -m venv .
	bin/pip install -r requirements.txt

install:
	bin/buildout
	$(NAAYA_BUILDOUT)/fix-buildout.sh

# '-include' so 'make bootstrap' works before src/naaya exists
-include $(NAAYA_BUILDOUT)/migration/migrate.mk

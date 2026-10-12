INSTANCE ?= zope-instance-0
DATAFS ?= ../var/filestorage/Data.fs
NAAYA_BUILDOUT := src/naaya/buildout/Naaya

.PHONY: install

install:
	bin/buildout
	$(NAAYA_BUILDOUT)/fix-buildout.sh

include $(NAAYA_BUILDOUT)/migration/migrate.mk

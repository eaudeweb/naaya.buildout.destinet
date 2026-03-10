INSTANCE ?= zope-instance-0
DATAFS ?= ../var/filestorage/Data.fs

.PHONY: install migrate

install:
	bin/buildout
	@./fix-buildout.sh

migrate:
	@echo "=== Migrating Data.fs for $(INSTANCE) ==="
	@echo ""
	@MARKER_DIR=$$(dirname "$(DATAFS)"); \
	if [ ! -f "$$MARKER_DIR/.zodbupdate-done" ]; then \
		echo "[Step 0] Ensuring zodbupdate is installed"; \
		pip install -q zodbupdate; \
		echo ""; \
		echo "[Step 1/3] zodbupdate --convert-py3"; \
		parts/$(INSTANCE)/bin/interpreter -c "import sys; sys.argv = ['zodbupdate', '--convert-py3', '--encoding', 'latin-1', '--encoding-fallback', 'latin-1', '-f', '$(DATAFS)']; from zodbupdate.main import main; main()"; \
		touch "$$MARKER_DIR/.zodbupdate-done"; \
	else \
		echo "[Step 1/3] zodbupdate --convert-py3: SKIPPED (already done)"; \
	fi
	@echo ""
	@echo "[Step 2/3] fix_provides"
	parts/$(INSTANCE)/bin/interpreter fix_provides.py $(DATAFS)
	@echo ""
	@echo "[Step 3/3] Zope-level fixes (PAS, LDAP, catalog)"
	bin/$(INSTANCE) run migrate_zodb.py
	@echo ""
	@echo "=== Migration complete ==="
	@echo "Start with: bin/$(INSTANCE) fg"
	@echo "Then reindex catalog from ZMI: portal_catalog -> Advanced -> Update Catalog"

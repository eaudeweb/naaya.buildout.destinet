"""
Post-zodbupdate ZODB migration fixes for Zope 5 / Python 3.

Run with: bin/<instance> run migrate_zodb.py

This handles all fixes that require the Zope app object (after zodbupdate
and fix_provides have been run on the raw Data.fs).

Steps:
  1. Replace broken PAS CookieAuthHelper (PlonePAS -> basic PAS)
  2. Deactivate plone.session PAS plugin
  3. Update LDAP auth source obj_path (ldap-plugin -> pasldap)
  4. Fix broken TextIndex -> ZCTextIndex in portal_catalog
  5. Fix relative ajax-loader.gif URL in ZODB slick-theme.css
  6. Rename bobobase_modification_time -> modification_time in glossary catalogs
"""

import sys
import transaction
from Testing.makerequest import makerequest

app = makerequest(app)  # noqa: F821

dry_run = '--dry-run' in sys.argv


def step_fix_pas_cookie(app):
    """Replace PlonePAS CookieAuthHelper with basic PAS CookieAuthHelper."""
    pas = getattr(app, 'acl_users', None)
    if pas is None:
        print("  No acl_users found at app root, skipping")
        return

    old = getattr(pas, 'credentials_cookie_auth', None)
    if old is None:
        print("  No credentials_cookie_auth plugin, skipping")
        return

    cls_name = type(old).__name__
    if cls_name == 'CookieAuthHelper':
        print("  credentials_cookie_auth is already basic CookieAuthHelper")
        return

    print(f"  Replacing {cls_name} with basic CookieAuthHelper")

    from Products.PluggableAuthService.plugins.CookieAuthHelper import (
        CookieAuthHelper,
    )
    from Products.PluggableAuthService.interfaces.plugins import (
        IChallengePlugin,
        ICredentialsResetPlugin,
        ICredentialsUpdatePlugin,
        IExtractionPlugin,
    )

    plugins = pas.plugins

    # Record which interfaces the old plugin was active for
    active_for = []
    for iface in [ICredentialsUpdatePlugin, ICredentialsResetPlugin,
                  IExtractionPlugin, IChallengePlugin]:
        active = [id for id, p in plugins.listPlugins(iface)]
        if 'credentials_cookie_auth' in active:
            active_for.append(iface)
            plugins.deactivatePlugin(iface, 'credentials_cookie_auth')

    # Preserve settings
    cookie_name = getattr(old, 'cookie_name', '__ac')
    login_path = getattr(old, 'login_path', 'login_form')

    # Replace
    pas._delObject('credentials_cookie_auth')
    new_plugin = CookieAuthHelper('credentials_cookie_auth')
    new_plugin.cookie_name = cookie_name
    new_plugin.login_path = login_path
    pas._setObject('credentials_cookie_auth', new_plugin)

    # Re-activate
    for iface in active_for:
        plugins.activatePlugin(iface, 'credentials_cookie_auth')
        print(f"    Re-activated for {iface.__name__}")

    print(f"  Done (cookie_name={cookie_name}, login_path={login_path})")


def step_deactivate_plone_session(app):
    """Deactivate plone.session plugin (requires plone.keyring, unavailable)."""
    pas = getattr(app, 'acl_users', None)
    if pas is None:
        return

    session = getattr(pas, 'session', None)
    if session is None:
        print("  No 'session' plugin, skipping")
        return

    from Products.PluggableAuthService.interfaces.plugins import (
        IAuthenticationPlugin,
        ICredentialsResetPlugin,
        ICredentialsUpdatePlugin,
        IExtractionPlugin,
    )

    plugins = pas.plugins
    deactivated = []
    for iface in [ICredentialsUpdatePlugin, ICredentialsResetPlugin,
                  IAuthenticationPlugin, IExtractionPlugin]:
        active = [id for id, p in plugins.listPlugins(iface)]
        if 'session' in active:
            plugins.deactivatePlugin(iface, 'session')
            deactivated.append(iface.__name__)

    if deactivated:
        print(f"  Deactivated 'session' from: {', '.join(deactivated)}")
    else:
        print("  'session' plugin was already inactive")


def step_fix_ldap_sources(app):
    """Update LDAP auth source obj_path from ldap-plugin to pasldap."""
    fixed = 0
    for site_id in app.objectIds():
        try:
            site = app[site_id]
            if not hasattr(site, 'getAuthenticationTool'):
                continue
            auth_tool = site.getAuthenticationTool()
            for src in auth_tool.getSources():
                if hasattr(src, 'obj_path') and 'ldap-plugin' in src.obj_path:
                    old_path = src.obj_path
                    src.obj_path = 'acl_users/pasldap'
                    print(f"  {site_id}: {old_path} -> {src.obj_path}")
                    fixed += 1
        except Exception as e:
            print(f"  {site_id}: error - {e}")

    if not fixed:
        print("  No LDAP sources needed updating")


def _fix_broken_indexes_in_catalog(catalog, catalog_path):
    """Replace broken TextIndex/TextIndexNG3 indexes with ZCTextIndex in a catalog."""
    from Products.ZCatalog.ZCatalog import ZCatalog
    if not isinstance(catalog, ZCatalog):
        return

    inner = catalog._catalog

    # Find broken indexes (access raw index to avoid __of__ on broken objects)
    broken = []
    for idx_name in list(inner.indexes.keys()):
        try:
            idx = inner.indexes[idx_name]
            if not hasattr(idx, '_apply_index'):
                broken.append(idx_name)
        except Exception:
            broken.append(idx_name)

    if not broken:
        return

    print(f"    {catalog_path}: {len(broken)} broken: {broken}")

    # Create Lexicon if missing
    if 'Lexicon' not in catalog.objectIds():
        from Products.ZCTextIndex.ZCTextIndex import PLexicon
        from Products.ZCTextIndex.Lexicon import (
            CaseNormalizer,
            Splitter,
            StopWordRemover,
        )
        lexicon = PLexicon('Lexicon', 'Default lexicon',
                           Splitter(), CaseNormalizer(), StopWordRemover())
        catalog._setObject('Lexicon', lexicon)
        print(f"    Created Lexicon in {catalog_path}")

    # Replace broken indexes
    extra = type('Extra', (), {
        'doc_attr': '',
        'index_type': 'Okapi BM25 Rank',
        'lexicon_id': 'Lexicon',
    })()

    for idx_name in broken:
        catalog.delIndex(idx_name)
        extra.doc_attr = idx_name
        catalog.addIndex(idx_name, 'ZCTextIndex', extra=extra)
        print(f"    Replaced {idx_name} -> ZCTextIndex")


def _find_all_catalogs(container, path=''):
    """Recursively find all ZCatalog instances in the ZODB."""
    from Products.ZCatalog.ZCatalog import ZCatalog
    results = []
    try:
        ids = container.objectIds()
    except Exception:
        return results
    for obj_id in ids:
        obj_path = f"{path}/{obj_id}" if path else obj_id
        try:
            obj = container[obj_id]
        except Exception:
            continue
        if isinstance(obj, ZCatalog):
            results.append((obj, obj_path))
        else:
            # Look one level deeper in site-like containers
            try:
                sub_ids = obj.objectIds()
            except Exception:
                continue
            for sub_id in sub_ids:
                sub_path = f"{obj_path}/{sub_id}"
                try:
                    sub_obj = obj[sub_id]
                except Exception:
                    continue
                if isinstance(sub_obj, ZCatalog):
                    results.append((sub_obj, sub_path))
                else:
                    # One more level for nested tools (e.g. thesaurus/catalog)
                    try:
                        for deep_id in sub_obj.objectIds():
                            deep_path = f"{sub_path}/{deep_id}"
                            try:
                                deep_obj = sub_obj[deep_id]
                                if isinstance(deep_obj, ZCatalog):
                                    results.append((deep_obj, deep_path))
                            except Exception:
                                continue
                    except Exception:
                        continue
    return results


def step_fix_catalog_indexes(app):
    """Replace broken TextIndex/TextIndexNG3 instances with ZCTextIndex in all catalogs."""
    catalogs = _find_all_catalogs(app)
    if not catalogs:
        print("  No catalogs found")
        return

    print(f"  Found {len(catalogs)} catalog(s)")
    fixed_any = False
    for catalog, catalog_path in catalogs:
        before = len(catalog._catalog.indexes)
        _fix_broken_indexes_in_catalog(catalog, catalog_path)
        if len(catalog._catalog.indexes) != before or any(
            not hasattr(catalog._catalog.indexes.get(k), '_apply_index', )
            for k in catalog._catalog.indexes.keys()
        ):
            fixed_any = True

    if not fixed_any:
        print("  No broken indexes found in any catalog")
    else:
        print("  NOTE: Run 'Update Catalog' from ZMI to reindex")


def step_fix_slick_theme_css(app):
    """Fix relative ajax-loader.gif URL in ZODB slick-theme.css files.

    The Slick carousel theme CSS contains url("./ajax-loader.gif") which
    resolves relative to the skin scheme path (e.g.
    portal_layout/destinet/colorscheme/ajax-loader.gif) causing a 404.
    Replace with an absolute URL to /++resource++Products.Naaya/ajax-loader.gif.
    """
    fixed = 0
    for site_id in app.objectIds():
        try:
            site = app[site_id]
            layout = getattr(site, 'portal_layout', None)
            if layout is None:
                continue
        except Exception:
            continue

        for skin_id in layout.objectIds():
            try:
                skin = layout[skin_id]
                if not hasattr(skin, 'objectIds'):
                    continue
                for scheme_id in skin.objectIds():
                    scheme = skin[scheme_id]
                    if not hasattr(scheme, 'objectIds'):
                        continue
                    for obj_id in scheme.objectIds():
                        if 'slick' not in obj_id.lower():
                            continue
                        obj = scheme[obj_id]
                        content = None
                        if hasattr(obj, 'read'):
                            content = obj.read()
                        elif hasattr(obj, 'data'):
                            content = obj.data
                            if isinstance(content, bytes):
                                content = content.decode('utf-8', errors='replace')
                            else:
                                content = str(content)
                        if not content or 'ajax-loader.gif' not in content:
                            continue

                        target = '/++resource++Products.Naaya/ajax-loader.gif'
                        new_content = content.replace(
                            'url("./ajax-loader.gif")',
                            'url("%s")' % target
                        ).replace(
                            "url('./ajax-loader.gif')",
                            "url('%s')" % target
                        ).replace(
                            'url(./ajax-loader.gif)',
                            'url(%s)' % target
                        ).replace(
                            'url("/misc_/Naaya/ajax-loader.gif")',
                            'url("%s")' % target
                        ).replace(
                            "url('/misc_/Naaya/ajax-loader.gif')",
                            "url('%s')" % target
                        ).replace(
                            'url(/misc_/Naaya/ajax-loader.gif)',
                            'url(%s)' % target
                        )
                        if new_content != content:
                            path = '%s/%s/%s/%s' % (site_id, skin_id, scheme_id, obj_id)
                            # Write back
                            if hasattr(obj, 'write'):
                                obj.write(new_content)
                            elif hasattr(obj, 'update_data'):
                                obj.update_data(new_content.encode('utf-8'))
                            else:
                                obj.data = new_content.encode('utf-8')
                            obj._p_changed = True
                            print("  Fixed: %s" % path)
                            fixed += 1
            except Exception as e:
                print("  Error in %s/%s: %s" % (site_id, skin_id, e))

    if not fixed:
        print("  No slick-theme.css files needed fixing")


def step_fix_glossary_catalogs(app):
    """Rename bobobase_modification_time -> modification_time in glossary catalogs.

    In Zope 5, bobobase_modification_time() was removed and replaced by
    modification_time(). The NaayaGlossary code already uses the new name,
    but existing ZODB catalogs still have the old index and column names.
    """
    from Products.ZCatalog.ZCatalog import ZCatalog

    fixed = 0
    for site_id in app.objectIds():
        try:
            site = app[site_id]
            if not hasattr(site, 'objectIds'):
                continue
        except Exception:
            continue

        # Find glossary objects (they have a GlossaryCatalog child)
        try:
            site_ids = site.objectIds()
        except Exception:
            continue

        for obj_id in site_ids:
            try:
                obj = site[obj_id]
                catalog = getattr(obj, 'GlossaryCatalog', None)
                if catalog is None or not isinstance(catalog, ZCatalog):
                    continue
            except Exception:
                continue

            inner = catalog._catalog

            # Check if we need to fix this catalog
            has_old = 'bobobase_modification_time' in inner.indexes
            has_new = 'modification_time' in inner.indexes
            if has_old and not has_new:
                # Rename index: delete old, add new
                catalog.delIndex('bobobase_modification_time')
                catalog.addIndex('modification_time', 'FieldIndex')
                print(f"    {site_id}/{obj_id}: renamed index "
                      f"bobobase_modification_time -> modification_time")

                # Rename column if present
                if 'bobobase_modification_time' in inner.schema:
                    catalog.delColumn('bobobase_modification_time')
                    if 'modification_time' not in inner.schema:
                        catalog.addColumn('modification_time')
                    print(f"    {site_id}/{obj_id}: renamed column "
                          f"bobobase_modification_time -> modification_time")
                fixed += 1
            elif not has_old and not has_new:
                # Neither exists — add the new one
                catalog.addIndex('modification_time', 'FieldIndex')
                if 'modification_time' not in inner.schema:
                    catalog.addColumn('modification_time')
                print(f"    {site_id}/{obj_id}: added missing "
                      f"modification_time index+column")
                fixed += 1

    if not fixed:
        print("  All glossary catalogs already up to date")
    else:
        print(f"  Fixed {fixed} glossary catalog(s)")
        print("  NOTE: Run rebuildCatalog from ZMI on each glossary to reindex")


# --- Run all steps ---

STEPS = [
    ("Fix PAS CookieAuthHelper", step_fix_pas_cookie),
    ("Deactivate plone.session plugin", step_deactivate_plone_session),
    ("Update LDAP auth source paths", step_fix_ldap_sources),
    ("Fix broken TextIndex -> ZCTextIndex", step_fix_catalog_indexes),
    ("Fix slick-theme.css ajax-loader.gif URL", step_fix_slick_theme_css),
    ("Fix glossary catalog bobobase_modification_time", step_fix_glossary_catalogs),
]

print("=" * 60)
print("Naaya ZODB migration fixes for Zope 5 / Python 3")
if dry_run:
    print("DRY RUN - no changes will be committed")
print("=" * 60)

for i, (label, func) in enumerate(STEPS, 1):
    print("\n[%d/%d] %s" % (i, len(STEPS), label))
    func(app)

if dry_run:
    print("\nDRY RUN - aborting transaction")
    transaction.abort()
else:
    print("\nCommitting transaction...")
    transaction.commit()
    print("Done.")

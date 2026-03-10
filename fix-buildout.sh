#!/bin/bash
# Post-buildout fixups for the destinet instances.
# Run this after each buildout.
#
# Products.CMFPlone is a transitive dependency:
#   pas.plugins.ldap -> yafowil.plone -> Products.CMFPlone
# We KEEP the egg (Python imports need it) but EXCLUDE its ZCML
# so that its AppTraverser and Plone views don't get registered.

# Register pas.plugins.ldap and exclude problematic ZCML packages.
# This file is loaded from package-includes BEFORE five:loadProducts,
# so the excludes take effect before Zope auto-discovers Products.*.
for pkg_dir in parts/*/etc/package-includes; do
    if [ -d "$pkg_dir" ]; then
        cat > "$pkg_dir/016.5-pas.plugins.ldap-configure.zcml" << 'ZCML'
<configure xmlns="http://namespaces.zope.org/zope"
           xmlns:zcml="http://namespaces.zope.org/zcml">
  <configure zcml:condition="installed Products.CMFPlone">
    <exclude package="Products.CMFPlone" />
  </configure>
  <configure zcml:condition="installed pas.plugins.ldap">
    <include package="pas.plugins.ldap" />
  </configure>
</configure>
ZCML
        echo "Added pas.plugins.ldap ZCML to $pkg_dir"

        # Disable plone.protect CSRF auto-protection (not needed for Naaya)
        cat > "$pkg_dir/999-additional-overrides.zcml" << 'ZCML'
<configure xmlns="http://namespaces.zope.org/zope">

<adapter
    factory="Products.NaayaCore.nocsrf.NoOpTransform"
    name="plone.protect.autocsrf"
    />

</configure>
ZCML
        echo "Added CSRF override to $pkg_dir"
    fi
done

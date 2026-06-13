# Minimal demo state: install a package AND manage a config file.
#
# Applied with:  salt '*' state.apply demo
# (the `demo` arg maps to salt://demo/init.sls in the master's file_roots)
#
# Both states are idempotent: pkg.installed is a no-op once htop is present,
# and file.managed only rewrites the file when the rendered content/mode drifts.
# So a second `state.apply demo` reports zero changes.

# 1) Install a package.
demo-package:
  pkg.installed:
    - name: htop

# 2) Manage a config file, rendered from a Jinja template that pulls from
#    grains (minion-side facts) and pillar (master-assigned data).
/etc/salt-demo.conf:
  file.managed:
    - source: salt://demo/files/banner.j2
    - template: jinja
    - user: root
    - group: root
    - mode: '0644'
    - require:
        # don't write the config until the package is in place
        - pkg: demo-package

# Pillar top map (pillar_roots base). Assigns the `demo` pillar to the minion.
# Pillar data is master-side and only exposed to matched minions.
base:
  'salt-minion':
    - demo

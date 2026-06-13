# Highstate map (file_roots base). Targets the minion by its id and assigns
# the `demo` state. `salt '*' state.apply` (no args) reads this; the idempotency
# proof uses `state.apply demo` to run just the demo state directly.
base:
  'salt-minion':
    - demo

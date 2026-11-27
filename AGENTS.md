# Python examples and tests

Local examples must contain exactly the code displayed in the corresponding GitBook chapter, including Network and USB tabs. GitBook is the authority; do not add independent example implementations or duplicate receiver wrappers.

Keep chapter scripts in `examples/documentation/`, map every Python block in `catalog.json`, and keep SDK regression tests in `tests/`. Device diagnostics use `asmagic-test`.

After an authorized chapter code change, run `python tools/sync_documentation_examples.py --gitbook ../gitbook`, then `python tools/sync_documentation_examples.py --check --gitbook ../gitbook`. Import never overwrites GitBook. Update mappings deliberately for chapter/block additions or removals; never weaken the drift check to accept mismatched code.

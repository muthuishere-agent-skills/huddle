# Third-Party Licenses — huddle

`huddle` bundles **no third-party code**. Its scripts import only the Python
standard library (`concurrent`, `datetime`, `getpass`, `json`, `os`, `pathlib`,
`re`, `shutil`, `subprocess`, `sys`, `tempfile`) alongside huddle's own modules,
and the repository vendors no dependency trees.

There is therefore nothing to attribute here. huddle itself is MIT — see `LICENSE`.

If a third-party dependency is ever added, regenerate this file (`pip-licenses`)
before publishing a release.

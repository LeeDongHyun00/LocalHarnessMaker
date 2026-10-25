Finish unpack.py's streaming tar extractor. Keep extract(source, destination,
*, max_files, max_bytes, dry_run=False) -> dict. source is a binary readable
stream, possibly non-seekable; destination's parent already exists.

AX1. Consume tar input in streaming mode; accept only regular files and directories. Reject links, devices and other entry types with ValueError('type'). Reject absolute names, any '..' component, backslashes or colon-bearing components with ValueError('path'). Normalize repeated '/' and '.' components; an empty normalized name is a type error.
AX2. Reject duplicate normalized paths and file/directory ancestor collisions with ValueError('alias'), including a file arriving after an already-seen descendant. A directory may be explicitly listed after an implicit parent directory. Do not follow archive links or call extractall.
AX3. max_files counts regular entries and max_bytes sums their declared uncompressed sizes. Nonnegative limits are inclusive; negative limits or a limit exceeded raise ValueError('quota'). Copy content in chunks of at most 65536 bytes without seeking the source. A truncated/broken archive may raise tarfile's own exception.
AX4. An existing destination, including a dangling symlink, is ValueError('destination'). Publish a completely validated extraction by renaming one temporary sibling directory only after reading the whole archive. Every failure leaves destination absent and removes temporary files; preserve preexisting siblings. An empty archive publishes an empty directory.
AX5. Return {'files': int, 'bytes': int, 'paths': sorted normalized regular-file names}. dry_run=True consumes and validates exactly the same archive and returns the same summary but creates no paths at all, including temporary files. Dry-run failures follow the same rejection rules.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.

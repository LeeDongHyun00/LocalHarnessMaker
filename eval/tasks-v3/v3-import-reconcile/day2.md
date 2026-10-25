Add resumable chunks to reconcile.py without changing the existing reconciliation
choices. A fresh session can inspect retained files.

IR4. ingest_chunk(token, rows) materializes the iterable and processes it as one
ordered chunk, returning the same per-row statuses as ingest. token is a nonempty
string; invalid token raises ValueError('token') before any state change.
Remember the token with its complete canonical JSON row-list bytes and returned
statuses. Replaying the identical token/content returns a fresh copy of the
original statuses and has no effects, even if intervening rows changed state.
Reusing a token with different row content raises ValueError('chunk') before
changing state. Rows supplied to this API are JSON-serializable.
IR5. Save/load must retain completed chunk records under the additional key
'chunks': mapping token to {'rows': canonical-row-list JSON string,
'statuses': status list}. load still accepts old snapshots without chunks.
A rejected row within a chunk neither rolls back good rows nor weakens its
original rejection boundary. Continue after reopen; conflicting/rejected rows
must preserve the preceding session's ordering and replacement decisions.
Run the same test command and add regression tests.

# ADR index and numbering policy

The repository contains legacy ADR filename collisions for IDs 055–061, 065,
and 071–073. They are retained for history and must not be silently renamed
because external status documents may refer to their original paths.

New decisions use the next unused numeric ID and a unique filename. A future
cleanup may assign stable IDs through an explicit migration table; until then,
the filename plus title is the canonical identity for legacy records.

Known legacy collisions:

- 055, 056, 057, 058, 059, 060, 061
- 065
- 071, 072, 073

# Collaboration Permission Matrix

| Capability | Owner | Caregiver | Viewer |
|---|---:|---:|---:|
| View shared pet history | yes | yes | yes |
| Add owner-entered care/observations | yes | configured | no |
| View restricted clinical/medication sources | yes | configured | no |
| Manage members, exports, deletion, billing | yes | no | no |
| Ask source-grounded assistant | yes | configured and funded by requester | no unless enabled |

Authorization is checked before retrieval, citation, mutation and every thread reopen. Revocation is fail-closed and invalidates cached access.

# Data Safety Worksheet

Status: `SOURCE_DECLARATION_PENDING_PLAY_CONSOLE_REVIEW`

This worksheet covers the implemented PETi 0–17 surface only. Out-of-scope
collaboration, search projections, conversations, and future assistant
features are not declared as shipped functionality.

| Data category | Purpose | Collection | Sharing | Retention/deletion |
|---|---|---|---|---|
| Firebase identity | Authentication and account ownership | Required at sign-in | No sale; service authentication only | Tombstoned on account deletion |
| Pet profile | Pet selection and owner-entered profile | Optional, owner-entered | Not shared by default | Deleted with account |
| Source media/documents | User-requested checks and records | Only after picker/capture action | Sent to configured backend/provider only for requested operation | Retention class and account deletion policy apply |
| Care, measurements, records | Timeline and owner history | Owner-entered or confirmed candidates | Not shared by default | Deleted/tombstoned with account |
| Analysis outputs | Safety-oriented observations and provenance | Generated for requested operation | Not sold; backend storage only | Deleted with account; residual verification required |
| Notification/device token | Care reminders | Only when notifications are registered | Firebase delivery service | Removed on account deletion |
| Billing identifiers | Premium entitlement reconciliation | Only for purchase flows | Google Play verification boundary | Billing retention policy; token never exposed in logs |

PETi does not use location, contacts, advertising ID, unrestricted media
library access, or on-device AI models. Final declarations require operator
review against the actual Play Console forms and production configuration.

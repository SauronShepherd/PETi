# Permissions Worksheet

Status: `SOURCE_DECLARATION_PENDING_DEVICE_AND_PLAY_REVIEW`

| Capability | Mechanism | User control | Broad permission required |
|---|---|---|---|
| Backend access | HTTPS network | Implicit during requested action | No |
| Photo/document import | Browser file picker | User selects each item | No |
| Camera capture | System capture intent | User starts and accepts capture | No unrestricted library access |
| Notifications | Browser notification permission where enabled | User grants/denies | No location permission |
| Rewarded ads | AdMob SDK only in funding flow | User explicitly requests reward | No contacts/location permission |

PETi does not request location, contacts, phone, microphone, unrestricted
background media, or advertising-ID permissions. Final manifest and device
review must be checked against the signed release artifact.

# Developer messages

**Leah (Oct 21):** We should keep the provider reference on every attempt. It makes support reconstruction much easier.

**Sam (Oct 22):** The checkout response is now built from the order after commit. This avoids returning a stale inventory snapshot.

**Priya (Oct 23):** I noticed clients disagree about whether keys are opaque strings or identifiers. Please do not make the API silently rewrite customer input without a migration note.

**Leah (Oct 24):** The timeout report may be connection pooling. I am checking SQLite behavior next.

**Sam (Oct 25):** Replaying the same request from the API console is clean. The mobile request capture is still the most useful lead.

**Priya (Oct 26):** Please keep incident reproductions deterministic enough to run without the provider.

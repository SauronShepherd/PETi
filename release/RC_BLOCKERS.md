# Release Candidate Blockers

## External blockers

The bounded Gemini/Vertex provider smoke, Cloud Run topology, and synthetic
OIDC worker vertical slices are now verified in the non-production sandbox.
The RC remains blocked by customer-authenticated staging matrices, live
privacy residual evidence, accessibility/device review, signed Android
artifacts, store declarations, public legal pages, the required held-out and
specialist certification suites, and the final video/Devpost submission.

Source-side manifests and runbooks do not clear these gates. Use
`scripts/build_release_evidence.py` after each source change to refresh hashes,
then attach execution artifacts only from the exact frozen revision.

Read-only refreshes also confirm the DEV API/worker revisions, worker internal
ingress, least-privilege invoker bindings, a running `analysis-dev` queue, and
the enabled hourly maintenance Scheduler job. These observations reduce
configuration uncertainty but do not remove any blocker above: authenticated
full-product execution and independently reviewable release evidence are still
required.

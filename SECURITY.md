# Security Policy

## Supported version

Security fixes currently target the latest commit on `main`. This repository
is a local-first reference implementation and does not claim a production
support or response-time commitment.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature when it is available for
this repository. Otherwise contact the repository owner privately through the
contact method listed on their GitHub profile.

Do not include credentials, private documents, full prompts, retrieved
contexts, provider payloads, or unredacted runtime logs in a public issue.

Useful reports include the affected revision, reproducible steps using
synthetic data, impact, and any suggested mitigation. Receipt and remediation
timelines depend on maintainer availability.

## Current security boundary

The project validates inputs, keeps secrets in runtime configuration, bounds
provider calls, reconstructs sources from retrieved contexts, and runs its
container as a non-root user. It does **not** currently implement
authentication, authorization, tenant isolation, document ACL enforcement, or
production audit retention. Deployments requiring those controls must add and
verify them before exposing the service.

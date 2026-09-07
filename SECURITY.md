# Security Policy

## Reporting a vulnerability

**Use GitHub's private vulnerability reporting:**
[Report a vulnerability](https://github.com/ujconsulting/uj-isse-meta-framework/security/advisories/new)

That channel is enabled and monitored. It creates a private advisory visible only to you
and the maintainers — please use it instead of a public issue, so a fix can land before
the details are public.

We aim to acknowledge a report within a few working days. This is a small project
maintained alongside other work; if you have not heard back within a week, please say so
on the same advisory rather than assuming it was received.

## This is a fork

This repository is a fork of
[joseph-fajen/ISEE_Meta_Framework](https://github.com/joseph-fajen/ISEE_Meta_Framework),
so where you report depends on what you found:

- **A problem in this fork's own changes** — report here. The modified files are listed in
  the README under "About This Fork".
- **A problem inherited from the original** — worth reporting upstream as well, since it
  affects the original and every other fork. Reporting it here too is welcome; we would
  rather receive it twice than not at all.

If you cannot tell which it is, report it here and we will work it out.

## What is in scope

This is a research tool that orchestrates calls to third-party AI providers. The parts
worth looking at:

- The Flask interface in `app.py`, which binds `0.0.0.0` and has **no authentication** —
  it is built to run locally. If you find a way to make it do something a local user did
  not ask for, that is in scope.
- Handling of API credentials: they are read from the environment and must never reach
  logs, run outputs, reports or CSV exports.
- The subprocess boundary between `app.py` and `main.py`, where web parameters become a
  command line.
- Anything that writes to disk under `data/`, including path handling in the run and
  report writers.

**Out of scope:** the behaviour or content of the AI models themselves, and anything
about the providers' own APIs. Those belong to the respective provider.

## What we ask

Please do not run automated scanners against a deployment you do not own, and do not test
against anyone else's API credentials. A working proof of concept against your own local
instance is the most useful thing you can send.

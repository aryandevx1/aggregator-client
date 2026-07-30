# Aggregator Client

Code generation pipeline for the Aggregator Platform.

## Features

- YAML schema loader
- Schema validator
- Entity ID injection
- Tag locking
- Protobuf generation
- (Upcoming) Go generation
- (Upcoming) TypeScript generation
- (Upcoming) SQL migrations

---

## Requirements

- Python 3.13+
- Git

---

## Setup

Clone the repository

git clone ...

cd aggregator-client

Run the setup script

.\scripts\setup.ps1

Activate the virtual environment

.\.venv\Scripts\Activate.ps1

---

## Running tests

pytest

---

## Project structure

generator/
tests/
scripts/
.githooks/
.github/

---

## CI

Every push runs:

- Local pre-push hook
- GitHub Actions
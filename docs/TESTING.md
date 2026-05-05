# Testing Guide

## Backend

Run backend tests from repository root:

```bash
python -m pytest tests/backend -q
```

Current backend coverage:

1. Health endpoint contract.
2. Request size and rate-limit middleware behavior.
3. Reports list/get/html route handling and 404 path.

## Frontend

Run frontend tests:

```bash
npm run test
```

Current frontend coverage:

1. Utility functions in `src/utils/textStats.ts`.
2. API service request payloads and error propagation in `src/services/api.ts`.

## Full Local Quality Loop

```bash
npm ci
npm run test
npm run build
python -m pytest tests/backend -q
```

## CI Expectations

GitHub Actions workflow runs:

1. Frontend tests.
2. Frontend build.
3. Backend tests.

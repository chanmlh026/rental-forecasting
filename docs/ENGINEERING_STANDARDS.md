# UK Rental Forecasting - Engineering Standards

## 1. Architecture

- Use modular, reusable components with clear responsibilities.
- Separate business logic from storage and cloud infrastructure.
- Design for both local and future GCP deployment.

## 2. Configuration Management

- Keep configurable parameters separate from application logic.
- Centralise configuration and validate its values.
- Avoid hardcoded machine-specific paths.

## 3. Data & Model Versioning

- Preserve raw data snapshots and relevant source metadata.
- Track code, data, configuration and model versions.
- Ensure forecasts are traceable and reproducible.

## 4. Data Integrity

- Validate schemas, completeness, consistency and anomalies.
- Prevent data leakage and enforce point-in-time correctness.
- Never silently modify or discard problematic data.

## 5. Testing & Quality

- Implement appropriate unit, integration and end-to-end tests.
- Test normal, boundary and failure scenarios.
- Require evidence that acceptance criteria are satisfied.

## 6. Reliability

- Provide clear logging and error handling.
- Support safe retries, recovery and idempotent operations.
- Preserve previously validated outputs when failures occur.

## 7. Security

- Never hardcode credentials or commit secrets.
- Apply least-privilege access principles.
- Keep development and production environments appropriately isolated.

## 8. Development Governance

- Follow the approved methodology and task scope.
- Prefer simple, maintainable solutions over unnecessary complexity.
- Document significant decisions and assumptions.
- Obtain approval before major design changes.
- Report test results, limitations and outstanding risks.

**Implementation Principle:** Production-ready design from day one, incremental
implementation and evidence-based validation.

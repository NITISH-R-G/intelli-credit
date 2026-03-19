# Contributing to Intelli-Credit

Thank you for your interest in contributing to our project! 

## Code Standards
- **Python**: We strictly adhere to PEP-8 standards. Check your code using `flake8 .` before pushing.
- **JavaScript/TypeScript**: Ensure your code passes `npm run lint` locally.
- **Backend Type Annotations**: We require complete type hinting across the FastAPI backend routes. Ensure parameters and return types leverage standard Python typing or Pydantic models.

## Security Practices
- **Never check in secrets, API keys, or personal identifiable information.** Our CI pipeline runs Gitleaks.
- Enforce secure routes in FastAPI using the `verify_firebase_token` dependency.

## Database
- Please prioritize the use of `async_database.py` over legacy synchronous database integrations.

## Creating Pull Requests
1. Search via open issues or create a new issue for the feature you wish to build.
2. Form your work into cohesive git commits with clear descriptions.
3. Submit a PR against `main`. Ensure all CI checks (Linting, Tests, Cypress E2E) pass.

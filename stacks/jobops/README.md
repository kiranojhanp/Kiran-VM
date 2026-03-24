# JobOps Stack

Compose file: `stacks/jobops/compose.yaml`

Self-hosted job application tracker with AI-powered job scraping, resume tailoring, and email tracking.

## In Komodo

1. Create or open the `jobops` stack.
2. Set compose path to `stacks/jobops/compose.yaml`.
3. Add the variables below in the stack Environment.
4. Deploy (or Redeploy), then open `https://<JOBOPS_HOST>`.

## Stack environment variables

- `JOBOPS_HOST` (required): public hostname. Example: `jobops.fewa.app`.
- `SHARED_DOCKER_NETWORK` (optional): shared proxy network. Default: `internal-network`.

## Optional .env variables

Create a `.env` file in the stack directory for additional configuration:

- `MODEL`: LLM model for AI scoring (default: `google/gemini-3-flash-preview`)
- `RXRESUME_EMAIL` / `RXRESUME_PASSWORD`: RxResume credentials for PDF resume generation
- `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD`: Optional basic auth for write access
- `GMAIL_OAUTH_CLIENT_ID` / `GMAIL_OAUTH_CLIENT_SECRET`: Gmail OAuth for inbox tracking
- `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`: Adzuna API credentials
- `UKVISAJOBS_EMAIL` / `UKVISAJOBS_PASSWORD`: UK visa sponsorship jobs extractor

## Features

- Universal job scraping (LinkedIn, Indeed, Glassdoor, Adzuna, etc.)
- AI-powered job suitability scoring
- Resume tailoring with RxResume v4
- Gmail integration for automatic application tracking

# Security Policy — ANUBIS Platform

## Supported Versions

| Version | Security Support |
|---------|-----------------|
| 3.x     | ✅ Active        |
| 2.x     | ⚠️ Critical only |
| < 2.0   | ❌ End of life   |

## Reporting a Vulnerability

If you discover a security vulnerability in ANUBIS, please report it
responsibly. **Do not open a public GitHub issue.**

Contact: **info.rstanfield@gmail.com**
Subject line: `[SECURITY] ANUBIS Vulnerability Report`

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Your suggested fix (optional)

You will receive acknowledgment within 48 hours and a resolution timeline
within 7 business days.

## API Key Security

ANUBIS uses API key authentication (`X-ANUBIS-API-KEY` header). Production
deployments **must** set the `ANUBIS_API_KEY` environment variable to a
cryptographically secure random string.

```bash
# Generate a secure key (example)
python3 -c "import secrets; print('ANUBIS-' + secrets.token_hex(24).upper())"
```

Never commit API keys to source control. Use environment variables or a
secrets manager in all production deployments.

## Data

ANUBIS does not transmit portfolio data to external services. All analysis
is performed locally. When yfinance is enabled, stock price requests are
sent to Yahoo Finance's public API — no portfolio data is included in these
requests.

## © 2024-2026 Richard L. Stanfield / MAAT — All Rights Reserved

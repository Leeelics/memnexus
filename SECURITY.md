# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in MemNexus, please report it responsibly.

### How to Report

1. **Do not** open a public issue
2. Email security concerns to: [your-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix release**: Depends on severity
  - Critical: Within 1 week
  - High: Within 2 weeks
  - Medium: Within 1 month
  - Low: Next scheduled release

### Security Best Practices

When deploying MemNexus:

1. **Change default secret keys**
   ```bash
   export MEMNEXUS_SECRET_KEY="your-random-secret-key"
   ```

2. **Use HTTPS in production**
   - Configure SSL/TLS certificates
   - Use reverse proxy (Nginx/Traefik)

3. **Restrict CORS origins**
   ```python
   # In production, don't use "*"
   allow_origins=["https://your-domain.com"]
   ```

4. **Keep dependencies updated**
   ```bash
   pip list --outdated
   npm audit
   ```

5. **Run with minimal privileges**
   - Use dedicated user account
   - Limit file system access
   - Use container security features

## Known Security Considerations

### Current Limitations

- No built-in authentication (planned for future)
- CORS allows all origins by default (configure for production)
- No rate limiting (add reverse proxy for protection)

### Recommended Mitigations

1. **Network Level**
   - Deploy behind firewall
   - Use VPN for remote access
   - Restrict port access

2. **Application Level**
   - Add API key authentication
   - Implement rate limiting
   - Enable request logging

3. **Data Level**
   - Encrypt sensitive data at rest
   - Use secure connections (TLS)
   - Regular backups

## Security Updates

Security updates will be:
- Announced in GitHub Security Advisories
- Listed in CHANGELOG.md
- Tagged with `security` label

## Acknowledgments

We thank the following people for reporting security issues:

- [Your name] - [Issue description]

---

Last updated: 2026-02-20

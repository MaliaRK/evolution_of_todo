# Security Zero Trust Skill

## Purpose
This skill provides implementation details for applying Zero Trust security principles to cloud-native applications. It focuses on implementing JWT-based authentication, secret isolation, least privilege access, and secure service-to-service communication to ensure robust security posture across the entire system.

## Capabilities
- Implement JWT-based authentication and authorization systems
- Isolate and secure sensitive secrets using proper management practices
- Apply least privilege principles to all system components
- Establish secure service-to-service communication channels
- Prevent secret exposure and unauthorized access
- Implement comprehensive security validation and verification

## Implementation Details

### JWT-Based Authentication Implementation
- Generate and validate JWT tokens with proper signing algorithms
- Implement token expiration and refresh mechanisms
- Use RS256 or ES256 algorithms instead of HS256 for better security
- Validate token claims including issuer, audience, and expiration
- Implement proper token storage and transmission security
- Design token revocation and blacklisting mechanisms

### Secret Isolation and Management
- Store secrets in secure secret management systems (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault)
- Use environment variables or mounted volumes for secret access
- Never hardcode secrets in source code or configuration files
- Implement secret rotation and refresh mechanisms
- Encrypt secrets at rest and in transit
- Limit secret access to authorized services and personnel

### Least Privilege Implementation
- Grant minimal necessary permissions to services and users
- Implement role-based access control (RBAC) with granular permissions
- Use service accounts with limited scopes and permissions
- Regularly audit and review access permissions
- Implement just-in-time access for elevated privileges
- Apply the principle of least privilege to all system components

### Secure Service-to-Service Communication
- Implement mutual TLS (mTLS) for service authentication
- Use service mesh for secure communication (Istio, Linkerd)
- Validate service identities and certificates
- Encrypt all inter-service communication
- Implement proper authentication and authorization between services
- Monitor and log all service-to-service communication

### Frontend Security Validation
- Never trust input from frontend applications
- Implement proper input validation and sanitization
- Use API gateways for request validation and transformation
- Implement proper CORS policies and headers
- Validate authentication and authorization for all requests
- Protect against common web vulnerabilities (XSS, CSRF, etc.)

### Security Validation and Verification
- Implement comprehensive authentication validation
- Verify JWT tokens against trusted authorities
- Validate all user inputs and request parameters
- Implement proper error handling without information leakage
- Conduct regular security audits and penetration testing
- Monitor for security violations and anomalies

## Usage Guidelines

### JWT Implementation Best Practices:
```javascript
// Example JWT validation
const jwt = require('jsonwebtoken');

function validateToken(token, publicKey) {
  return jwt.verify(token, publicKey, {
    algorithms: ['RS256'],
    issuer: 'trusted-issuer',
    audience: 'my-app'
  });
}
```

### Secret Management:
- Use Dapr secrets building block for secret access
- Store secrets in encrypted format
- Implement secret rotation policies
- Audit secret access and usage
- Use temporary credentials when possible
- Never log or expose secrets in plain text

### Least Privilege Examples:
- Database users with minimal required permissions
- API keys with limited scope and expiration
- Kubernetes service accounts with minimal RBAC roles
- Cloud IAM roles with minimal necessary permissions
- File system permissions restricted to necessary access
- Network access controls limiting inter-service communication

### Security Validation Checklist:
1. Verify all secrets are properly isolated
2. Confirm JWT validation is implemented correctly
3. Validate service-to-service communication security
4. Check that frontend input is properly validated
5. Ensure authentication is required for protected resources
6. Verify that security policies are enforced consistently

### Prohibited Actions:
- Never commit secrets to version control
- Don't trust frontend input without validation
- Never skip authentication validation
- Don't use weak cryptographic algorithms
- Never expose sensitive information in logs
- Don't grant excessive privileges to services or users
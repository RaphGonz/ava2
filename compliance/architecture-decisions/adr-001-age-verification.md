# ADR-001: Pluggable Age Verification Architecture

**Status:** Accepted
**Date:** 2026-02-23
**Related Documents:**
- compliance/policies/age-verification-strategy.md
- compliance/policies/terms-of-service.md

---

## Context

The Ava platform serves adult content (intimate conversations, AI-generated imagery) and must enforce age restrictions to comply with regulations. The regulatory landscape is rapidly evolving in 2026:

- **Texas** (Jan 1, 2026): Requires "commercially reasonable" age verification for apps distributing adult content
- **Utah** (May 7, 2026): Similar requirements with potential fines for non-compliance
- **Louisiana** (July 1, 2026): Enforcement of age verification laws with app store restrictions
- **California** (Jan 1, 2027): Upcoming age verification requirements

**Current Approach:** Self-declaration checkbox at signup ("I confirm I am 18+"). This is simple to implement but may not meet the "commercially reasonable" threshold if enforcement is strict.

**Risk:** If we hardcode self-declaration into the application, upgrading to ID verification later requires a full rewrite of authentication, user onboarding, and session management. This creates technical debt and delays compliance when regulations tighten.

**Requirement:** The architecture must support future age verification methods (ID verification, biometric scanning, third-party verification services) without rearchitecting the application.

## Decision

We implement a **provider pattern** for age verification. All verification logic flows through an abstraction layer (`AgeVerificationManager`), which delegates to a pluggable provider implementation. The active provider is set via configuration.

### TypeScript Interface Definition

```typescript
/**
 * Age verification provider interface
 * All providers must implement this contract
 */
interface AgeVerificationProvider {
  /**
   * Verify user's age using provider-specific data
   * @param userId - Unique user identifier
   * @param data - Verification data (checkbox, ID document, selfie, etc.)
   * @returns VerificationResult with status and metadata
   */
  verify(userId: string, data: VerificationData): Promise<VerificationResult>;

  /**
   * Does this provider require periodic re-verification?
   * @returns true if re-verification is needed (e.g., every 30 days)
   */
  requiresReVerification(): boolean;

  /**
   * How long is a verification session valid?
   * @returns Session duration in minutes (Infinity for no expiration)
   */
  getSessionDuration(): number;
}

interface VerificationData {
  // Self-declaration provider
  declaredAge18Plus?: boolean;

  // ID verification provider (future)
  idDocument?: File;
  selfie?: File;

  // Biometric provider (future)
  biometricData?: BiometricScan;
}

interface VerificationResult {
  verified: boolean;
  method: string; // 'self-declaration', 'id-verification', 'biometric'
  timestamp: Date;
  requiresReVerification: boolean;
  confidence?: number; // Optional confidence score (0.0 to 1.0)
  errorMessage?: string; // If verification failed
}
```

### Verification Manager

```typescript
/**
 * Centralized age verification manager
 * All application code calls this manager, never checks verification flags directly
 */
class AgeVerificationManager {
  private provider: AgeVerificationProvider;

  constructor(provider: AgeVerificationProvider) {
    this.provider = provider;
  }

  /**
   * Swap the active provider (e.g., upgrade from self-declaration to ID verification)
   */
  setProvider(provider: AgeVerificationProvider): void {
    this.provider = provider;
  }

  /**
   * Verify a user's age
   * Application code calls this method everywhere age verification is needed
   */
  async verifyAge(userId: string, data: VerificationData): Promise<VerificationResult> {
    const result = await this.provider.verify(userId, data);

    // Log verification attempt (audit trail for compliance)
    await auditLog.record({
      event: 'age_verification_attempt',
      userId,
      method: result.method,
      verified: result.verified,
      timestamp: result.timestamp
    });

    return result;
  }

  /**
   * Check if a user needs re-verification
   */
  requiresReVerification(): boolean {
    return this.provider.requiresReVerification();
  }
}
```

### Phase 1 Provider: SelfDeclarationProvider

```typescript
/**
 * Self-declaration age verification (Phase 1)
 * Simple checkbox confirmation at signup
 */
class SelfDeclarationProvider implements AgeVerificationProvider {
  async verify(userId: string, data: VerificationData): Promise<VerificationResult> {
    if (!data.declaredAge18Plus) {
      return {
        verified: false,
        method: 'self-declaration',
        timestamp: new Date(),
        requiresReVerification: false,
        errorMessage: 'User declined age verification'
      };
    }

    return {
      verified: true,
      method: 'self-declaration',
      timestamp: new Date(),
      requiresReVerification: false
    };
  }

  requiresReVerification(): boolean {
    return false; // One-time verification, no re-verification needed
  }

  getSessionDuration(): number {
    return Infinity; // Never expires
  }
}
```

### Future Provider Stub: IDVerificationProvider

```typescript
/**
 * ID verification provider (Phase 2+)
 * Uses third-party services: Onfido, Veriff, Jumio, Stripe Identity
 */
class IDVerificationProvider implements AgeVerificationProvider {
  private apiClient: OnfidoClient; // or Veriff, Jumio, Stripe Identity

  constructor(apiKey: string) {
    this.apiClient = new OnfidoClient(apiKey);
  }

  async verify(userId: string, data: VerificationData): Promise<VerificationResult> {
    // Upload ID document and selfie to third-party API
    const response = await this.apiClient.verifyAge({
      idDocument: data.idDocument,
      selfie: data.selfie
    });

    return {
      verified: response.isAdult,
      method: 'id-verification',
      timestamp: new Date(),
      requiresReVerification: true,
      confidence: response.confidenceScore
    };
  }

  requiresReVerification(): boolean {
    return true; // Re-verify periodically (e.g., every 90 days)
  }

  getSessionDuration(): number {
    return 90 * 24 * 60; // 90 days in minutes
  }
}
```

### Configuration-Driven Provider Selection

```json
{
  "ageVerification": {
    "provider": "self-declaration",
    "config": {}
  }
}
```

To upgrade to ID verification:

```json
{
  "ageVerification": {
    "provider": "id-verification",
    "config": {
      "service": "onfido",
      "apiKey": "onfido-api-key",
      "reVerificationDays": 90
    }
  }
}
```

Application code remains unchanged—`AgeVerificationManager` loads the configured provider at startup.

### Application Usage

```typescript
// Initialize verification manager with configured provider
const provider = loadProviderFromConfig(); // Reads config.json
const verificationManager = new AgeVerificationManager(provider);

// Signup flow
async function handleSignup(email: string, password: string, ageData: VerificationData) {
  const userId = await createUserAccount(email, password);

  // Verify age (delegates to active provider)
  const result = await verificationManager.verifyAge(userId, ageData);

  if (!result.verified) {
    await deleteUserAccount(userId); // Rollback account creation
    throw new Error('Age verification required');
  }

  return { userId, message: 'Account created successfully' };
}

// Middleware: Check age verification before accessing intimate mode
async function requireAgeVerification(req, res, next) {
  const user = await getUser(req.userId);

  if (!user.ageVerified) {
    return res.status(403).json({ error: 'Age verification required' });
  }

  // Check if re-verification is needed
  if (verificationManager.requiresReVerification()) {
    const lastVerified = user.lastVerifiedAt;
    const sessionDuration = verificationManager.getSessionDuration();

    if (Date.now() - lastVerified > sessionDuration * 60 * 1000) {
      return res.status(403).json({ error: 'Re-verification required' });
    }
  }

  next();
}
```

**Key Principle:** Application code calls `AgeVerificationManager.verifyAge()` everywhere. Never check `user.ageVerified` flags directly. This ensures swapping providers is a configuration change, not a code change.

## Consequences

### Positive

1. **Future-proof:** When regulations require ID verification, we implement `IDVerificationProvider` and change configuration. No application code rewrite needed.

2. **Testable:** Each provider can be tested independently. Mock providers simplify unit testing.

3. **Compliance adaptability:** Different jurisdictions can use different providers (e.g., EU uses ID verification, US uses self-declaration).

4. **Audit trail:** All verification attempts flow through `AgeVerificationManager`, ensuring consistent logging.

5. **Data minimization:** Providers handle PII (ID documents, selfies). Application receives only verification result tokens. Privacy by design.

### Negative

1. **Over-engineering for Phase 1:** Self-declaration is simple—a single boolean flag. The provider pattern adds abstraction overhead for a feature that won't be used until regulatory enforcement tightens.

   **Mitigation:** Regulatory risk justifies the upfront investment. Rearchitecting later is far more expensive than building the abstraction now.

2. **Third-party dependencies:** Future ID verification requires third-party services (Onfido, Veriff, Stripe Identity), introducing vendor lock-in and API costs.

   **Mitigation:** Provider interface abstracts vendor specifics. Swapping from Onfido to Veriff is a provider implementation change, not an application rewrite.

3. **Re-verification complexity:** Some providers require periodic re-verification (e.g., every 30-90 days). This adds session management complexity.

   **Mitigation:** `requiresReVerification()` and `getSessionDuration()` methods make re-verification logic explicit. Providers that don't require re-verification (like self-declaration) return `false` and `Infinity`.

## Related Decisions

- **ADR-003 (Audit Logging):** Age verification events are logged in the consolidated `audit_log` table with minimal data (user_id, method, result).
- **Age Verification Strategy Document:** Full policy and regulatory context for age verification approach.

## Implementation Notes

- **Phase 1:** Implement `SelfDeclarationProvider` only. Stub `IDVerificationProvider` exists as documentation but is not used.
- **Phase 2+:** When regulations require ID verification, implement full `IDVerificationProvider` with third-party API integration.
- **Database schema:** Store only `user.age_verified: boolean` and `user.age_verification_method: string`. No PII (timestamps, IP addresses, uploaded documents).

---

**Last Updated:** 2026-02-23

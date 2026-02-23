# Age Verification Strategy

**Status:** DRAFT
**Created:** 2026-02-23
**Notice:** **REQUIRES ATTORNEY REVIEW BEFORE PUBLICATION** — This document is a framework for legal counsel to refine.

---

## 1. Overview

Ava enforces age restrictions to comply with regulations governing adult content platforms and ensure only adults access intimate features. This document outlines the current age verification approach, the pluggable architecture for future upgrades, and the 20+ avatar age floor enforcement.

**Core Principles:**
- **Current approach (Phase 1):** Self-declaration checkbox at signup
- **Future adaptability:** Pluggable architecture enables seamless upgrade to ID verification or biometric methods
- **Data minimization:** No unnecessary storage of verification metadata
- **Account age vs. avatar age:** Separate enforcement mechanisms

## 2. Current Approach: Self-Declaration (Phase 1)

### 2.1 Process

**One-Time Verification:** During account creation, users are presented with a self-declaration checkbox:

> "I confirm that I am 18 years of age or older."

**Mandatory Acceptance:** Checking the box is required to create an account. Declining the declaration results in complete denial of access—no secretary mode, no intimate mode, no account creation.

**No Re-Verification:** Once declared at signup, users are not prompted to verify age again (unless regulations require periodic re-verification in the future).

### 2.2 Data Minimization

To protect user privacy, the platform **does not store**:
- Timestamp of age declaration
- IP address at time of verification
- Device fingerprints or browser metadata
- Screenshots or proof of declaration

**What is logged:**
- `user_id`: Unique identifier for the user
- `verified: true`: Boolean confirmation that age was verified
- `method: 'self-declaration'`: Verification method used

**Audit Trail:** Age verification events are logged in the `audit_log` table for compliance purposes, but contain minimal data:

```json
{
  "user_id": "uuid",
  "event_type": "age_verification",
  "result": "success",
  "event_data": {
    "method": "self-declaration",
    "version": 1
  }
}
```

No timestamp or IP address is stored (data minimization principle).

### 2.3 Secondary Signals

While not explicit verification methods, the platform relies on implicit age signals:

**Phone Account Ownership (WhatsApp):** WhatsApp requires a phone number to create an account. Phone account ownership generally implies the user is an adult (though not guaranteed).

**Payment Card on File (Future):** When billing is implemented (Phase 7), possession of a valid payment card is an additional signal that the user is 18+ (credit cards require 18+ in most jurisdictions; debit cards imply bank account ownership).

**Note:** These secondary signals are not verification methods—they are supplementary indicators used in combination with self-declaration.

## 3. Pluggable Architecture for Future Upgrades

### 3.1 Regulatory Context

**2026 State Laws:** Texas (Jan 1, 2026), Utah (May 7, 2026), Louisiana (July 1, 2026), and California (Jan 1, 2027) have enacted laws requiring "commercially reasonable" age verification for apps distributing adult content.

**Self-Declaration Risk:** While self-declaration is simple to implement, it may not meet the "commercially reasonable" threshold if regulations are strictly enforced. The platform must be prepared to upgrade verification methods without rearchitecting the application.

### 3.2 AgeVerificationProvider Interface

The platform implements a **provider pattern** for age verification. All verification logic flows through an abstraction layer, allowing the active provider to be swapped via configuration.

**TypeScript Interface Definition:**

```typescript
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

### 3.3 Current Provider: SelfDeclarationProvider

**Phase 1 Implementation:**

```typescript
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
    return false; // One-time verification
  }

  getSessionDuration(): number {
    return Infinity; // Never expires
  }
}
```

**Usage in Application:**

```typescript
const verificationManager = new AgeVerificationManager(new SelfDeclarationProvider());

const result = await verificationManager.verifyAge(userId, {
  declaredAge18Plus: true
});

if (!result.verified) {
  throw new Error('Age verification required');
}
```

### 3.4 Future Providers

**IDVerificationProvider (Phase 2+):**

Uses third-party services (Onfido, Veriff, Jumio, Stripe Identity) to verify government-issued ID documents and selfie liveness checks.

```typescript
class IDVerificationProvider implements AgeVerificationProvider {
  private apiClient: OnfidoClient; // or Veriff, Jumio, etc.

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
      requiresReVerification: true, // Re-verify periodically
      confidence: response.confidenceScore
    };
  }

  requiresReVerification(): boolean {
    return true; // Re-verify every 90 days
  }

  getSessionDuration(): number {
    return 90 * 24 * 60; // 90 days in minutes
  }
}
```

**BiometricProvider (Phase 3+):**

Uses facial age estimation or other biometric signals for age verification.

```typescript
class BiometricProvider implements AgeVerificationProvider {
  async verify(userId: string, data: VerificationData): Promise<VerificationResult> {
    // Facial age estimation API call
    const estimatedAge = await biometricAPI.estimateAge(data.biometricData);

    return {
      verified: estimatedAge >= 18,
      method: 'biometric',
      timestamp: new Date(),
      requiresReVerification: true,
      confidence: estimatedAge.confidence
    };
  }

  requiresReVerification(): boolean {
    return true; // Re-verify every 30 days
  }

  getSessionDuration(): number {
    return 30 * 24 * 60; // 30 days in minutes
  }
}
```

### 3.5 Swapping Providers

**Configuration Change Only:**

To upgrade from self-declaration to ID verification:

1. Implement `IDVerificationProvider` class
2. Update configuration file:

```json
{
  "ageVerification": {
    "provider": "id-verification",
    "config": {
      "apiKey": "onfido-api-key",
      "reVerificationDays": 90
    }
  }
}
```

3. Application code remains unchanged—`AgeVerificationManager` automatically uses the new provider

**No Code Rewrite Needed:** This is the key benefit of the pluggable architecture. Swapping verification methods is a configuration change, not a code change.

### 3.6 Upgrade Path

**Trigger for Upgrade:**
- Regulatory enforcement actions against platforms using self-declaration
- State law clarification that self-declaration is insufficient
- Platform expansion to jurisdictions requiring ID verification

**Implementation Steps:**
1. Select third-party verification provider (Onfido, Veriff, Jumio, Stripe Identity)
2. Implement `IDVerificationProvider` class
3. Test verification flow in staging environment
4. Update production configuration to activate new provider
5. Communicate change to users (in-app notification, email)
6. Monitor verification success rates and user feedback

**Grandfathering Existing Users:** Decision TBD—do existing users (verified via self-declaration) need to re-verify with ID, or are they grandfathered? This depends on regulatory guidance and platform risk tolerance.

## 4. Avatar Age Floor: 20+ Enforcement

### 4.1 Separate from Account Age

**Account Age Verification:** Users must be 18+ to create an account (verified via methods above).

**Avatar Age Floor:** Users' fictional avatars must be configured with an age of **20 years or older**. This is a separate, stricter requirement.

**Rationale:** The 20+ floor provides additional safety margin beyond the legal 18+ threshold. It eliminates any ambiguity about fictional character maturity and reduces risk of inadvertently depicting characters that appear underage.

### 4.2 Enforcement Mechanism

**Form Validation:** The avatar creation form includes an age field with hard validation:

```typescript
// Avatar age validation
if (avatarAge < 20) {
  throw new ValidationError('Avatar age must be 20 or older');
}
```

**No Exceptions:** The 20+ floor is non-negotiable. Users cannot create avatars younger than 20, regardless of context or justification.

**Database Constraint:**

```sql
ALTER TABLE avatars
ADD CONSTRAINT avatar_age_minimum CHECK (age >= 20);
```

This ensures the 20+ floor is enforced at the database level, even if application code is bypassed.

### 4.3 User Communication

During avatar creation, users see clear guidance:

> **Avatar Age:** Your avatar must be 20 years of age or older. This is a platform requirement to ensure all characters are unambiguously adult.

## 5. Regulatory Compliance Monitoring

### 5.1 Ongoing Monitoring

The platform monitors regulatory developments in key jurisdictions:
- Texas, Utah, Louisiana, California (active age verification laws)
- Federal legislation (e.g., TAKE IT DOWN Act, potential federal age verification law)
- International jurisdictions (EU, UK, Australia) if expanding globally

**Quarterly Review:** Every 90 days, review:
1. Enforcement actions against platforms using self-declaration
2. New state or federal age verification laws
3. Updates to WhatsApp Business API policies (adult content)

### 5.2 Trigger for Upgrade

If monitoring reveals:
- Enforcement actions against platforms using self-declaration alone
- State law clarification that self-declaration is insufficient
- Legal counsel recommendation to upgrade verification methods

Then: Activate pluggable architecture upgrade path (see section 3.6).

## 6. Data Retention and Privacy

**Minimal Data Storage:** As outlined in section 2.2, the platform stores only:
- `user_id`, `verified: true`, `method: 'self-declaration'`

**No PII Storage:** No timestamps, IP addresses, device fingerprints, or uploaded documents are retained after verification.

**Third-Party Verification (Future):** If ID verification is implemented, third-party providers (Onfido, Veriff, etc.) handle PII. The platform receives only a verification result token, not the ID document itself.

**Audit Logs:** Verification events are logged in `audit_log` for compliance, but logs contain minimal data (user_id and verification method only).

**Account Deletion:** Upon account deletion, audit logs are anonymized (user_id replaced with anonymized token). Verification records cannot be linked back to the deleted user.

## 7. Summary

**Current State (Phase 1):**
- Self-declaration checkbox at signup
- One-time verification, no re-verification
- Data minimization (no timestamps, IP addresses, or metadata)
- 20+ avatar age floor enforced separately

**Future Adaptability:**
- Pluggable `AgeVerificationProvider` architecture
- Swapping providers is a configuration change, not a code rewrite
- Upgrade path ready for ID verification or biometric methods when regulations require

**Key Technical Reference:**
- See `compliance/architecture-decisions/adr-001-age-verification.md` for full technical design

---

**DRAFT NOTICE:** This document requires review and refinement by an attorney specializing in age verification regulations and adult content platforms before implementation.

**Last Updated:** 2026-02-23

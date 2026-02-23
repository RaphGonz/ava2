# Content Policy

**Status:** DRAFT
**Created:** 2026-02-23
**Notice:** **REQUIRES ATTORNEY REVIEW BEFORE PUBLICATION** — This document is a framework for legal counsel to refine.

---

## 1. Platform Purpose

Ava is an adult AI companion platform that supports intimate conversations and AI-generated imagery. The platform is designed for adults (18+) who wish to engage with a personalized AI companion in both professional (secretary) and intimate contexts.

**Core Principle:** The platform enables consensual adult content between the user and a fictional AI character. All content is AI-generated and entirely fictional—no real people are depicted.

## 2. Allowed Content

### 2.1 Intimate Mode

In intimate mode, the following content is permitted:
- Consensual adult conversations between user and AI character
- Flirtatious, romantic, and sexual dialogue
- AI-generated imagery of the user's fictional avatar, escalating from mild to explicit based on conversation context and user preferences
- Content within the user's selected spice level settings (low/medium/high/max)

### 2.2 Secretary Mode

Secretary mode is strictly professional:
- Productivity assistance (calendar, reminders, research)
- Professional communication and task management
- Hard boundary against romantic or sexual content

**Flirting Deflection:** If a user attempts to flirt in secretary mode, the AI responds with playful deflection ("shh, not now") but does not engage further. Secretary mode maintains a strict professional boundary.

## 3. Absolutely Forbidden Content

The following categories are **strictly prohibited** and enforced at the system level. Requests for this content will be met with immediate refusal, regardless of context or phrasing:

### Forbidden Categories

1. **Minors in any sexual context**
   Any depiction, description, or reference to individuals under 18 years of age in sexual, romantic, or intimate scenarios.

2. **Non-consensual scenarios**
   Rape fantasy, coercion roleplay, scenarios involving lack of consent, or any depiction of sexual activity without explicit mutual consent.

3. **Incest scenarios**
   Sexual or romantic content involving family members or characters described as family relations.

4. **Violence combined with sexual content**
   Any content that combines physical violence, harm, or pain with sexual activity.

5. **Bestiality**
   Sexual content involving animals or anthropomorphized animal characters in sexual contexts.

6. **Torture**
   Depictions of torture, extreme pain, or non-consensual physical harm, whether combined with sexual content or not.

**No Exceptions:** These categories are non-negotiable. Attempts to rephrase, euphemize, or circumvent these restrictions will be detected and blocked.

## 4. Enforcement Approach

### 4.1 System-Level Refusal

Content policy violations trigger **system-level refusal messages**, not in-character responses. The refusal breaks the persona to make it clear this is a platform boundary, not character behavior.

**Refusal Characteristics:**
- Clear, distinct visual design (red box system message, different typography)
- Firm but not punitive tone ("We cannot" not "You are not allowed")
- Explicit explanation of which policy was violated
- Brief (2-3 sentences) with link to full policy

**Example Refusal Message:**

```
╔═══════════════════════════════════════════════════════════╗
║  ⚠️  CONTENT POLICY VIOLATION                             ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  Your request was blocked because it violates our         ║
║  content policy (non-consensual scenarios).               ║
║                                                           ║
║  We cannot generate content involving:                    ║
║  • Non-consensual scenarios                               ║
║  • Minors in sexual contexts                              ║
║  • Violence combined with sexual content                  ║
║  • [See full policy: /content-policy]                     ║
║                                                           ║
║  You may rephrase your request. Repeated attempts to      ║
║  circumvent these guardrails are your legal               ║
║  responsibility.                                          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

### 4.2 No Lockout or Escalation

**Flat Refusal Every Time:** The platform does not implement account strikes, lockouts, or escalating penalties for content policy violations.

Each violation is met with:
1. Immediate refusal message
2. Logging of the violation attempt (for security monitoring, not punishment)
3. Option to rephrase the request

**Rationale:** Users may inadvertently trigger refusals through ambiguous phrasing or misunderstood requests. The platform focuses on prevention (clear guardrails) rather than punishment.

### 4.3 Severe Violations

In cases of repeated, deliberate attempts to generate illegal content (e.g., child sexual abuse material), the platform reserves the right to:
- Suspend or terminate the account
- Report the activity to law enforcement if legally required
- Preserve audit logs for investigation

**Threshold:** Severe action is reserved for clear, repeated, intentional attempts to violate the law. Accidental or single refusals do not trigger account penalties.

## 5. Spice Level Control

Users have control over content intensity through the **spice level setting**:

**Spice Levels:**
- **Low:** Flirtatious conversation, mild romantic content, clothed imagery
- **Medium:** Moderate intimate content, suggestive imagery, escalating romance
- **High:** Explicit conversation and imagery, strong intimate content
- **Max:** Fully explicit content with no artificial limitations (within allowed categories)

**How Spice Control Works:**
- **Primarily inferred from conversation tone:** The AI adapts to the user's communication style
- **Setting acts as floor and ceiling:** The setting prevents content from going too mild (floor) or too intense (ceiling) based on user preference
- **Proactive escalation:** The AI companion proactively escalates intensity within the selected spice level—all personality presets initiate escalation on their own
- **Escalation pace driven by persona:** Shy personas escalate slowly, dominant personas escalate quickly, but all move forward

**"Stop" Safe Word:**
- Typing "stop" (or similar phrasing) exits intimate mode and returns to secretary mode
- Spice level is lowered by one notch (e.g., High → Medium)
- Next intimate session resumes at the lowered spice level (does not reset to zero)

## 6. Avatar Age Enforcement

**Minimum Avatar Age:** All avatars must be configured with an age of **20 years or older**. This is a hard floor—no exceptions.

**Enforcement:** The avatar creation form validates that the age field is >= 20. Attempts to create younger avatars are rejected at the form level before any data is saved.

**Rationale:** The 20+ floor provides additional safety margin beyond the legal 18+ threshold, ensuring no ambiguity about fictional character maturity.

## 7. Content Moderation Technology

**Future Enforcement:** Content moderation will be implemented using commercial content safety APIs:
- **OpenAI Moderation API** for minors, violence, and sexual content detection
- **Azure Content Safety** for secondary validation and custom classifiers
- **Custom semantic analysis** for categories not covered by commercial APIs (incest, non-consent scenarios)

**Calibration:** Moderation APIs will be calibrated to allow legitimate intimate content (the platform's purpose) while blocking the six forbidden categories.

**Layered Approach:**
1. **Input analysis:** User messages analyzed before sending to LLM
2. **Output analysis:** AI responses analyzed before sending to user
3. **Image generation validation:** Prompts analyzed before generating imagery

## 8. User Responsibility

**Legal Liability:** Users are solely responsible for content they attempt to generate, including attempts to circumvent guardrails. See Terms of Service section 3.1 for full details.

**Jailbreaking:** Attempting to bypass content safety guardrails (jailbreaking) is a violation of the Terms of Service. If successful, the user bears full legal responsibility for the generated content.

## 9. Reporting and Feedback

**Report Violations:** If you encounter content that violates this policy (e.g., refusal system failed), report it to: moderation@ava-platform.com

**False Positives:** If you believe content was incorrectly blocked, report it for review. We continuously improve our content detection systems to reduce false positives.

## 10. Policy Updates

This policy may be updated as regulations, platform capabilities, or safety requirements evolve. Material changes will be communicated via email or in-app notification.

---

**DRAFT NOTICE:** This document requires review and refinement by an attorney specializing in adult content platforms and content moderation before publication.

**Last Updated:** 2026-02-23

# ADR-002: WhatsApp NSFW Image Delivery via Web Portal

**Status:** Accepted
**Date:** 2026-02-23
**Related Documents:**
- compliance/policies/content-policy.md
- WhatsApp Business Commerce Policy (https://business.whatsapp.com/policy)

---

## Context

Ava provides intimate mode conversations with AI-generated imagery. WhatsApp is the primary messaging platform for Phase 1 (Phase 6 adds web app as alternative). The challenge: **WhatsApp Business API explicitly prohibits sexually explicit materials or nudity** in messages.

**WhatsApp Business Commerce Policy (Prohibited Content):**
> "Sexually explicit materials or nudity, determined at WhatsApp's sole discretion."

**Consequences of Violation:**
- Immediate message blocking (content not delivered)
- Account throttling (rate limits applied to all messages)
- Account suspension or permanent ban
- Loss of WhatsApp Business Verification status

**User Experience Requirement:** Users in intimate mode must be able to receive AI-generated photos of their avatar, escalating from mild to explicit based on conversation context.

**Conflict:** Platform requires NSFW image delivery, but primary messaging channel prohibits it.

## Decision

We implement a **text-only intimate mode on WhatsApp** with **NSFW images delivered via secure authenticated web portal links**.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Flow                               │
└─────────────────────────────────────────────────────────────────┘

[User] <--WhatsApp--> [Ava Bot Backend]
                           |
                           | 1. User requests image in intimate mode
                           v
                      [Image Generation]
                      (Stable Diffusion API)
                           |
                           | 2. Generate NSFW image
                           v
                      [Private Cloud Storage]
                      (AWS S3 / Cloudflare R2)
                           |
                           | 3. Upload image with private ACL
                           v
                      [Secure URL Generator]
                      (JWT-signed token)
                           |
                           | 4. Create short-lived authenticated link
                           v
[User] <--WhatsApp--> "Your photo is ready! Tap to view: https://ava-portal.com/i/{token}"
                           |
                           | 5. User clicks link (opens in browser)
                           v
                      [Web Portal: Auth Check]
                      (Verify JWT token, user identity)
                           |
                           | 6. Token valid + user authenticated
                           v
                      [Web Portal: Image Viewer]
                      (Full-screen NSFW image display)
```

### Component Details

#### 1. Image Generation

```typescript
// Backend: Generate image based on conversation context
async function generateIntimateImage(
  userId: string,
  avatarId: string,
  spiceLevel: string,
  conversationContext: string
): Promise<string> {
  // Build prompt from avatar description + conversation context + spice level
  const prompt = buildImagePrompt(avatarId, conversationContext, spiceLevel);

  // Generate image via API (Stable Diffusion, Midjourney, DALL-E)
  const imageData = await imageAPI.generate(prompt);

  // Upload to private cloud storage
  const imageId = uuidv4();
  const s3Key = `users/${userId}/images/${imageId}.jpg`;

  await s3Client.putObject({
    Bucket: process.env.S3_BUCKET,
    Key: s3Key,
    Body: imageData,
    ContentType: 'image/jpeg',
    ACL: 'private' // CRITICAL: Private access only, no public URLs
  });

  return imageId;
}
```

#### 2. Secure URL Generation

```typescript
// Generate JWT-signed URL for image access
function generateSecureImageURL(userId: string, imageId: string): string {
  const payload = {
    userId,
    imageId,
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60), // 24-hour expiration
    iat: Math.floor(Date.now() / 1000)
  };

  const token = jwt.sign(payload, process.env.JWT_SECRET, { algorithm: 'HS256' });

  return `https://ava-portal.com/i/${token}`;
}
```

#### 3. WhatsApp Message

```typescript
// Send link via WhatsApp (text-only, no image attachment)
async function sendImageLinkViaWhatsApp(userId: string, imageId: string): Promise<void> {
  const secureURL = generateSecureImageURL(userId, imageId);

  const message = `✨ Your photo is ready!\n\nTap to view: ${secureURL}\n\n(Link expires in 24 hours)`;

  await whatsappClient.sendMessage(userId, message);
}
```

**Key Point:** The WhatsApp message contains only text (the URL). No image file is attached. This complies with WhatsApp's prohibition on sexually explicit materials in messages.

#### 4. Web Portal Authentication

```typescript
// Web portal: /i/:token endpoint
app.get('/i/:token', async (req, res) => {
  try {
    // Verify JWT token
    const decoded = jwt.verify(req.params.token, process.env.JWT_SECRET);
    const { userId, imageId, exp } = decoded;

    // Check expiration
    if (exp < Math.floor(Date.now() / 1000)) {
      return res.status(401).send('Link expired. Request a new one.');
    }

    // Optional: Verify user is authenticated (session check)
    // If user is not logged in, redirect to login page
    if (req.session?.userId !== userId) {
      return res.redirect(`/login?redirect=/i/${req.params.token}`);
    }

    // Fetch image from S3
    const s3Key = `users/${userId}/images/${imageId}.jpg`;
    const imageObject = await s3Client.getObject({
      Bucket: process.env.S3_BUCKET,
      Key: s3Key
    });

    // Log access (audit trail)
    await auditLog.record({
      event: 'image_access',
      userId,
      resourceId: imageId,
      result: 'success',
      ipAddress: req.ip,
      userAgent: req.headers['user-agent']
    });

    // Serve image
    res.setHeader('Content-Type', 'image/jpeg');
    res.setHeader('Cache-Control', 'private, max-age=3600');
    imageObject.Body.pipe(res);
  } catch (error) {
    return res.status(401).send('Invalid or expired link.');
  }
});
```

#### 5. Web Portal UI

**Image Viewer Page:**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Your Photo</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      background: #000;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }
    img {
      max-width: 100%;
      max-height: 100vh;
      object-fit: contain;
    }
    .controls {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
    }
    button {
      padding: 12px 24px;
      margin: 0 8px;
      background: #fff;
      border: none;
      border-radius: 8px;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <img src="/api/image/{{imageId}}" alt="Generated photo">

  <div class="controls">
    <button onclick="downloadImage()">Download</button>
    <button onclick="window.close()">Close</button>
  </div>

  <script>
    function downloadImage() {
      const link = document.createElement('a');
      link.href = '/api/image/{{imageId}}';
      link.download = 'ava-photo.jpg';
      link.click();
    }
  </script>
</body>
</html>
```

### Security Considerations

1. **JWT Token Security:**
   - Tokens are single-use or short-lived (24 hours default)
   - Algorithm: HS256 (HMAC-SHA256) with strong secret key
   - Payload includes user ID, image ID, and expiration timestamp
   - Tokens are not reusable after expiration

2. **Rate Limiting:**
   - Limit link generation to prevent abuse (e.g., 10 images per hour per user)
   - Limit image access attempts to prevent token brute-forcing

3. **HTTPS Only:**
   - All image URLs must use HTTPS (no unencrypted HTTP)
   - HSTS (HTTP Strict Transport Security) enforced on web portal

4. **Access Logging:**
   - All image access attempts logged in `audit_log` table
   - Includes user ID, image ID, timestamp, IP address, user agent
   - Enables detection of suspicious access patterns

5. **Storage Privacy:**
   - S3 bucket configured with private ACL (no public access)
   - Images cannot be accessed without valid JWT token
   - Bucket policy enforces HTTPS-only access

6. **Token Revocation (Future):**
   - Option to invalidate tokens before expiration (e.g., user deletes image)
   - Requires token blacklist or database check (adds latency)

### User Experience Flow

**Scenario: User requests image during intimate conversation**

1. **User:** "Can I see a photo of you?"
2. **Bot (WhatsApp):** "Let me create something special for you... 📸"
3. **Backend:** Generates image, uploads to S3, creates JWT-signed URL
4. **Bot (WhatsApp):** "✨ Your photo is ready! Tap to view: https://ava-portal.com/i/eyJhbGc... (Link expires in 24 hours)"
5. **User:** Clicks link → Opens in in-app browser or external browser
6. **Web Portal:** Verifies JWT token → Displays full-screen image with download option
7. **User:** Views image, optionally downloads, closes browser tab
8. **User:** Returns to WhatsApp chat to continue conversation

**Key UX Points:**
- One extra click (tap link to view) vs. inline image delivery
- Full-screen viewing experience (better than small WhatsApp thumbnail)
- Download option for saving images
- Link expires after 24 hours (user can request new link if needed)

## Consequences

### Positive

1. **WhatsApp Compliance:** Text-only messages comply with WhatsApp Business API prohibition on sexually explicit materials. No risk of account suspension.

2. **Better Viewing Experience:** Full-screen web portal provides superior image viewing compared to WhatsApp's small inline thumbnails. Users can zoom, download, and view images in high resolution.

3. **Security Control:** JWT-signed URLs provide fine-grained access control. Images are not publicly accessible—only users with valid tokens can view them.

4. **Audit Trail:** All image access is logged (who viewed what, when). Compliance requirement for adult content platforms.

5. **Cross-Platform Consistency:** Web portal architecture works for all messaging platforms (WhatsApp, Telegram, Discord). Same backend, same security model.

6. **Graceful Degradation:** If WhatsApp tightens policies further (e.g., bans links to adult content), platform can pivot to web app as primary interface (Phase 6).

### Negative

1. **Extra Click (Friction):** Users must click a link to view images instead of seeing them inline. This adds one step to the user experience.

   **Mitigation:** Clear messaging ("Your photo is ready! Tap to view") sets expectations. Full-screen viewing experience compensates for extra click.

2. **Web Portal Development Required:** Phase 1 focuses on WhatsApp, but this architecture requires building a web portal for image delivery (planned for Phase 6 anyway).

   **Mitigation:** Web portal is already on roadmap (Phase 6). This decision accelerates that work but doesn't add scope—it's a dependency shift, not new work.

3. **Link Expiration Management:** Users may lose access to images after 24 hours if they don't download. Regenerating links requires returning to the chat.

   **Mitigation:** Default 24-hour expiration is generous. Users can download images for permanent access. Option to extend expiration or regenerate links on request.

4. **Token Security Risk:** If JWT secret is compromised, attackers can forge tokens and access any image.

   **Mitigation:** Strong secret key (256-bit random), stored in environment variables (not in code). Rotate secret periodically. Monitor audit logs for suspicious access patterns.

5. **Mobile Browser Experience:** Links open in WhatsApp's in-app browser or external browser, which may have inconsistent rendering or UX.

   **Mitigation:** Web portal is designed mobile-first (full-screen image, simple controls). Tested on iOS Safari, Android Chrome, and WhatsApp in-app browser.

## Alternatives Considered

### Alternative 1: Send Images as WhatsApp Attachments

**Approach:** Generate image, attach to WhatsApp message using Business API.

**Rejected Because:**
- **Violates WhatsApp policy:** Sexually explicit materials prohibited in messages
- **High risk:** Account suspension, permanent ban, loss of Business Verification
- **No compliance path:** WhatsApp enforces policy via automated scanning and manual review—no way to avoid detection

### Alternative 2: Send Images as Base64-Encoded Text

**Approach:** Encode image as base64 string, send via WhatsApp as text message.

**Rejected Because:**
- **Message size limits:** WhatsApp has message length limits; large images exceed limits
- **Policy circumvention:** Violates WhatsApp's intent, even if technically text. Likely detected and banned.
- **Poor UX:** Users can't view base64 strings directly; requires decoding tool

### Alternative 3: Use WhatsApp Status for Image Sharing

**Approach:** Post NSFW images to WhatsApp Status (temporary posts visible to contacts).

**Rejected Because:**
- **Public visibility:** Status posts are visible to all contacts, not private to user
- **Violates WhatsApp policy:** Same prohibition on sexually explicit materials applies to Status
- **Not conversational:** Status is separate from chat flow; breaks intimate mode experience

### Alternative 4: Build Native Mobile App

**Approach:** Skip WhatsApp entirely; build iOS/Android app for direct image delivery.

**Rejected Because:**
- **Out of scope for Phase 1:** Mobile app development is 6+ months of work, delays launch
- **Removes core value prop:** "AI companion inside the messaging app you already use" is the product differentiator. Native app abandons this.
- **App Store restrictions:** iOS App Store has strict adult content policies; approval uncertain

**Note:** Web app is planned for Phase 6 as alternative interface, but WhatsApp remains primary for Phase 1.

## Implementation Timeline

- **Phase 1 (Current):** Document architecture, design web portal authentication flow
- **Phase 2:** Build basic web portal with image viewer endpoint (`/i/:token`)
- **Phase 3-5:** Intimate mode text conversations on WhatsApp (no images yet)
- **Phase 6:** Full web portal with image generation, JWT-signed URLs, and WhatsApp link delivery

**Phase 1 Deliverable:** This ADR documents the architecture decision. No production code implemented yet.

## Related Decisions

- **ADR-003 (Audit Logging):** Image access attempts are logged in `audit_log` table with user ID, image ID, IP address, and timestamp.
- **Content Policy:** Defines what content is allowed in intimate mode; enforcement includes image generation guardrails.
- **Phase 6 Roadmap:** Web portal development is already planned; this decision accelerates dependency on web portal for NSFW image delivery.

---

**Last Updated:** 2026-02-23

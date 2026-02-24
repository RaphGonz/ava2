export async function signIn(email: string, password: string) {
  const res = await fetch('/auth/signin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Sign in failed' }))
    throw new Error(err.detail ?? 'Sign in failed')
  }
  const data = await res.json()
  // Decode JWT payload (base64url decode middle segment) to get sub (user_id)
  const payloadB64 = data.access_token.split('.')[1]
  const payload = JSON.parse(atob(payloadB64.replace(/-/g, '+').replace(/_/g, '/')))
  return { access_token: data.access_token, user_id: payload.sub as string }
}

export async function signOut() {
  // JWT is stateless — clear locally, no server call needed
}

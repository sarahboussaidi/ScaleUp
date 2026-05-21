export const AUTH_COOKIE_NAME = "scaleup_session"

const DEFAULT_SESSION_SECRET = "scaleup-dev-secret-change-me"
const SESSION_SECRET =
  process.env.SCALEUP_SESSION_SECRET ||
  process.env.NEXT_PUBLIC_SCALEUP_SESSION_SECRET ||
  DEFAULT_SESSION_SECRET

export type SessionPayload = {
  sub: string
  email: string
  firstName: string
  lastName: string
  plan: "free" | "pro"
  iat: number
  exp: number
}

function encodeBytesBase64Url(bytes: Uint8Array) {
  if (typeof btoa === "function") {
    let binary = ""
    bytes.forEach((byte) => {
      binary += String.fromCharCode(byte)
    })
    return btoa(binary).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_")
  }

  return Buffer.from(bytes).toString("base64url")
}

function decodeBase64UrlToBytes(value: string) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/")
  const padding = "=".repeat((4 - (normalized.length % 4)) % 4)
  const base64 = normalized + padding

  let binary: string

  if (typeof atob === "function") {
    binary = atob(base64)
  } else {
    binary = Buffer.from(base64, "base64").toString("binary")
  }

  return Uint8Array.from(binary, (character) => character.charCodeAt(0))
}

function decodeBase64Url(value: string) {
  return new TextDecoder().decode(decodeBase64UrlToBytes(value))
}

function toUtf8Bytes(value: string) {
  return new TextEncoder().encode(value)
}

async function importHmacKey() {
  return crypto.subtle.importKey(
    "raw",
    toUtf8Bytes(SESSION_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"],
  )
}

async function signData(value: string) {
  const key = await importHmacKey()
  const signature = await crypto.subtle.sign("HMAC", key, toUtf8Bytes(value))
  return encodeBytesBase64Url(new Uint8Array(signature))
}

export async function createSessionToken(payload: SessionPayload) {
  const encodedPayload = encodeBytesBase64Url(toUtf8Bytes(JSON.stringify(payload)))
  const signature = await signData(encodedPayload)
  return `${encodedPayload}.${signature}`
}

export async function verifySessionToken(token: string): Promise<SessionPayload | null> {
  const [encodedPayload, encodedSignature] = token.split(".")

  if (!encodedPayload || !encodedSignature) {
    return null
  }

  const expectedSignature = await signData(encodedPayload)
  if (expectedSignature !== encodedSignature) {
    return null
  }

  try {
    const payload = JSON.parse(decodeBase64Url(encodedPayload)) as SessionPayload

    if (!payload?.sub || !payload?.email || !payload?.exp) {
      return null
    }

    if (Date.now() > payload.exp) {
      return null
    }

    return payload
  } catch {
    return null
  }
}

export function readCookieValue(cookieHeader: string | null | undefined, name: string) {
  if (!cookieHeader) return null

  const cookies = cookieHeader.split(";").map((part) => part.trim())
  const match = cookies.find((cookie) => cookie.startsWith(`${name}=`))

  if (!match) return null

  return decodeURIComponent(match.slice(name.length + 1))
}

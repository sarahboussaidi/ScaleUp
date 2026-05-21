import { AUTH_COOKIE_NAME } from "@/lib/session"

export function getBrowserSessionToken() {
  if (typeof document === "undefined") {
    return null
  }

  const cookies = document.cookie.split("; ")
  const match = cookies.find((cookie) => cookie.startsWith(`${AUTH_COOKIE_NAME}=`))

  if (!match) {
    return null
  }

  return decodeURIComponent(match.slice(AUTH_COOKIE_NAME.length + 1))
}

export async function fetchCurrentUser() {
  const response = await fetch("/api/auth/me", {
    credentials: "include",
  })

  if (!response.ok) {
    return null
  }

  return response.json()
}

export async function logoutCurrentUser() {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
  })
}

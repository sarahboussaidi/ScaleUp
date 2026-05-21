import { randomUUID, pbkdf2Sync } from "crypto"
import { promises as fs } from "fs"
import path from "path"

export type StoredUser = {
  id: string
  firstName: string
  lastName: string
  dateOfBirth: string
  address: string
  phone: string
  email: string
  organizationName?: string
  passwordSalt: string
  passwordHash: string
  plan: "free" | "pro"
  createdAt: string
}

export type PublicUser = Omit<StoredUser, "passwordSalt" | "passwordHash">

const DATA_DIR = path.join(process.cwd(), "data")
const USERS_FILE = path.join(DATA_DIR, "auth-users.json")

async function ensureStorage() {
  await fs.mkdir(DATA_DIR, { recursive: true })
}

async function readUsers(): Promise<StoredUser[]> {
  try {
    const raw = await fs.readFile(USERS_FILE, "utf8")
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? (parsed as StoredUser[]) : []
  } catch {
    return []
  }
}

async function writeUsers(users: StoredUser[]) {
  await ensureStorage()
  await fs.writeFile(USERS_FILE, JSON.stringify(users, null, 2), "utf8")
}

export function hashPassword(password: string, salt = randomUUID().replace(/-/g, "")) {
  const hash = pbkdf2Sync(password, salt, 120000, 64, "sha512").toString("hex")
  return { salt, hash }
}

export function verifyPassword(password: string, salt: string, expectedHash: string) {
  const { hash } = hashPassword(password, salt)
  return hash === expectedHash
}

export function toPublicUser(user: StoredUser): PublicUser {
  const { passwordSalt: _passwordSalt, passwordHash: _passwordHash, ...publicUser } = user
  return publicUser
}

export async function findUserByEmail(email: string) {
  const users = await readUsers()
  return users.find((user) => user.email.toLowerCase() === email.toLowerCase()) || null
}

export async function createUser(input: Omit<StoredUser, "id" | "passwordSalt" | "passwordHash" | "createdAt"> & { password: string }) {
  const users = await readUsers()
  const existing = users.find((user) => user.email.toLowerCase() === input.email.toLowerCase())

  if (existing) {
    throw new Error("An account with this email already exists.")
  }

  const { salt, hash } = hashPassword(input.password)
  const user: StoredUser = {
    id: randomUUID(),
    firstName: input.firstName.trim(),
    lastName: input.lastName.trim(),
    dateOfBirth: input.dateOfBirth,
    address: input.address.trim(),
    phone: input.phone.trim(),
    email: input.email.trim().toLowerCase(),
    organizationName: input.organizationName?.trim() || undefined,
    passwordSalt: salt,
    passwordHash: hash,
    plan: input.plan,
    createdAt: new Date().toISOString(),
  }

  users.push(user)
  await writeUsers(users)

  return user
}

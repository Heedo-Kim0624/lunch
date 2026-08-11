import type {
  AccountUser,
  AuthResponse,
  LoginPayload,
  RegistrationPayload,
} from '../types/auth'

const TOKEN_STORAGE_KEY = 'lunch-machine-auth-token'

function firstApiMessage(value: unknown): string | null {
  if (typeof value === 'string') {
    return value
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstApiMessage(item)
      if (message) return message
    }
  }
  if (value && typeof value === 'object') {
    for (const item of Object.values(value)) {
      const message = firstApiMessage(item)
      if (message) return message
    }
  }
  return null
}

export function authErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'data' in error) {
    const message = firstApiMessage(error.data)
    if (message) return message
  }
  return '서버와 연결하지 못했어요. 잠시 후 다시 시도해 주세요.'
}

export function useAuth() {
  const config = useRuntimeConfig()
  const token = useState<string | null>('auth-token', () => null)
  const user = useState<AccountUser | null>('auth-user', () => null)
  const initialized = useState('auth-initialized', () => false)

  function authorizationHeaders(): Record<string, string> {
    return token.value ? { Authorization: `Token ${token.value}` } : {}
  }

  function saveSession(response: AuthResponse): void {
    token.value = response.token
    user.value = response.user
    if (import.meta.client) {
      localStorage.setItem(TOKEN_STORAGE_KEY, response.token)
    }
  }

  function clearSession(): void {
    token.value = null
    user.value = null
    if (import.meta.client) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
    }
  }

  async function initialize(): Promise<void> {
    if (initialized.value || import.meta.server) return
    initialized.value = true
    token.value = localStorage.getItem(TOKEN_STORAGE_KEY)
    if (!token.value) return

    try {
      const response = await $fetch<{ user: AccountUser }>(`${config.public.apiBase}/auth/me`, {
        headers: authorizationHeaders(),
      })
      user.value = response.user
    }
    catch {
      clearSession()
    }
  }

  async function register(payload: RegistrationPayload): Promise<void> {
    const response = await $fetch<AuthResponse>(`${config.public.apiBase}/auth/register`, {
      method: 'POST',
      body: {
        display_name: payload.displayName,
        email: payload.email,
        password: payload.password,
        password_confirm: payload.passwordConfirm,
      },
    })
    saveSession(response)
  }

  async function login(payload: LoginPayload): Promise<void> {
    const response = await $fetch<AuthResponse>(`${config.public.apiBase}/auth/login`, {
      method: 'POST',
      body: payload,
    })
    saveSession(response)
  }

  async function logout(): Promise<void> {
    try {
      if (token.value) {
        await $fetch(`${config.public.apiBase}/auth/logout`, {
          method: 'POST',
          headers: authorizationHeaders(),
        })
      }
    }
    finally {
      clearSession()
    }
  }

  return {
    token: readonly(token),
    user: readonly(user),
    initialized: readonly(initialized),
    authorizationHeaders,
    initialize,
    register,
    login,
    logout,
  }
}

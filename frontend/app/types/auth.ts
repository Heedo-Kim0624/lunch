export interface AccountUser {
  id: number
  email: string
  display_name: string
}

export interface AuthResponse {
  token: string
  user: AccountUser
}

export interface RegistrationPayload {
  displayName: string
  email: string
  password: string
  passwordConfirm: string
}

export interface LoginPayload {
  email: string
  password: string
}

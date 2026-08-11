export interface RegistrationForm {
  displayName: string
  email: string
  password: string
  passwordConfirm: string
  acceptedPrivacy: boolean
}

export type RegistrationErrors = Partial<Record<keyof RegistrationForm, string>>

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateRegistrationForm(form: RegistrationForm): RegistrationErrors {
  const errors: RegistrationErrors = {}

  if (!form.displayName.trim()) {
    errors.displayName = '표시할 이름을 입력해 주세요.'
  }
  if (!EMAIL_PATTERN.test(form.email.trim())) {
    errors.email = '올바른 이메일 주소를 입력해 주세요.'
  }
  if (form.password.length < 10) {
    errors.password = '비밀번호는 10자 이상이어야 합니다.'
  }
  if (form.password !== form.passwordConfirm) {
    errors.passwordConfirm = '비밀번호가 서로 일치하지 않습니다.'
  }
  if (!form.acceptedPrivacy) {
    errors.acceptedPrivacy = '개인정보 처리 안내에 동의해 주세요.'
  }

  return errors
}

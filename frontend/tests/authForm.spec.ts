import { describe, expect, it } from 'vitest'

import { validateRegistrationForm } from '../app/utils/authForm'

describe('validateRegistrationForm', () => {
  it('accepts a complete registration form', () => {
    expect(validateRegistrationForm({
      displayName: '점심러',
      email: 'lunch@example.com',
      password: 'Tasty-lunch-2026!',
      passwordConfirm: 'Tasty-lunch-2026!',
      acceptedPrivacy: true,
    })).toEqual({})
  })

  it('returns field-specific errors for invalid input', () => {
    expect(validateRegistrationForm({
      displayName: '',
      email: 'not-an-email',
      password: 'short',
      passwordConfirm: 'different',
      acceptedPrivacy: false,
    })).toEqual({
      displayName: '표시할 이름을 입력해 주세요.',
      email: '올바른 이메일 주소를 입력해 주세요.',
      password: '비밀번호는 10자 이상이어야 합니다.',
      passwordConfirm: '비밀번호가 서로 일치하지 않습니다.',
      acceptedPrivacy: '개인정보 처리 안내에 동의해 주세요.',
    })
  })
})

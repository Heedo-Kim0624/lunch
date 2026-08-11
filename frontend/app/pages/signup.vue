<script setup lang="ts">
import type { RegistrationErrors, RegistrationForm } from '../utils/authForm'
import { validateRegistrationForm } from '../utils/authForm'

useHead({ title: '회원가입 · 점심 결정 기계' })

const { register } = useAuth()
const form = reactive<RegistrationForm>({
  displayName: '',
  email: '',
  password: '',
  passwordConfirm: '',
  acceptedPrivacy: false,
})
const errors = ref<RegistrationErrors>({})
const formError = ref('')
const isSubmitting = ref(false)

async function submitRegistration() {
  formError.value = ''
  errors.value = validateRegistrationForm(form)
  if (Object.keys(errors.value).length > 0) return

  isSubmitting.value = true
  try {
    await register(form)
    await navigateTo('/')
  }
  catch (error) {
    formError.value = authErrorMessage(error)
  }
  finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card" aria-labelledby="signup-title">
      <div class="auth-ticket-tag" aria-hidden="true">NEW MEMBER · LM—01</div>
      <p class="auth-eyebrow">취향 기록을 어디서나 이어가세요</p>
      <h1 id="signup-title">회원가입</h1>
      <p class="auth-intro">레버를 당길수록 내 선택을 학습합니다. 이메일과 선택 기록만 저장해요.</p>

      <form class="auth-form" novalidate @submit.prevent="submitRegistration">
        <div class="form-field">
          <label for="display-name">표시할 이름</label>
          <input
            id="display-name"
            v-model="form.displayName"
            name="display-name"
            type="text"
            autocomplete="nickname"
            maxlength="50"
            :aria-invalid="Boolean(errors.displayName)"
            :aria-describedby="errors.displayName ? 'display-name-error' : undefined"
          >
          <p v-if="errors.displayName" id="display-name-error" class="field-error">{{ errors.displayName }}</p>
        </div>

        <div class="form-field">
          <label for="signup-email">이메일</label>
          <input
            id="signup-email"
            v-model="form.email"
            name="email"
            type="email"
            inputmode="email"
            autocomplete="email"
            :aria-invalid="Boolean(errors.email)"
            :aria-describedby="errors.email ? 'signup-email-error' : undefined"
          >
          <p v-if="errors.email" id="signup-email-error" class="field-error">{{ errors.email }}</p>
        </div>

        <div class="form-field">
          <label for="signup-password">비밀번호</label>
          <input
            id="signup-password"
            v-model="form.password"
            name="password"
            type="password"
            autocomplete="new-password"
            :aria-invalid="Boolean(errors.password)"
            aria-describedby="password-hint signup-password-error"
          >
          <p id="password-hint" class="field-hint">10자 이상, 흔하지 않은 비밀번호를 사용해 주세요.</p>
          <p v-if="errors.password" id="signup-password-error" class="field-error">{{ errors.password }}</p>
        </div>

        <div class="form-field">
          <label for="password-confirm">비밀번호 확인</label>
          <input
            id="password-confirm"
            v-model="form.passwordConfirm"
            name="password-confirm"
            type="password"
            autocomplete="new-password"
            :aria-invalid="Boolean(errors.passwordConfirm)"
            :aria-describedby="errors.passwordConfirm ? 'password-confirm-error' : undefined"
          >
          <p v-if="errors.passwordConfirm" id="password-confirm-error" class="field-error">{{ errors.passwordConfirm }}</p>
        </div>

        <div class="form-field checkbox-field">
          <input
            id="privacy-consent"
            v-model="form.acceptedPrivacy"
            name="privacy-consent"
            type="checkbox"
            :aria-invalid="Boolean(errors.acceptedPrivacy)"
            :aria-describedby="errors.acceptedPrivacy ? 'privacy-error' : undefined"
          >
          <label for="privacy-consent">
            <NuxtLink to="/privacy" target="_blank">개인정보 처리 안내</NuxtLink>를 확인했고 동의합니다.
          </label>
          <p v-if="errors.acceptedPrivacy" id="privacy-error" class="field-error">{{ errors.acceptedPrivacy }}</p>
        </div>

        <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>

        <button class="auth-submit" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '계정을 만드는 중…' : '계정 만들고 시작하기' }}
        </button>
      </form>

      <p class="auth-switch">이미 계정이 있나요? <NuxtLink to="/login">로그인</NuxtLink></p>
    </section>
  </main>
</template>

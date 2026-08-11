<script setup lang="ts">
useHead({ title: '로그인 · 점심 결정 기계' })

const { login } = useAuth()
const form = reactive({ email: '', password: '' })
const errors = reactive({ email: '', password: '' })
const formError = ref('')
const isSubmitting = ref(false)

async function submitLogin() {
  errors.email = form.email.includes('@') ? '' : '올바른 이메일 주소를 입력해 주세요.'
  errors.password = form.password ? '' : '비밀번호를 입력해 주세요.'
  formError.value = ''
  if (errors.email || errors.password) return

  isSubmitting.value = true
  try {
    await login(form)
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
    <section class="auth-card auth-card-compact" aria-labelledby="login-title">
      <div class="auth-ticket-tag" aria-hidden="true">RETURNING MEMBER · LM—01</div>
      <p class="auth-eyebrow">내 취향 기록을 다시 불러옵니다</p>
      <h1 id="login-title">로그인</h1>

      <form class="auth-form" novalidate @submit.prevent="submitLogin">
        <div class="form-field">
          <label for="login-email">이메일</label>
          <input
            id="login-email"
            v-model="form.email"
            name="email"
            type="email"
            inputmode="email"
            autocomplete="email"
            :aria-invalid="Boolean(errors.email)"
            :aria-describedby="errors.email ? 'login-email-error' : undefined"
          >
          <p v-if="errors.email" id="login-email-error" class="field-error">{{ errors.email }}</p>
        </div>

        <div class="form-field">
          <label for="login-password">비밀번호</label>
          <input
            id="login-password"
            v-model="form.password"
            name="password"
            type="password"
            autocomplete="current-password"
            :aria-invalid="Boolean(errors.password)"
            :aria-describedby="errors.password ? 'login-password-error' : undefined"
          >
          <p v-if="errors.password" id="login-password-error" class="field-error">{{ errors.password }}</p>
        </div>

        <p v-if="formError" class="form-error" role="alert">{{ formError }}</p>

        <button class="auth-submit" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? '로그인 중…' : '로그인하고 레버 당기기' }}
        </button>
      </form>

      <p class="auth-switch">처음 오셨나요? <NuxtLink to="/signup">무료로 회원가입</NuxtLink></p>
    </section>
  </main>
</template>

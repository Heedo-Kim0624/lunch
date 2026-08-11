<script setup lang="ts">
const { user, logout } = useAuth()
const isLoggingOut = ref(false)

async function handleLogout() {
  isLoggingOut.value = true
  try {
    await logout()
    await navigateTo('/')
  }
  finally {
    isLoggingOut.value = false
  }
}
</script>

<template>
  <nav class="site-nav" aria-label="주요 메뉴">
    <NuxtLink class="site-brand" to="/">
      <span aria-hidden="true">LM—01</span>
      점심 결정 기계
    </NuxtLink>
    <div class="site-nav-actions">
      <template v-if="user">
        <span class="account-name">{{ user.display_name }} 님</span>
        <button type="button" class="nav-button" :disabled="isLoggingOut" @click="handleLogout">
          {{ isLoggingOut ? '처리 중' : '로그아웃' }}
        </button>
      </template>
      <template v-else>
        <NuxtLink class="nav-link" to="/login">로그인</NuxtLink>
        <NuxtLink class="nav-button nav-button-primary" to="/signup">회원가입</NuxtLink>
      </template>
    </div>
  </nav>
</template>

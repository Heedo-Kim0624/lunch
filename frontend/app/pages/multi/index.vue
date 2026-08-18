<script setup lang="ts">
import type { MultiRoomJoinEnvelope } from '../../types/multiRoom'
import { multiApiUrl, roomTokenStorageKey } from '../../utils/multiRoom'

const config = useRuntimeConfig()
const nickname = ref('')
const isCreating = ref(false)
const error = ref('')

useHead({ title: '멀티 점심방 만들기 · 점심 결정 기계' })

async function createRoom(): Promise<void> {
  if (nickname.value.trim().length < 2 || isCreating.value) {
    return
  }
  isCreating.value = true
  error.value = ''
  try {
    const response = await $fetch<MultiRoomJoinEnvelope>(
      multiApiUrl(config.public.apiBase, 'multi/rooms'),
      { method: 'POST', body: { nickname: nickname.value } },
    )
    localStorage.setItem(roomTokenStorageKey(response.room.code), response.participant_token)
    await navigateTo(`/multi/${response.room.code}`)
  }
  catch (caught) {
    const payload = typeof caught === 'object' && caught !== null && 'data' in caught
      ? (caught as { data?: { detail?: string } }).data
      : undefined
    error.value = payload?.detail || '공유방을 만들지 못했어요. 잠시 후 다시 시도해 주세요.'
  }
  finally {
    isCreating.value = false
  }
}
</script>

<template>
  <main class="multi-lobby-page">
    <section class="multi-lobby-card" aria-labelledby="multi-lobby-title">
      <p class="eyebrow">GROUP DECISION UNIT · LM—MULTI</p>
      <h1 id="multi-lobby-title">같이 고르는 점심</h1>
      <p class="multi-lobby-intro">
        공유 링크로 사람을 모으고 각자 먹고 싶은 메뉴를 적으세요.
        겹치는 메뉴 중 가장 많은 표를 받은 음식이 기계에서 나옵니다.
      </p>

      <form class="multi-create-form" @submit.prevent="createRoom">
        <label>
          <span>방에서 사용할 닉네임</span>
          <input
            v-model="nickname"
            type="text"
            minlength="2"
            maxlength="20"
            autocomplete="nickname"
            placeholder="예: 점심대장"
            required
          >
        </label>
        <button type="submit" :disabled="isCreating || nickname.trim().length < 2">
          {{ isCreating ? '방 만드는 중…' : '멀티방 만들기' }}
        </button>
      </form>
      <p v-if="error" class="multi-form-error" role="alert">{{ error }}</p>

      <ol class="multi-flow-list">
        <li><b>01</b><span>링크를 공유하고 닉네임으로 참가</span></li>
        <li><b>02</b><span>각자 원하는 음식 목록 작성 완료</span></li>
        <li><b>03</b><span>겹치는 최다 메뉴를 방장 레버로 결정</span></li>
      </ol>
    </section>
  </main>
</template>

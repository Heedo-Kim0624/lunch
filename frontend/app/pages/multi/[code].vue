<script setup lang="ts">
import type { MultiChoiceSubmission } from '../../types/multiRoom'
import { multiLeverLabel, multiRoomStatusMessage, multiShareUrl } from '../../utils/multiRoom'

const route = useRoute()
const rawCode = Array.isArray(route.params.code) ? route.params.code[0] : route.params.code
const code = String(rawCode || '').toUpperCase()
const {
  room,
  isLoading,
  isMutating,
  error,
  initialize,
  join,
  submitChoices,
  draw,
  startPolling,
  stopPolling,
} = useMultiRoom(code)

const joinNickname = ref('')
const choiceDialogOpen = ref(false)
const isPulling = ref(false)
const shareUrl = ref(`/multi/${code}`)
const copyStatus = ref('')

useHead({ title: `멀티 점심방 ${code} · 점심 결정 기계` })

const statusMessage = computed(() => room.value ? multiRoomStatusMessage(room.value) : '')
const isHost = computed(() => Boolean(room.value?.self?.is_host))
const canUseLever = computed(
  () => Boolean(room.value?.self?.is_host && room.value.can_draw && !isMutating.value),
)

async function handleJoin(): Promise<void> {
  if (joinNickname.value.trim().length < 2) {
    return
  }
  try {
    await join(joinNickname.value)
    choiceDialogOpen.value = true
  }
  catch {
    // The composable exposes the server-safe error copy.
  }
}

async function handleChoiceSubmit(choices: MultiChoiceSubmission[]): Promise<void> {
  try {
    await submitChoices(choices)
    choiceDialogOpen.value = false
  }
  catch {
    // Keep the dialog open so the participant can retry.
  }
}

async function handleDraw(): Promise<void> {
  if (!canUseLever.value) {
    return
  }
  isPulling.value = true
  try {
    await Promise.all([
      draw(),
      new Promise(resolve => setTimeout(resolve, 650)),
    ])
  }
  catch {
    // The shared error region announces the failure.
  }
  finally {
    isPulling.value = false
  }
}

async function copyShareLink(): Promise<void> {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copyStatus.value = '공유 링크를 복사했어요.'
  }
  catch {
    copyStatus.value = '복사하지 못했어요. 링크를 직접 선택해 주세요.'
  }
}

onMounted(async () => {
  shareUrl.value = multiShareUrl(window.location.origin, code)
  await initialize()
  if (room.value?.self && !room.value.self.is_ready && room.value.status === 'WAITING') {
    choiceDialogOpen.value = true
  }
  startPolling()
})

onBeforeUnmount(stopPolling)
</script>

<template>
  <main class="multi-room-page">
    <header class="multi-room-header">
      <div>
        <p class="eyebrow">SHARED LUNCH ROOM · {{ code }}</p>
        <h1>같이 돌리는 점심 기계</h1>
      </div>
      <div v-if="room" class="multi-share-box">
        <label for="multi-share-link">초대 링크</label>
        <div>
          <input id="multi-share-link" :value="shareUrl" readonly @focus="($event.target as HTMLInputElement).select()">
          <button type="button" @click="copyShareLink">링크 복사</button>
        </div>
        <p class="sr-only" aria-live="polite">{{ copyStatus }}</p>
      </div>
    </header>

    <section v-if="isLoading && !room" class="multi-state-card" aria-live="polite">
      공유방 기계를 불러오는 중…
    </section>
    <section v-else-if="!room" class="multi-state-card multi-state-error" role="alert">
      <strong>공유방을 열 수 없어요.</strong>
      <p>{{ error }}</p>
      <NuxtLink to="/multi">새 멀티방 만들기</NuxtLink>
    </section>

    <template v-else>
      <section class="multi-machine-stage" aria-labelledby="multi-machine-title">
        <h2 id="multi-machine-title" class="sr-only">참가자 공동 점심 추첨 기계</h2>
        <div class="machine-shadow" aria-hidden="true" />
        <div class="machine-body multi-machine-body">
          <span class="bolt bolt-top-left" aria-hidden="true" />
          <span class="bolt bolt-top-right" aria-hidden="true" />
          <span class="bolt bolt-bottom-left" aria-hidden="true" />
          <span class="bolt bolt-bottom-right" aria-hidden="true" />

          <div class="multi-machine-label">
            <span>오늘의</span>
            <strong>단체 점심</strong>
            <small>{{ room.participant_count }}명 참가 중</small>
          </div>

          <ol class="participant-reels" aria-label="참가자 준비 상태">
            <li
              v-for="(participant, index) in room.participants"
              :key="participant.id"
              :class="{ 'participant-reel-ready': participant.is_ready, 'participant-reel-spinning': isPulling }"
            >
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <strong>{{ participant.nickname }}</strong>
              <small v-if="participant.is_host">HOST</small>
              <b>{{ participant.is_ready ? `${participant.choice_count}개 완료` : '목록 작성 중' }}</b>
            </li>
          </ol>

          <div class="multi-result-window" aria-live="polite" aria-atomic="true">
            <article v-if="room.result" class="ticket multi-result-ticket">
              <p class="ticket-kicker">GROUP WINNER · DRAW {{ room.result.draw_count }}</p>
              <p class="ticket-number">{{ room.result.votes }} VOTES</p>
              <h3>{{ room.result.food.name }}</h3>
              <p class="ticket-family">{{ room.result.food.family }}</p>
              <div class="ticket-rule" aria-hidden="true" />
              <p class="ticket-reason">
                {{ room.can_reroll ? '공동 최다 메뉴 중 하나예요. 다시 뽑을 수 있습니다.' : '가장 많은 참가자의 목록에 겹친 메뉴예요.' }}
              </p>
              <p class="ticket-description">{{ room.result.food.description }}</p>
            </article>
            <div v-else class="multi-waiting-display">
              <span class="status-lamp" aria-hidden="true" />
              <p>{{ room.all_ready ? '집계 완료' : '목록 수집 중' }}</p>
              <strong>{{ statusMessage }}</strong>
            </div>
          </div>

          <div v-if="room.all_ready && room.leaders.length" class="multi-leaders">
            <span>현재 최다</span>
            <ul>
              <li v-for="leader in room.leaders" :key="leader.key">
                {{ leader.name }} <b>{{ leader.votes }}표</b>
              </li>
            </ul>
          </div>

          <div class="output-slot" aria-hidden="true"><span /></div>

          <button
            class="lever multi-lever"
            :class="{ 'lever-pulled': isPulling }"
            type="button"
            :disabled="!canUseLever"
            :aria-label="room ? multiLeverLabel(room) : '공동 점심 레버'"
            aria-describedby="multi-room-status"
            @click="handleDraw"
          >
            <span class="lever-handle" aria-hidden="true" />
            <span class="lever-stem" aria-hidden="true" />
            <span class="lever-base" aria-hidden="true" />
          </button>
        </div>
      </section>

      <section class="multi-room-controls">
        <p id="multi-room-status" :class="{ 'multi-no-overlap': room.blocked_reason === 'no_overlap' }">
          {{ statusMessage }}
        </p>
        <div>
          <button
            v-if="room.self && room.status === 'WAITING'"
            type="button"
            class="action-button action-secondary"
            @click="choiceDialogOpen = true"
          >
            <span>{{ room.self.is_ready ? '내 목록 수정' : '내 목록 작성' }}</span>
            <small>{{ room.self.choices.length }}개 선택됨</small>
          </button>
          <p v-if="room.self && !isHost" class="multi-host-note">최종 레버는 방장이 당깁니다.</p>
          <p v-else-if="!room.self && room.status === 'DRAWN'" class="multi-host-note">추첨이 끝난 공개 결과입니다.</p>
        </div>
        <p v-if="error" class="multi-form-error" role="alert">{{ error }}</p>
      </section>

      <Teleport to="body">
        <div v-if="!room.self && room.status === 'WAITING'" class="multi-overlay">
          <section class="multi-join-panel" role="dialog" aria-modal="true" aria-labelledby="multi-join-title">
            <p>ROOM {{ room.code }}</p>
            <h2 id="multi-join-title">닉네임으로 참가하기</h2>
            <p>계정은 필요하지 않아요. 이 방에서 구분할 이름만 입력해 주세요.</p>
            <form @submit.prevent="handleJoin">
              <label>
                <span>닉네임</span>
                <input v-model="joinNickname" type="text" minlength="2" maxlength="20" autocomplete="nickname" required autofocus>
              </label>
              <button type="submit" :disabled="isMutating || joinNickname.trim().length < 2">
                {{ isMutating ? '참가 중…' : '방에 참가하기' }}
              </button>
            </form>
            <p v-if="error" class="multi-form-error" role="alert">{{ error }}</p>
          </section>
        </div>
      </Teleport>

      <MultiChoiceDialog
        :open="choiceDialogOpen && Boolean(room.self) && room.status === 'WAITING'"
        :initial-choices="room.self?.choices || []"
        :submitting="isMutating"
        @close="choiceDialogOpen = false"
        @submit="handleChoiceSubmit"
      />
    </template>
  </main>
</template>

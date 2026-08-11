<script setup lang="ts">
const { state, isBusy, draw, accept, reroll } = useLunchMachine()
const { user } = useAuth()

useHead({
  title: '점심 결정 기계',
})

const hasTicket = computed(() => Boolean(state.value.ticket))
const ticketAccepted = computed(() => state.value.status === 'accepted')
</script>

<template>
  <main class="experience-shell">
    <header class="masthead">
      <p class="eyebrow">LUNCH DECISION UNIT · LM—01</p>
      <h1>점심 결정 기계</h1>
      <p class="masthead-copy">고민은 기계 안에 넣어 두었습니다. 한 번만 당겨 보세요.</p>
    </header>

    <section class="machine-stage" aria-labelledby="machine-title">
      <h2 id="machine-title" class="sr-only">개인화 점심 추천 기계</h2>

      <div class="machine-shadow" aria-hidden="true" />
      <div class="machine-body">
        <span class="bolt bolt-top-left" aria-hidden="true" />
        <span class="bolt bolt-top-right" aria-hidden="true" />
        <span class="bolt bolt-bottom-left" aria-hidden="true" />
        <span class="bolt bolt-bottom-right" aria-hidden="true" />

        <div class="machine-label" aria-hidden="true">
          <span>오늘의</span>
          <strong>점심</strong>
          <small>DECISION SERVICE</small>
        </div>

        <div class="ticket-window" aria-live="polite" aria-atomic="true">
          <div
            v-if="state.status === 'idle'"
            class="window-idle"
          >
            <span class="status-lamp" aria-hidden="true" />
            <p>준비 완료</p>
            <strong>레버를 당겨 주세요</strong>
          </div>

          <div
            v-else-if="state.status === 'drawing' || state.status === 'rerolling'"
            class="window-loading"
          >
            <div class="ticker-dots" aria-hidden="true">
              <i />
              <i />
              <i />
            </div>
            <p>{{ state.status === 'rerolling' ? '새 후보를 찾는 중' : '취향을 계산하는 중' }}</p>
          </div>

          <article
            v-else-if="state.ticket"
            class="ticket"
            :class="{ 'ticket-accepted': ticketAccepted }"
          >
            <div class="ticket-teeth ticket-teeth-top" aria-hidden="true" />
            <p class="ticket-kicker">TODAY'S LUNCH · {{ state.ticket.policyVersion }}</p>
            <p class="ticket-number">NO. {{ String(state.ticket.recommendationId).padStart(4, '0') }}</p>
            <h3>{{ state.ticket.food.name }}</h3>
            <p class="ticket-family">{{ state.ticket.food.family }}</p>
            <div class="ticket-rule" aria-hidden="true" />
            <p class="ticket-reason">{{ state.ticket.reason }}</p>
            <p class="ticket-description">{{ state.ticket.food.description }}</p>
            <div v-if="ticketAccepted" class="accepted-stamp" aria-label="선택 완료">
              선택 완료
            </div>
            <div class="ticket-teeth ticket-teeth-bottom" aria-hidden="true" />
          </article>

          <div v-else-if="state.status === 'error'" class="window-error" role="alert">
            <span aria-hidden="true">!</span>
            <p>{{ state.error }}</p>
          </div>
        </div>

        <div class="output-slot" aria-hidden="true">
          <span />
        </div>

        <button
          class="lever"
          type="button"
          :class="{ 'lever-pulled': isBusy }"
          :disabled="isBusy || hasTicket"
          aria-label="점심 추천 레버 당기기"
          @click="draw"
        >
          <span class="lever-handle" aria-hidden="true" />
          <span class="lever-stem" aria-hidden="true" />
          <span class="lever-base" aria-hidden="true" />
          <span class="lever-copy">{{ isBusy ? '작동 중' : '당기기' }}</span>
        </button>

        <div class="machine-instruction">
          <span>01</span>
          <p>레버를 한 번 당기면<br>오늘의 메뉴가 나옵니다.</p>
        </div>
      </div>
    </section>

    <section v-if="state.ticket" class="ticket-actions" aria-label="추천 결과 선택">
      <template v-if="!ticketAccepted">
        <button class="action-button action-primary" type="button" :disabled="isBusy" @click="accept">
          <span>이걸 먹을래요</span>
          <small>선택을 기억합니다</small>
        </button>
        <button class="action-button action-secondary" type="button" :disabled="isBusy" @click="reroll">
          <span>다른 메뉴 뽑기</span>
          <small>약한 거절로 기록합니다</small>
        </button>
      </template>
      <div v-else class="accepted-message" role="status">
        <strong>결정 끝.</strong>
        <span>맛있게 먹고 오세요.</span>
      </div>
    </section>

    <button
      v-else-if="state.status === 'error'"
      class="retry-button"
      type="button"
      @click="draw"
    >
      다시 시도하기
    </button>

    <footer class="page-footer">
      <p v-if="user">{{ user.display_name }} 님의 선택을 계정에 기억합니다.</p>
      <p v-else>로그인 전에는 이 기기의 선택 기록만 사용합니다.</p>
      <span aria-hidden="true">●</span>
      <p><NuxtLink to="/privacy">정밀 위치는 수집하지 않습니다.</NuxtLink></p>
    </footer>
  </main>
</template>

<script setup lang="ts">
import type {
  RecommendationFilterKey,
  RecommendationFilterValue,
} from '../types/recommendation'
import {
  cloneRecommendationFilters,
  countRecommendationFilters,
  createEmptyRecommendationFilters,
  RECOMMENDATION_FILTER_GROUPS,
  toggleRecommendationFilter,
} from '../utils/recommendationFilters'

const {
  state,
  isBusy,
  filters,
  noMatchingFoods,
  setFilters,
  draw,
  accept,
  reroll,
} = useLunchMachine()
const { user } = useAuth()

useHead({
  title: '점심 결정 기계',
})

const hasTicket = computed(() => Boolean(state.value.ticket))
const ticketAccepted = computed(() => state.value.status === 'accepted')
const filterDialogOpen = ref(false)
const filterTrigger = ref<HTMLButtonElement | null>(null)
const filterCloseButton = ref<HTMLButtonElement | null>(null)
const filterPanel = ref<HTMLElement | null>(null)
const draftFilters = ref(cloneRecommendationFilters(filters.value))
const activeFilterCount = computed(() => countRecommendationFilters(filters.value))
const draftFilterCount = computed(() => countRecommendationFilters(draftFilters.value))

async function openFilterDialog(): Promise<void> {
  draftFilters.value = cloneRecommendationFilters(filters.value)
  filterDialogOpen.value = true
  await nextTick()
  filterCloseButton.value?.focus()
}

async function closeFilterDialog(): Promise<void> {
  filterDialogOpen.value = false
  await nextTick()
  filterTrigger.value?.focus()
}

function toggleDraftFilter(
  key: RecommendationFilterKey,
  value: RecommendationFilterValue,
): void {
  draftFilters.value = toggleRecommendationFilter(draftFilters.value, key, value)
}

function clearDraftFilters(): void {
  draftFilters.value = createEmptyRecommendationFilters()
}

function applyFilters(): void {
  setFilters(draftFilters.value)
  void closeFilterDialog()
}

function handleFilterDialogKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    void closeFilterDialog()
    return
  }
  if (event.key !== 'Tab' || !filterPanel.value) {
    return
  }

  const focusable = Array.from(
    filterPanel.value.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  )
  const first = focusable[0]
  const last = focusable.at(-1)
  if (!first || !last) {
    return
  }
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  }
  else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}
</script>

<template>
  <main class="experience-shell">
    <header class="masthead">
      <p class="eyebrow">LUNCH DECISION UNIT · LM—01</p>
      <h1>점심 결정 기계</h1>
    </header>

    <section class="machine-stage" aria-labelledby="machine-title">
      <h2 id="machine-title" class="sr-only">개인화 점심 추천 기계</h2>

      <div class="machine-shadow" aria-hidden="true" />
      <div class="machine-body">
        <span class="bolt bolt-top-left" aria-hidden="true" />
        <span class="bolt bolt-top-right" aria-hidden="true" />
        <span class="bolt bolt-bottom-left" aria-hidden="true" />
        <span class="bolt bolt-bottom-right" aria-hidden="true" />

        <button
          ref="filterTrigger"
          class="machine-label"
          type="button"
          aria-haspopup="dialog"
          :aria-expanded="filterDialogOpen"
          aria-controls="recommendation-filter-dialog"
          @click="openFilterDialog"
        >
          <span>오늘의</span>
          <strong>점심</strong>
          <small>{{ activeFilterCount ? `조건 ${activeFilterCount}개 선택` : '조건 고르기' }}</small>
          <b v-if="activeFilterCount" class="filter-count" aria-hidden="true">
            {{ activeFilterCount }}
          </b>
        </button>

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
        </button>
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
      @click="noMatchingFoods ? openFilterDialog() : draw()"
    >
      {{ noMatchingFoods ? '조건 다시 고르기' : '다시 시도하기' }}
    </button>

    <footer class="page-footer">
      <p v-if="user">{{ user.display_name }} 님의 선택을 계정에 기억합니다.</p>
      <p v-else>로그인 전에는 이 기기의 선택 기록만 사용합니다.</p>
      <span aria-hidden="true">●</span>
      <p><NuxtLink to="/privacy">정밀 위치는 수집하지 않습니다.</NuxtLink></p>
    </footer>

    <Teleport to="body">
      <div
        v-if="filterDialogOpen"
        class="filter-overlay"
        @click.self="closeFilterDialog"
        @keydown="handleFilterDialogKeydown"
      >
        <section
          id="recommendation-filter-dialog"
          ref="filterPanel"
          class="filter-panel"
          role="dialog"
          aria-modal="true"
          aria-labelledby="filter-dialog-title"
          aria-describedby="filter-dialog-help"
        >
          <header class="filter-panel-header">
            <div>
              <p>MENU SELECTOR · MULTI</p>
              <h2 id="filter-dialog-title">먹고 싶은 조건</h2>
            </div>
            <button
              ref="filterCloseButton"
              class="filter-close"
              type="button"
              aria-label="조건 선택 창 닫기"
              @click="closeFilterDialog"
            >
              ×
            </button>
          </header>

          <p id="filter-dialog-help" class="filter-help">
            한 줄에서 여러 개를 고르면 후보가 늘고, 줄과 줄 사이는 모두 만족하는 메뉴만 남아요.
            아무것도 고르지 않은 줄은 제한하지 않습니다.
          </p>

          <div class="filter-groups">
            <fieldset
              v-for="group in RECOMMENDATION_FILTER_GROUPS"
              :key="group.key"
              class="filter-group"
            >
              <legend>{{ group.label }}</legend>
              <div class="filter-options">
                <label
                  v-for="option in group.options"
                  :key="option.value"
                  class="filter-option"
                  :class="{ 'filter-option-selected': draftFilters[group.key].includes(option.value) }"
                >
                  <input
                    type="checkbox"
                    :checked="draftFilters[group.key].includes(option.value)"
                    @change="toggleDraftFilter(group.key, option.value)"
                  >
                  <span aria-hidden="true">✓</span>
                  {{ option.label }}
                </label>
              </div>
            </fieldset>
          </div>

          <footer class="filter-panel-actions">
            <button class="filter-reset" type="button" @click="clearDraftFilters">
              모두 지우기
            </button>
            <button class="filter-apply" type="button" @click="applyFilters">
              {{ draftFilterCount ? `조건 ${draftFilterCount}개 적용` : '조건 없이 적용' }}
            </button>
          </footer>
        </section>
      </div>
    </Teleport>
  </main>
</template>

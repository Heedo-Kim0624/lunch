<script setup lang="ts">
import type { FoodSearchEnvelope, MultiFoodSummary } from '../types/multiRoom'

const props = defineProps<{
  open: boolean
  initialChoices: MultiFoodSummary[]
  submitting: boolean
}>()

const emit = defineEmits<{
  close: []
  submit: [foodIds: number[]]
}>()

const config = useRuntimeConfig()
const panel = ref<HTMLElement | null>(null)
const searchInput = ref<HTMLInputElement | null>(null)
const query = ref('')
const results = ref<MultiFoodSummary[]>([])
const selected = ref<MultiFoodSummary[]>([])
const isSearching = ref(false)
const searchError = ref('')
let searchTimer: ReturnType<typeof setTimeout> | null = null

const selectedIds = computed(() => new Set(selected.value.map(food => food.id)))
const canSubmit = computed(
  () => selected.value.length >= 1 && selected.value.length <= 12 && !props.submitting,
)

async function searchFoods(): Promise<void> {
  isSearching.value = true
  searchError.value = ''
  try {
    const response = await $fetch<FoodSearchEnvelope>(`${config.public.apiBase}/foods`, {
      query: { q: query.value.trim() },
    })
    results.value = response.foods
  }
  catch {
    searchError.value = '음식 목록을 불러오지 못했어요.'
  }
  finally {
    isSearching.value = false
  }
}

function toggleFood(food: MultiFoodSummary): void {
  if (selectedIds.value.has(food.id)) {
    selected.value = selected.value.filter(item => item.id !== food.id)
    return
  }
  if (selected.value.length < 12) {
    selected.value = [...selected.value, food]
  }
}

function removeFood(foodId: number): void {
  selected.value = selected.value.filter(food => food.id !== foodId)
}

function submit(): void {
  if (canSubmit.value) {
    emit('submit', selected.value.map(food => food.id))
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
    return
  }
  if (event.key !== 'Tab' || !panel.value) {
    return
  }
  const focusable = Array.from(
    panel.value.querySelectorAll<HTMLElement>(
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

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      return
    }
    selected.value = [...props.initialChoices]
    query.value = ''
    await searchFoods()
    await nextTick()
    searchInput.value?.focus()
  },
)

watch(query, () => {
  if (!props.open) {
    return
  }
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => void searchFoods(), 220)
})

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="multi-overlay" @click.self="emit('close')" @keydown="handleKeydown">
      <section
        ref="panel"
        class="multi-choice-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="multi-choice-title"
        aria-describedby="multi-choice-help"
      >
        <header class="multi-dialog-header">
          <div>
            <p>MY LUNCH REEL · 1—12</p>
            <h2 id="multi-choice-title">먹고 싶은 음식 목록</h2>
          </div>
          <button class="filter-close" type="button" aria-label="음식 선택 창 닫기" @click="emit('close')">
            ×
          </button>
        </header>

        <p id="multi-choice-help" class="multi-dialog-help">
          실제로 먹고 싶은 메뉴만 골라 주세요. 여러 사람의 목록에 겹친 메뉴가 최종 후보가 됩니다.
        </p>

        <label class="multi-food-search">
          <span>음식 검색</span>
          <input
            ref="searchInput"
            v-model="query"
            type="search"
            maxlength="40"
            placeholder="치킨, 라면, 김밥…"
            autocomplete="off"
          >
        </label>

        <div class="multi-selected" aria-live="polite">
          <div class="multi-selected-heading">
            <strong>내 목록</strong>
            <span>{{ selected.length }} / 12</span>
          </div>
          <p v-if="selected.length === 0" class="multi-empty-copy">아직 고른 음식이 없어요.</p>
          <ul v-else>
            <li v-for="food in selected" :key="food.id">
              <span>{{ food.name }}</span>
              <button type="button" :aria-label="`${food.name} 목록에서 제거`" @click="removeFood(food.id)">
                ×
              </button>
            </li>
          </ul>
        </div>

        <div class="multi-search-results" aria-live="polite">
          <p v-if="isSearching">메뉴를 찾는 중…</p>
          <p v-else-if="searchError" role="alert">{{ searchError }}</p>
          <p v-else-if="results.length === 0">검색 결과가 없어요.</p>
          <ul v-else>
            <li v-for="food in results" :key="food.id">
              <button
                type="button"
                :class="{ 'food-result-selected': selectedIds.has(food.id) }"
                :aria-pressed="selectedIds.has(food.id)"
                :disabled="!selectedIds.has(food.id) && selected.length >= 12"
                @click="toggleFood(food)"
              >
                <span>
                  <strong>{{ food.name }}</strong>
                  <small>{{ food.cuisine }} · {{ food.family }}</small>
                </span>
                <b>{{ selectedIds.has(food.id) ? '선택됨' : '추가' }}</b>
              </button>
            </li>
          </ul>
        </div>

        <footer class="multi-dialog-actions">
          <button class="filter-reset" type="button" @click="emit('close')">나중에 작성</button>
          <button class="filter-apply" type="button" :disabled="!canSubmit" @click="submit">
            {{ submitting ? '저장 중…' : `목록 ${selected.length}개 작성 완료` }}
          </button>
        </footer>
      </section>
    </div>
  </Teleport>
</template>

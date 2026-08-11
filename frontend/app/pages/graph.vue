<script setup lang="ts">
import type { RecommendationGraphNode, RecommendationGraphResponse } from '../types/recommendationGraph'
import {
  GRAPH_HEIGHT,
  GRAPH_WIDTH,
  positionGraphEdges,
  positionGraphNodes,
} from '../utils/recommendationGraph'

const config = useRuntimeConfig()
const selectedNodeId = ref<number | null>(null)
const {
  data: graph,
  status,
  error,
  refresh,
} = await useFetch<RecommendationGraphResponse>(
  `${config.public.apiBase}/recommendation-graph`,
  { key: 'recommendation-graph' },
)

useHead({ title: '음식 취향 지도 · 점심 결정 기계' })

const positionedNodes = computed(() => positionGraphNodes(graph.value?.nodes ?? []))
const positionedEdges = computed(() => positionGraphEdges(graph.value?.edges ?? [], positionedNodes.value))
const selectedNode = computed<RecommendationGraphNode | null>(() => (
  graph.value?.nodes.find(node => node.id === selectedNodeId.value)
  ?? graph.value?.nodes[0]
  ?? null
))
const loading = computed(() => status.value === 'pending')

const cuisineLabels = {
  korean: '한식',
  chinese: '중식',
  western: '양식',
  japanese: '일식',
  southeast_asian: '동남아식',
  other: '그 외',
} as const

const attributeLabels: Record<string, string> = {
  spicy: '매운맛',
  broth: '국물',
  light: '가벼움',
  protein: '단백질',
  adventurous: '새로움',
  cold: '차가움',
  familiar: '익숙함',
}

function selectNode(nodeId: number): void {
  selectedNodeId.value = nodeId
}
</script>

<template>
  <main class="graph-page">
    <header class="graph-hero">
      <p class="eyebrow">TASTE RELATION MAP · RULES—V4</p>
      <h1>음식 취향 지도</h1>
      <p>
        음식의 특성이 비슷하면 가는 선으로, 최소 5명의 선택 흐름이 겹치면 굵은 선으로 연결됩니다.
        개인의 선택 목록이나 계정 정보는 표시하지 않습니다.
      </p>
    </header>

    <section class="graph-console" aria-labelledby="graph-title">
      <div class="graph-console-header">
        <div>
          <p>RELATION MONITOR</p>
          <h2 id="graph-title">현재 추천 관계망</h2>
        </div>
        <button type="button" class="graph-refresh" :disabled="loading" @click="refresh()">
          {{ loading ? '동기화 중' : '새로고침' }}
        </button>
      </div>

      <div v-if="loading && !graph" class="graph-state" role="status">
        선택 관계를 조립하고 있어요.
      </div>
      <div v-else-if="error" class="graph-state graph-state-error" role="alert">
        <p>취향 지도를 불러오지 못했어요.</p>
        <button type="button" @click="refresh()">다시 불러오기</button>
      </div>
      <template v-else-if="graph">
        <div class="graph-stats" aria-label="그래프 요약">
          <span><strong>{{ graph.stats.node_count }}</strong> 음식</span>
          <span><strong>{{ graph.stats.edge_count }}</strong> 연결</span>
          <span>
            <strong>{{ graph.stats.mode === 'hybrid' ? '혼합' : '특성' }}</strong>
            모드
          </span>
          <span>
            <strong>{{ graph.privacy.minimum_shared_selectors }}명+</strong>
            공개 기준
          </span>
        </div>

        <div class="graph-workbench">
          <div class="graph-canvas" tabindex="0" aria-label="음식 관계 그래프. 방향키 대신 Tab 키로 각 음식을 탐색할 수 있습니다.">
            <svg
              class="graph-svg"
              :viewBox="`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`"
              role="img"
              aria-labelledby="graph-svg-title graph-svg-description"
            >
              <title id="graph-svg-title">음식 특성과 공동 선택 관계</title>
              <desc id="graph-svg-description">
                색상은 음식 나라 분류, 선은 특성 또는 집계된 공동 선택 관계를 뜻합니다.
              </desc>
              <g class="graph-cluster-labels" aria-hidden="true">
                <text x="165" y="32">한식</text>
                <text x="480" y="32">중식</text>
                <text x="795" y="32">양식</text>
                <text x="165" y="605">일식</text>
                <text x="480" y="605">동남아식</text>
                <text x="795" y="605">그 외</text>
              </g>
              <line
                v-for="edge in positionedEdges"
                :key="`${edge.source}-${edge.target}`"
                :x1="edge.x1"
                :y1="edge.y1"
                :x2="edge.x2"
                :y2="edge.y2"
                :class="['graph-edge', `graph-edge-${edge.relation}`]"
              >
                <title>
                  {{ edge.relation === 'content' ? '특성이 비슷한 음식' : `${edge.selector_count}명 이상의 선택이 겹친 음식` }}
                </title>
              </line>
              <g
                v-for="node in positionedNodes"
                :key="node.id"
                :class="['graph-node', `graph-node-${node.cuisine_group}`, { 'graph-node-selected': selectedNode?.id === node.id }]"
                :transform="`translate(${node.x} ${node.y})`"
                role="button"
                tabindex="0"
                :aria-label="`${node.name}, ${cuisineLabels[node.cuisine_group]}, ${node.family}`"
                @click="selectNode(node.id)"
                @keydown.enter.prevent="selectNode(node.id)"
                @keydown.space.prevent="selectNode(node.id)"
              >
                <circle :r="node.selector_count ? 12 : 8" />
                <text v-if="selectedNode?.id === node.id" y="-17">{{ node.name }}</text>
              </g>
            </svg>
          </div>

          <aside class="graph-inspector" aria-live="polite">
            <template v-if="selectedNode">
              <p class="graph-inspector-kicker">SELECTED NODE</p>
              <h3>{{ selectedNode.name }}</h3>
              <p>{{ selectedNode.cuisine }} · {{ selectedNode.family }}</p>
              <p v-if="selectedNode.selector_count" class="graph-shared-signal">
                최소 {{ selectedNode.selector_count }}명의 집계 선택 신호가 있어요.
              </p>
              <dl class="graph-attributes">
                <template v-for="(value, key) in selectedNode.attributes" :key="key">
                  <dt>{{ attributeLabels[key] ?? key }}</dt>
                  <dd>
                    <span :style="{ width: `${Math.round(value * 100)}%` }" />
                    <b>{{ Math.round(value * 100) }}</b>
                  </dd>
                </template>
              </dl>
            </template>
          </aside>
        </div>

        <div class="graph-legend" aria-label="관계 범례">
          <span><i class="legend-content" /> 음식 특성 유사</span>
          <span><i class="legend-collaborative" /> 공동 선택</span>
          <span><i class="legend-hybrid" /> 두 관계 모두</span>
        </div>

        <details class="graph-text-alternative">
          <summary>텍스트 음식 목록 보기</summary>
          <ul>
            <li v-for="node in graph.nodes" :key="node.id">
              <button type="button" @click="selectNode(node.id)">
                {{ node.name }} — {{ node.cuisine }}, {{ node.family }}
              </button>
            </li>
          </ul>
        </details>
      </template>
    </section>

    <section class="graph-explainer" aria-labelledby="graph-how-title">
      <p>HOW IT LEARNS</p>
      <h2 id="graph-how-title">그래프는 추천에 이렇게 들어갑니다</h2>
      <ol>
        <li>로그인 사용자의 수락·먹음·즐겨찾기를 시간 감쇠해 집계합니다.</li>
        <li>최소 5명이 함께 고른 음식 쌍만 협업 관계로 인정합니다.</li>
        <li>현재 사용자가 좋아한 음식과 연결된 후보에 협업 점수를 더합니다.</li>
        <li>필터·싫어요·최근 반복 감점은 협업 추천보다 먼저 보호 장치로 적용됩니다.</li>
      </ol>
    </section>
  </main>
</template>

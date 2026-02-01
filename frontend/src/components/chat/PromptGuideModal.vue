<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="1000px"
    class="prompt-guide-modal"
    :close-on-click-modal="true"
    :close-on-press-escape="true"
  >
    <!-- NL2SQL 가이드 -->
    <div v-if="mode === 'nl2sql'" class="guide-content">
      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><DataLine /></el-icon>
          조회 가능한 데이터
        </h4>
        <div class="data-tables">
          <div v-for="table in nl2sqlTables" :key="table.name" class="table-info">
            <div class="table-header">
              <span class="table-name">{{ table.name }}</span>
              <span class="table-desc">{{ table.description }}</span>
            </div>
            <div class="table-columns">
              <el-tag
                v-for="col in table.columns"
                :key="col"
                size="small"
                type="info"
                class="column-tag"
              >
                {{ col }}
              </el-tag>
            </div>
          </div>
        </div>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><CircleCheck /></el-icon>
          좋은 질문 예시
        </h4>
        <ul class="example-list good">
          <li v-for="example in nl2sqlGoodExamples" :key="example" @click="useExample(example)">
            <el-icon><Check /></el-icon>
            {{ example }}
          </li>
        </ul>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><Warning /></el-icon>
          피해야 할 질문
        </h4>
        <ul class="example-list bad">
          <li v-for="example in nl2sqlBadExamples" :key="example.text">
            <el-icon><Close /></el-icon>
            <span>{{ example.text }}</span>
            <span class="reason">- {{ example.reason }}</span>
          </li>
        </ul>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><InfoFilled /></el-icon>
          프롬프트 작성 팁
        </h4>
        <ul class="tips-list">
          <li v-for="(tip, index) in nl2sqlTips" :key="index">
            <span class="tip-number">{{ index + 1 }}</span>
            <span v-html="tip"></span>
          </li>
        </ul>
      </section>

      <section class="guide-section important-rules">
        <h4 class="section-title">
          <el-icon><Bell /></el-icon>
          알아두면 좋은 규칙
        </h4>
        <div class="rules-grid">
          <div class="rule-item">
            <span class="rule-label">기본 조건</span>
            <span class="rule-value">특별한 언급 없으면 <strong>재직자</strong>만 조회</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">입사자 집계</span>
            <span class="rule-value">입사일(HIRE_DATE) 기준, 재직 조건 불필요</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">퇴사자 집계</span>
            <span class="rule-value">퇴사일(RETIRE_DATE) 기준, 재직 조건 불필요</span>
          </div>
          <div class="rule-item">
            <span class="rule-label">상세 조회</span>
            <span class="rule-value">"목록", "명단", "상세" 언급 시 개별 데이터 표시</span>
          </div>
        </div>
      </section>
    </div>

    <!-- RAG 가이드 -->
    <div v-else-if="mode === 'rag'" class="guide-content">
      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><Document /></el-icon>
          검색 가능한 문서
        </h4>
        <div class="doc-categories">
          <div v-for="category in ragCategories" :key="category.type" class="category-info">
            <div class="category-header">
              <el-tag :type="category.tagType" size="small">{{ category.label }}</el-tag>
            </div>
            <ul class="doc-list">
              <li v-for="doc in category.documents" :key="doc">{{ doc }}</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><CircleCheck /></el-icon>
          좋은 질문 예시
        </h4>
        <ul class="example-list good">
          <li v-for="example in ragGoodExamples" :key="example" @click="useExample(example)">
            <el-icon><Check /></el-icon>
            {{ example }}
          </li>
        </ul>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><Warning /></el-icon>
          피해야 할 질문
        </h4>
        <ul class="example-list bad">
          <li v-for="example in ragBadExamples" :key="example.text">
            <el-icon><Close /></el-icon>
            <span>{{ example.text }}</span>
            <span class="reason">- {{ example.reason }}</span>
          </li>
        </ul>
      </section>

      <section class="guide-section">
        <h4 class="section-title">
          <el-icon><InfoFilled /></el-icon>
          프롬프트 작성 팁
        </h4>
        <ul class="tips-list">
          <li v-for="(tip, index) in ragTips" :key="index">
            <span class="tip-number">{{ index + 1 }}</span>
            {{ tip }}
          </li>
        </ul>
      </section>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="visible = false">닫기</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import {
  DataLine, Document, CircleCheck, Warning, InfoFilled, Bell,
  Check, Close
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  mode: {
    type: String,
    default: 'nl2sql',
    validator: (value) => ['nl2sql', 'rag', 'auto', 'agent'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'use-example'])

const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => {
  const titles = {
    nl2sql: 'NL2SQL 프롬프트 가이드',
    rag: 'RAG 프롬프트 가이드',
    auto: '프롬프트 가이드',
    agent: 'Agent 프롬프트 가이드'
  }
  return titles[props.mode] || '프롬프트 가이드'
})

// ============================================
// NL2SQL 가이드 데이터 (docs/NL2SQL 시스템 프롬프트.md 기반)
// ============================================
const nl2sqlTables = [
  {
    name: 'v_ai_employee',
    description: '직원 기본정보 (핵심 테이블)',
    columns: ['이름', '직위', '부서', '입사일', '재직상태', '성별', '고용형태', '퇴직일']
  },
  {
    name: 'v_ai_address',
    description: '주소 정보',
    columns: ['주소', '상세주소', '우편번호', '거주지역']
  },
  {
    name: 'v_ai_education',
    description: '학력 정보',
    columns: ['학교명', '전공', '복수전공', '졸업연도']
  },
  {
    name: 'v_ai_career',
    description: '경력 정보',
    columns: ['전직장', '직위', '근무기간', '경력인정율']
  },
  {
    name: 'v_ai_license',
    description: '자격증 정보',
    columns: ['자격증명', '자격구분', '발급기관', '취득일', '유효상태']
  },
  {
    name: 'v_ai_language',
    description: '어학 정보',
    columns: ['어학종류', '시험종류', '점수', '등급']
  },
  {
    name: 'v_ai_feedback',
    description: '인사평가 정보',
    columns: ['평가명', '평가종류', '평가점수', '평가등급', '평가일자']
  },
  {
    name: 'v_ai_pay_report',
    description: '급여 정보',
    columns: ['급여년월', '고정비', '변동비', '지급합계', '실지급액']
  },
  {
    name: 'v_ai_training',
    description: '교육 정보',
    columns: ['과정명', '교육기관', '시작일', '종료일', '수료여부']
  },
  {
    name: 'v_ai_reward',
    description: '상벌 정보',
    columns: ['상벌구분', '상벌종류', '사유', '일자', '포상금']
  },
  {
    name: 'v_ai_military',
    description: '병역 정보',
    columns: ['군종류', '계급', '병과', '전역일']
  },
  {
    name: 'v_ai_family',
    description: '가족 정보',
    columns: ['관계', '이름', '성별', '생년월일', '장애여부']
  }
]

const nl2sqlGoodExamples = [
  '2024년 입사자는 몇 명인가요?',
  '부서별 직원 수를 보여줘',
  '현재 재직 중인 직원은 몇 명인가요?',
  '2010년부터 2020년까지 연도별 입사자/퇴사자 현황',
  'TOEIC 800점 이상인 직원 수',
  '정보처리기사 자격증 보유자 명단',
  '서울에 사는 직원 목록',
  '홍길동의 학력과 자격증을 보여줘',
  '2023년 인사평가 A등급 받은 직원 수'
]

const nl2sqlBadExamples = [
  { text: '직원 알려줘', reason: '너무 모호함, 구체적 조건 필요' },
  { text: '매출액이 얼마야?', reason: '존재하지 않는 데이터 (인사 데이터만 조회 가능)' },
  { text: '김철수 급여 알려줘', reason: '개인 급여 정보는 제한될 수 있음' }
]

const nl2sqlTips = [
  '<strong>수치/통계</strong>가 필요하면 "몇 명", "몇 건", "총 수" 등으로 질문',
  '<strong>목록/상세</strong>가 필요하면 "명단", "목록", "상세 정보" 등으로 질문',
  '<strong>기간</strong>을 명시하세요 (예: "2024년", "2010년~2020년")',
  '<strong>조건</strong>을 구체적으로 (예: "서울 근무", "과장급 이상", "정규직")',
  '퇴직자 조회 시 "퇴직자", "퇴사자" 명시 (기본은 재직자만 조회)'
]

// ============================================
// RAG 가이드 데이터 (추후 DB 연동 예정)
// ============================================
const ragCategories = [
  {
    type: 'policy',
    label: '정책/규정',
    tagType: 'primary',
    documents: ['재택근무 정책', '연차휴가 규정', '출장비 정산 기준', '보안 정책']
  },
  {
    type: 'guide',
    label: '가이드',
    tagType: 'success',
    documents: ['신입사원 온보딩 가이드', '업무 매뉴얼', '시스템 사용 가이드']
  },
  {
    type: 'faq',
    label: 'FAQ',
    tagType: 'warning',
    documents: ['인사 관련 FAQ', '복리후생 FAQ', 'IT 지원 FAQ']
  }
]

const ragGoodExamples = [
  '재택근무 신청 절차와 조건은?',
  '연차 휴가는 어떻게 신청하나요?',
  '출장비 정산 기준이 어떻게 되나요?',
  '성과평가 제도는 어떻게 운영되나요?',
  '신입사원 온보딩 절차를 알려주세요'
]

const ragBadExamples = [
  { text: '재택근무', reason: '질문 형태가 아님, 무엇을 알고 싶은지 명시 필요' },
  { text: '올해 매출 목표', reason: '문서에 없는 정보일 수 있음' },
  { text: '김부장님 연락처', reason: '개인정보는 문서에서 제공하지 않음' }
]

const ragTips = [
  '알고 싶은 내용을 질문 형태로 작성하세요',
  '특정 정책이나 절차에 대해 구체적으로 질문하세요',
  '조건이나 제한사항이 궁금하면 명시적으로 요청하세요',
  '"~은 어떻게 되나요?", "~의 기준은?" 형식이 효과적입니다'
]

// 예시 사용
const useExample = (example) => {
  emit('use-example', example)
  visible.value = false
}
</script>

<style lang="scss" scoped>
.prompt-guide-modal {
  :deep(.el-dialog) {
    border-radius: 16px;

    .el-dialog__header {
      border-bottom: 1px solid var(--border-color);
      padding: 16px 20px;
      margin: 0;
    }

    .el-dialog__title {
      font-size: 18px;
      font-weight: 600;
    }

    .el-dialog__body {
      padding: 0;
      max-height: 65vh;
      overflow-y: auto;
    }

    .el-dialog__footer {
      border-top: 1px solid var(--border-color);
      padding: 12px 20px;
    }
  }
}

.guide-content {
  padding: 16px 20px;
}

.guide-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color-primary);
  margin: 0 0 12px;

  .el-icon {
    font-size: 18px;
    color: var(--color-primary);
  }
}

// NL2SQL 테이블 정보
.data-tables {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.table-info {
  background: var(--bg-color-page);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
}

.table-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 8px;

  .table-name {
    font-weight: 600;
    font-size: 12px;
    color: var(--color-primary);
    font-family: monospace;
  }

  .table-desc {
    font-size: 11px;
    color: var(--text-color-secondary);
  }
}

.table-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.column-tag {
  font-size: 10px;
  padding: 2px 6px;
  height: auto;
}

// RAG 카테고리
.doc-categories {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.category-info {
  background: var(--bg-color-page);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
}

.category-header {
  margin-bottom: 8px;
}

.doc-list {
  margin: 0;
  padding-left: 20px;

  li {
    font-size: 13px;
    color: var(--text-color-regular);
    line-height: 1.6;
  }
}

// 예시 리스트
.example-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;

  li {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 13px;
    transition: background-color 0.2s;

    .el-icon {
      margin-top: 2px;
      flex-shrink: 0;
    }

    .reason {
      color: var(--text-color-secondary);
      font-size: 11px;
    }
  }

  &.good li {
    background: rgba(103, 194, 58, 0.1);
    color: var(--text-color-primary);
    cursor: pointer;

    .el-icon {
      color: #67c23a;
    }

    &:hover {
      background: rgba(103, 194, 58, 0.2);
    }
  }

  &.bad {
    grid-template-columns: 1fr;

    li {
      background: rgba(245, 108, 108, 0.1);
      color: var(--text-color-primary);
      cursor: default;
      flex-wrap: wrap;

      .el-icon {
        color: #f56c6c;
      }
    }
  }
}

// 팁 리스트
.tips-list {
  margin: 0;
  padding: 0;
  list-style: none;

  li {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 13px;
    color: var(--text-color-regular);
    line-height: 1.6;
    margin-bottom: 8px;

    :deep(strong) {
      color: var(--color-primary);
      font-weight: 600;
    }
  }

  .tip-number {
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 20px;
    height: 20px;
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
  }
}

// 규칙 그리드
.important-rules {
  background: rgba(64, 158, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
  margin-top: 20px;
}

.rules-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.rule-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: var(--bg-color-card);
  border-radius: 8px;
  padding: 10px 12px;

  .rule-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--color-primary);
    text-transform: uppercase;
  }

  .rule-value {
    font-size: 12px;
    color: var(--text-color-regular);
    line-height: 1.4;

    strong {
      color: var(--text-color-primary);
    }
  }
}

// 다크모드 대응
:root[data-theme="dark"] {
  .table-info,
  .category-info {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }

  .example-list.good li {
    background: rgba(103, 194, 58, 0.15);
  }

  .example-list.bad li {
    background: rgba(245, 108, 108, 0.15);
  }

  .important-rules {
    background: rgba(64, 158, 255, 0.12);
  }

  .rule-item {
    background: rgba(255, 255, 255, 0.05);
  }
}

// 반응형
@media (max-width: 1024px) {
  .data-tables {
    grid-template-columns: repeat(3, 1fr);
  }

  .example-list {
    grid-template-columns: repeat(2, 1fr);
  }

  .rules-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .data-tables {
    grid-template-columns: repeat(2, 1fr);
  }

  .doc-categories {
    grid-template-columns: 1fr;
  }

  .example-list {
    grid-template-columns: 1fr;
  }

  .rules-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .data-tables {
    grid-template-columns: 1fr;
  }
}
</style>

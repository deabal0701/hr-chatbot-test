<template>
  <div class="settings-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>시스템 설정</h2>
        <p class="subtitle">API, 모델, 검색 파라미터 등을 설정합니다.</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="loadSettings" :loading="isLoading">
        새로고침
      </el-button>
    </div>

    <!-- 설정 탭 -->
    <div class="content-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <!-- OpenAI 설정 -->
        <el-tab-pane label="OpenAI" name="openai">
          <div class="settings-section">
            <h3>OpenAI API 설정</h3>
            <el-form label-position="top" class="settings-form openai-form">
              <el-form-item label="API Key">
                <div class="api-key-input">
                  <el-input
                    v-model="formData.openai.api_key"
                    :type="showApiKey ? 'text' : 'password'"
                    placeholder="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    clearable
                    class="api-key-field"
                  >
                    <template #suffix>
                      <el-icon class="cursor-pointer" @click="showApiKey = !showApiKey">
                        <View v-if="!showApiKey" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                  <el-button type="success" @click="validateApiKey" :loading="validating">
                    검증
                  </el-button>
                </div>
                <div v-if="apiKeyStatus" class="validation-status" :class="apiKeyStatus.valid ? 'success' : 'error'">
                  {{ apiKeyStatus.message }}
                </div>
              </el-form-item>

              <el-form-item label="Organization ID (선택)">
                <el-input
                  v-model="formData.openai.organization_id"
                  placeholder="org-xxxxxxxxxxxxxxxxxxxxxxxx"
                  clearable
                  class="org-id-field"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Anthropic 설정 -->
        <el-tab-pane label="Anthropic" name="anthropic">
          <div class="settings-section">
            <h3>Anthropic API 설정</h3>
            <el-form label-position="top" class="settings-form openai-form">
              <el-form-item label="API Key">
                <div class="api-key-input">
                  <el-input
                    v-model="formData.anthropic.api_key"
                    :type="showAnthropicApiKey ? 'text' : 'password'"
                    placeholder="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    clearable
                    class="api-key-field"
                  >
                    <template #suffix>
                      <el-icon class="cursor-pointer" @click="showAnthropicApiKey = !showAnthropicApiKey">
                        <View v-if="!showAnthropicApiKey" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                </div>
                <div class="form-help">
                  Anthropic Claude 모델 사용을 위한 API 키를 입력하세요.
                  <a href="https://console.anthropic.com/settings/keys" target="_blank">API 키 발급받기 →</a>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 임베딩 설정 -->
        <el-tab-pane label="임베딩" name="embedding">
          <div class="settings-section">
            <h3>임베딩 모델 설정</h3>

            <el-form label-position="top" class="settings-form">
              <el-form-item label="임베딩 모델">
                <el-select
                  v-model="formData.embedding.model"
                  style="width: 100%"
                  @change="onEmbeddingModelChange"
                >
                  <el-option label="text-embedding-3-small (추천, 1536차원)" value="text-embedding-3-small" />
                  <el-option label="text-embedding-3-large (3072차원)" value="text-embedding-3-large" />
                  <el-option label="text-embedding-ada-002 (1536차원, 레거시)" value="text-embedding-ada-002" />
                </el-select>
              </el-form-item>

              <el-form-item label="벡터 차원">
                <el-input-number
                  v-model="formData.embedding.dimension"
                  :min="256"
                  :max="3072"
                  :step="256"
                  style="width: 100%"
                  disabled
                />
                <div class="form-help">
                  모델에 따라 자동 설정됩니다. (현재 DB: 1536 고정)
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- LLM 설정 -->
        <el-tab-pane label="LLM" name="llm">
          <div class="settings-section">
            <h3>LLM 모델 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="LLM 제공자">
                <el-select v-model="formData.llm.provider" style="width: 100%" @change="onLLMProviderChange">
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="Anthropic (Claude)" value="anthropic" />
                </el-select>
                <div class="form-help">LLM 서비스 제공자를 선택하세요</div>
              </el-form-item>

              <div class="form-item-with-link">
                <el-form-item label="LLM 모델">
                  <el-input
                    v-model="formData.llm.model"
                    :placeholder="getLLMModelPlaceholder()"
                    clearable
                    style="width: 100%"
                  />
                </el-form-item>
                <a :href="getPricingLink()" target="_blank" class="pricing-link">
                  가격 정보 보기 →
                </a>
              </div>

              <el-form-item label="Temperature">
                <el-slider
                  v-model="formData.llm.temperature"
                  :min="0"
                  :max="2"
                  :step="0.1"
                  show-input
                />
                <div class="form-help">낮을수록 일관된 응답, 높을수록 창의적 응답 (0.0-2.0)</div>
              </el-form-item>

              <el-form-item label="최대 토큰">
                <el-input-number
                  v-model="formData.llm.max_tokens"
                  :min="100"
                  :max="8000"
                  :step="100"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- RAG 설정 -->
        <el-tab-pane label="RAG" name="rag">
          <div class="settings-section">
            <h3>RAG 검색 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="검색 문서 수 (Top-K)">
                <el-input-number
                  v-model="formData.rag.top_k"
                  :min="1"
                  :max="50"
                  style="width: 100%"
                />
                <div class="form-help">질문에 대해 검색할 유사 문서 수</div>
              </el-form-item>

              <el-form-item label="유사도 측정 방식">
                <el-select
                  v-model="formData.rag.distance_metric"
                  style="width: 100%"
                  disabled
                >
                  <el-option label="Cosine Distance (코사인 거리)" value="cosine" />
                </el-select>
                <div class="form-help">벡터 간 유사도를 측정하는 알고리즘 (텍스트 임베딩에 권장)</div>
              </el-form-item>

              <el-form-item label="유사도 임계값">
                <el-slider
                  v-model="formData.rag.similarity_threshold"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  show-input
                />
                <div class="form-help">이 값 이상의 유사도를 가진 문서만 반환 (0.0-1.0)</div>
              </el-form-item>

              <el-form-item label="최대 컨텍스트 길이">
                <el-input-number
                  v-model="formData.rag.max_context_length"
                  :min="1000"
                  :max="16000"
                  :step="500"
                  style="width: 100%"
                />
                <div class="form-help">LLM에 전달할 최대 컨텍스트 길이 (문자)</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- NL2SQL 설정 -->
        <el-tab-pane label="NL2SQL" name="nl2sql">
          <div class="settings-section">
            <h3>NL2SQL 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="SQL 실행 타임아웃 (초)">
                <el-input-number
                  v-model="formData.nl2sql.timeout_seconds"
                  :min="5"
                  :max="120"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="최대 반환 행 수">
                <el-input-number
                  v-model="formData.nl2sql.max_rows"
                  :min="100"
                  :max="10000"
                  :step="100"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="읽기 전용 모드">
                <el-switch v-model="formData.nl2sql.read_only_mode" />
                <span class="switch-label">{{ formData.nl2sql.read_only_mode ? '활성화' : '비활성화' }}</span>
                <div class="form-help">SELECT 쿼리만 허용 (보안상 권장)</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Agent 설정 -->
        <el-tab-pane label="Agent" name="agent">
          <div class="settings-section">
            <h3>AI Agent 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="Agent LLM 제공자">
                <el-select v-model="formData.agent.llm_provider" style="width: 100%">
                  <el-option label="OpenAI" value="openai" />
                  <el-option label="Anthropic (Claude)" value="anthropic" />
                </el-select>
                <div class="form-help">Agent 실행에 사용할 LLM 제공자를 선택하세요</div>
              </el-form-item>

              <el-form-item label="최대 반복 횟수">
                <el-input-number
                  v-model="formData.agent.max_iterations"
                  :min="3"
                  :max="30"
                  style="width: 100%"
                />
                <div class="form-help">Agent가 문제를 해결하기 위해 시도할 최대 반복 횟수</div>
              </el-form-item>

              <el-form-item label="실행 타임아웃 (초)">
                <el-input-number
                  v-model="formData.agent.timeout_seconds"
                  :min="30"
                  :max="300"
                  :step="10"
                  style="width: 100%"
                />
                <div class="form-help">Agent 전체 실행의 최대 대기 시간</div>
              </el-form-item>

              <el-form-item label="메모리 기능">
                <el-switch v-model="formData.agent.enable_memory" />
                <span class="switch-label">{{ formData.agent.enable_memory ? '활성화' : '비활성화' }}</span>
                <div class="form-help">멀티턴 대화를 위한 세션 메모리 사용</div>
              </el-form-item>

              <el-form-item label="사용 가능한 도구">
                <el-checkbox-group v-model="formData.agent.enabled_tools">
                  <el-checkbox label="query_database">DB 조회 (NL2SQL)</el-checkbox>
                  <el-checkbox label="search_documents">문서 검색 (RAG)</el-checkbox>
                  <el-checkbox label="calculate">계산기</el-checkbox>
                </el-checkbox-group>
                <div class="form-help">Agent가 사용할 수 있는 도구를 선택하세요</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 청킹 설정 -->
        <el-tab-pane label="청킹" name="chunking">
          <div class="settings-section">
            <h3>문서 청킹 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="기본 청크 크기 (문자)">
                <el-input-number
                  v-model="formData.chunking.default_chunk_size"
                  :min="100"
                  :max="5000"
                  :step="100"
                  style="width: 100%"
                />
                <div class="form-help">문서를 나눌 때 기본 청크 크기</div>
              </el-form-item>

              <el-form-item label="기본 오버랩 (문자)">
                <el-input-number
                  v-model="formData.chunking.default_overlap"
                  :min="0"
                  :max="500"
                  :step="10"
                  style="width: 100%"
                />
                <div class="form-help">청크 간 중복되는 문자 수 (문맥 유지용)</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- 저장 버튼 -->
      <div class="settings-actions">
        <el-button @click="resetCategory" :disabled="isSaving">
          기본값으로 초기화
        </el-button>
        <el-button type="primary" @click="saveSettings" :loading="isSaving">
          저장
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, View, Hide } from '@element-plus/icons-vue'
import settingsApi from '@/api/settings'

const activeTab = ref('openai')
const isLoading = ref(false)
const isSaving = ref(false)
const validating = ref(false)
const showApiKey = ref(false)
const showAnthropicApiKey = ref(false)
const apiKeyStatus = ref(null)

// 설정 데이터 (타입별로 구조화)
const formData = reactive({
  openai: {
    api_key: '',
    organization_id: ''
  },
  anthropic: {
    api_key: ''
  },
  embedding: {
    model: 'text-embedding-3-small',
    dimension: 1536
  },
  llm: {
    provider: 'openai',
    model: 'gpt-4-turbo-preview',
    temperature: 0.1,
    max_tokens: 2000
  },
  rag: {
    top_k: 10,
    distance_metric: 'cosine',
    similarity_threshold: 0.7,
    max_context_length: 4000
  },
  nl2sql: {
    timeout_seconds: 30,
    max_rows: 1000,
    read_only_mode: true
  },
  agent: {
    llm_provider: 'openai',
    max_iterations: 10,
    timeout_seconds: 60,
    enable_memory: true,
    enabled_tools: ['query_database', 'search_documents', 'calculate']
  },
  chunking: {
    default_chunk_size: 1000,
    default_overlap: 100
  }
})

// 원본 데이터 (변경 감지용)
const originalData = ref({})

// 설정 로드
const loadSettings = async () => {
  isLoading.value = true
  try {
    const response = await settingsApi.getAll()

    // 카테고리별로 데이터 매핑
    response.categories.forEach(cat => {
      if (formData[cat.category]) {
        cat.settings.forEach(setting => {
          let value = parseValue(setting.value, setting.value_type)

          // enabled_tools는 쉼표 구분 문자열을 배열로 변환
          if (cat.category === 'agent' && setting.key === 'enabled_tools' && typeof value === 'string') {
            value = value.split(',').map(t => t.trim()).filter(t => t)
          }

          formData[cat.category][setting.key] = value
        })
      }
    })

    // 원본 데이터 저장
    originalData.value = JSON.parse(JSON.stringify(formData))

    ElMessage.success('설정을 불러왔습니다.')
  } catch (error) {
    console.error('설정 로드 실패:', error)
    ElMessage.error('설정을 불러오는데 실패했습니다.')
  } finally {
    isLoading.value = false
  }
}

// 값 파싱 (타입에 따라)
const parseValue = (value, valueType) => {
  switch (valueType) {
    case 'int':
      return parseInt(value, 10)
    case 'float':
      return parseFloat(value)
    case 'bool':
      return value === 'true' || value === true
    default:
      return value
  }
}

// 값을 문자열로 변환
const stringifyValue = (value) => {
  if (typeof value === 'boolean') {
    return value ? 'true' : 'false'
  }
  return String(value)
}

// 설정 저장
const saveSettings = async () => {
  isSaving.value = true
  try {
    const category = activeTab.value
    const settings = {}

    // 현재 탭의 설정을 문자열로 변환
    Object.entries(formData[category]).forEach(([key, value]) => {
      // enabled_tools는 배열을 쉼표 구분 문자열로 변환
      if (category === 'agent' && key === 'enabled_tools' && Array.isArray(value)) {
        settings[key] = value.join(',')
      } else {
        settings[key] = stringifyValue(value)
      }
    })

    await settingsApi.updateCategory(category, settings)

    // 원본 데이터 업데이트
    originalData.value[category] = JSON.parse(JSON.stringify(formData[category]))

    ElMessage.success('설정이 저장되었습니다.')
  } catch (error) {
    console.error('설정 저장 실패:', error)
    ElMessage.error('설정 저장에 실패했습니다.')
  } finally {
    isSaving.value = false
  }
}

// 카테고리 초기화
const resetCategory = async () => {
  try {
    await ElMessageBox.confirm(
      `${activeTab.value} 설정을 기본값으로 초기화하시겠습니까?`,
      '설정 초기화',
      {
        confirmButtonText: '초기화',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    await settingsApi.resetCategory(activeTab.value)
    await loadSettings()
    ElMessage.success('설정이 초기화되었습니다.')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('설정 초기화 실패:', error)
      ElMessage.error('설정 초기화에 실패했습니다.')
    }
  }
}

// API 키 검증
const validateApiKey = async () => {
  const apiKey = formData.openai.api_key
  if (!apiKey || apiKey.includes('*')) {
    ElMessage.warning('API 키를 입력해주세요.')
    return
  }

  validating.value = true
  apiKeyStatus.value = null

  try {
    const response = await settingsApi.validateApiKey(apiKey)
    apiKeyStatus.value = response

    if (response.valid) {
      ElMessage.success('API 키가 유효합니다.')
    } else {
      ElMessage.error(response.message)
    }
  } catch (error) {
    console.error('API 키 검증 실패:', error)
    apiKeyStatus.value = { valid: false, message: '검증 중 오류가 발생했습니다.' }
  } finally {
    validating.value = false
  }
}

// 탭 변경 시 저장 여부 확인
const handleTabChange = () => {
  // 탭 변경 시 추가 로직이 필요하면 여기에
}

// 모델별 기본 차원 매핑
const MODEL_DIMENSIONS = {
  'text-embedding-3-small': 1536,
  'text-embedding-3-large': 3072,
  'text-embedding-ada-002': 1536
}

// 임베딩 모델 변경 시 차원 자동 설정
const onEmbeddingModelChange = (model) => {
  const dimension = MODEL_DIMENSIONS[model] || 1536
  formData.embedding.dimension = dimension

  // 3072 차원 모델 선택 시 경고
  if (dimension !== 1536) {
    ElMessageBox.alert(
      `선택한 모델(${model})은 ${dimension} 차원을 사용합니다.\n` +
      '현재 DB 스키마는 1536 차원으로 설정되어 있어 호환되지 않습니다.\n\n' +
      'DB 스키마를 수정하거나 1536 차원 모델을 사용해주세요.',
      '차원 불일치 경고',
      {
        confirmButtonText: '확인',
        type: 'warning'
      }
    )
  }
}

// LLM 제공자별 모델 placeholder
const getLLMModelPlaceholder = () => {
  const provider = formData.llm.provider
  if (provider === 'anthropic') {
    return 'claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-sonnet-20240229'
  }
  return 'gpt-4o, gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo'
}

// LLM 제공자별 가격 정보 링크
const getPricingLink = () => {
  const provider = formData.llm.provider
  if (provider === 'anthropic') {
    return 'https://www.anthropic.com/pricing#anthropic-api'
  }
  return 'https://platform.openai.com/docs/pricing'
}

// LLM 제공자 변경 시 처리
const onLLMProviderChange = (provider) => {
  // 제공자 변경 시 모델 필드 초기화 (사용자가 직접 입력하도록)
  if (provider === 'anthropic' && formData.llm.model.startsWith('gpt-')) {
    formData.llm.model = ''
  } else if (provider === 'openai' && formData.llm.model.startsWith('claude-')) {
    formData.llm.model = ''
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style lang="scss" scoped>
.settings-view {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .settings-section {
    padding: 20px 0;

    h3 {
      margin: 0 0 20px;
      font-size: 16px;
      font-weight: 500;
      color: var(--text-color-primary);
    }
  }

  .settings-form {
    max-width: 600px;

    .el-form-item {
      margin-bottom: 24px;
    }

    // OpenAI 설정 폼은 더 넓게
    &.openai-form {
      max-width: 800px;
    }
  }

  // API Key 입력 필드 - 넓게
  .api-key-field {
    min-width: 600px;

    :deep(.el-input__inner) {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 14px;
      letter-spacing: 0.5px;
    }
  }

  // Organization ID 필드도 동일하게
  .org-id-field {
    width: 700px;

    :deep(.el-input__inner) {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 14px;
    }
  }

  .api-key-input {
    display: flex;
    gap: 12px;

    .el-input {
      flex: 1;
    }
  }

  .validation-status {
    margin-top: 8px;
    font-size: 13px;

    &.success {
      color: #67c23a;
    }

    &.error {
      color: #f56c6c;
    }
  }

  .form-help {
    margin-top: 4px;
    font-size: 12px;
    color: var(--text-color-secondary);
  }

  .switch-label {
    margin-left: 8px;
    font-size: 14px;
    color: var(--text-color-regular);
  }

  .settings-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color-light);
    margin-top: 20px;
  }

  .cursor-pointer {
    cursor: pointer;
  }

  // LLM 모델 선택 관련 스타일
  .form-item-with-link {
    position: relative;

    .pricing-link {
      position: absolute;
      top: 0;
      right: 0;
      font-size: 12px;
      color: var(--el-color-primary);
      text-decoration: none;
      font-weight: normal;

      &:hover {
        text-decoration: underline;
      }
    }
  }
}
</style>

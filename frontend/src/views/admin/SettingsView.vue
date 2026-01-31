<template>
  <div class="settings-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>시스템 설정</h2>
        <p class="subtitle">API, 모델, 검색 파라미터 등을 설정합니다.</p>
      </div>
    </div>

    <!-- 설정 탭 -->
    <div class="content-card">
      <el-tabs v-model="activeTab">
        <!-- API 키 관리 (OpenAI + Anthropic 통합) -->
        <el-tab-pane label="API 키 관리" name="api_keys">
          <div class="settings-section">
            <h3>API 키 관리</h3>
            <p class="section-desc">LLM 제공자별 API 키를 설정합니다.</p>

            <el-form label-position="top" class="settings-form">
              <!-- OpenAI API Key -->
              <div class="api-key-section">
                <h4 class="provider-title">
                  <span>OpenAI</span>
                  <el-tag size="small" type="success">Primary</el-tag>
                </h4>

                <el-form-item label="API Key">
                  <el-input
                    v-model="formData.openai.api_key"
                    :type="showApiKey ? 'text' : 'password'"
                    placeholder="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    class="api-key-field"
                  >
                    <template #suffix>
                      <el-icon class="cursor-pointer" @click="toggleApiKeyVisibility('openai')">
                        <View v-if="!showApiKey" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    OpenAI GPT 모델 및 임베딩 사용을 위한 API 키
                    <a href="https://platform.openai.com/api-keys" target="_blank">API 키 발급받기 →</a>
                  </div>
                </el-form-item>

                <el-form-item label="Organization ID (선택)" v-if="false">
                  <el-input
                    v-model="formData.openai.organization_id"
                    placeholder="org-xxxxxxxxxxxxxxxxxxxxxxxx"
                    clearable
                    style="max-width: 500px"
                  />
                </el-form-item>
              </div>

              <!-- Anthropic API Key -->
              <div class="api-key-section">
                <h4 class="provider-title">
                  <span>Anthropic (Claude)</span>
                  <el-tag size="small" type="info">Optional</el-tag>
                </h4>

                <el-form-item label="API Key">
                  <el-input
                    v-model="formData.anthropic.api_key"
                    :type="showAnthropicApiKey ? 'text' : 'password'"
                    placeholder="sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    class="api-key-field"
                  >
                    <template #suffix>
                      <el-icon class="cursor-pointer" @click="toggleApiKeyVisibility('anthropic')">
                        <View v-if="!showAnthropicApiKey" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    Anthropic Claude 모델 사용을 위한 API 키
                    <a href="https://console.anthropic.com/settings/keys" target="_blank">API 키 발급받기 →</a>
                  </div>
                </el-form-item>
              </div>

              <!-- Google API Key -->
              <div class="api-key-section">
                <h4 class="provider-title">
                  <span>Google (Gemini)</span>
                  <el-tag size="small" type="info">Optional</el-tag>
                </h4>

                <el-form-item label="API Key">
                  <el-input
                    v-model="formData.google.api_key"
                    :type="showGoogleApiKey ? 'text' : 'password'"
                    placeholder="AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    class="api-key-field"
                  >
                    <template #suffix>
                      <el-icon class="cursor-pointer" @click="toggleApiKeyVisibility('google')">
                        <View v-if="!showGoogleApiKey" />
                        <Hide v-else />
                      </el-icon>
                    </template>
                  </el-input>
                  <div class="form-help">
                    Google Gemini 모델 사용을 위한 API 키
                    <a href="https://aistudio.google.com/app/apikey" target="_blank">API 키 발급받기 →</a>
                  </div>
                </el-form-item>
              </div>

            </el-form>

          </div>
        </el-tab-pane>

        <!-- LLM 설정 -->
        <el-tab-pane label="LLM" name="llm">
          <div class="settings-section">
            <h3>LLM 모델 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="LLM 제공자">
                <el-select
                  v-model="formData.llm.provider"
                  style="width: 100%"
                  @change="onLLMProviderChange"
                  :loading="llmProvidersLoading"
                >
                  <el-option
                    v-for="provider in llmProviders"
                    :key="provider.code_value"
                    :label="provider.code_name"
                    :value="provider.code_value"
                  />
                </el-select>
                <div class="form-help">LLM 서비스 제공자를 선택하세요</div>
              </el-form-item>

              <div class="form-item-with-link">
                <el-form-item label="LLM 모델">
                  <el-select
                    v-model="formData.llm.model"
                    style="width: 100%"
                    :loading="llmModelsLoading"
                    filterable
                    allow-create
                    placeholder="모델을 선택하거나 직접 입력"
                  >
                    <el-option
                      v-for="model in currentLLMModels"
                      :key="model.code_value"
                      :label="model.code_name"
                      :value="model.code_value"
                    />
                  </el-select>
                </el-form-item>
                <a v-if="false" :href="getPricingLink()" target="_blank" class="pricing-link">
                  가격 정보 보기 →
                </a>
              </div>

              <el-form-item label="Temperature">
                <el-slider
                  v-model="formData.llm.temperature"
                  :min="0"
                  :max="temperatureMax"
                  :step="0.1"
                  show-input
                />
                <div class="form-help">{{ temperatureHelpText }}</div>
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

              <!-- GPT-5 계열 모델인 경우에만 Reasoning Effort 표시 -->
              <el-form-item v-if="isGPT5Model" label="Reasoning Effort (추론 강도)">
                <el-select
                  v-model="formData.llm.reasoning_effort"
                  style="width: 100%"
                >
                  <el-option
                    v-for="option in reasoningEffortOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
                <div class="form-help">
                  GPT-5 계열 모델의 추론 강도를 설정합니다. 높을수록 더 깊은 추론을 수행하지만 응답 시간이 증가합니다.
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- RAG 설정 (청킹 + 임베딩 + RAG 통합) -->
        <el-tab-pane label="RAG 설정" name="rag">
          <div class="settings-section">
            <h3>RAG 문서 검색 설정</h3>
            <p class="section-desc">
              문서 전처리부터 검색까지 전 과정을 설정합니다. 청킹/임베딩 설정 변경 시 문서를 재임베딩해야 적용됩니다.
            </p>

            <el-form label-position="top" class="settings-form">
              <!-- 섹션 1: 청킹 -->
              <div class="setting-section">
                <h4 class="section-title">
                  <el-icon><Edit /></el-icon>
                  1단계: 문서 청킹 (전처리)
                  <el-tag size="small" type="warning">재임베딩 필요</el-tag>
                </h4>
                <p class="section-desc">긴 문서를 작은 조각으로 나누는 방법을 설정합니다.</p>

                <el-form-item label="청크 크기 (문자)">
                  <el-input-number
                    v-model="formData.chunking.default_chunk_size"
                    :min="100"
                    :max="5000"
                    :step="100"
                    style="width: 100%"
                  />
                  <div class="form-help">문서를 나눌 때 기본 청크 크기</div>
                </el-form-item>

                <el-form-item label="오버랩 (문자)">
                  <el-input-number
                    v-model="formData.chunking.default_overlap"
                    :min="0"
                    :max="500"
                    :step="10"
                    style="width: 100%"
                  />
                  <div class="form-help">청크 간 중복되는 문자 수 (문맥 유지용)</div>
                </el-form-item>
              </div>

              <el-divider />

              <!-- 섹션 2: 임베딩 -->
              <div class="setting-section">
                <h4 class="section-title">
                  <el-icon><Connection /></el-icon>
                  2단계: 벡터 임베딩
                  <el-tag size="small" type="warning">재임베딩 필요</el-tag>
                </h4>
                <p class="section-desc">텍스트를 벡터로 변환하는 모델을 설정합니다.</p>

                <el-form-item label="임베딩 모델">
                  <el-select
                    v-model="formData.embedding.model"
                    style="width: 100%"
                    @change="onEmbeddingModelChange"
                    :loading="embeddingModelsLoading"
                  >
                    <el-option
                      v-for="model in embeddingModels"
                      :key="model.code_value"
                      :label="model.code_name"
                      :value="model.code_value"
                    />
                  </el-select>
                  <div class="form-help">
                    문서 임베딩에 사용할 OpenAI 모델을 선택하세요
                  </div>
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
              </div>

              <el-divider />

              <!-- 섹션 3: RAG 검색 -->
              <div class="setting-section">
                <h4 class="section-title">
                  <el-icon><Search /></el-icon>
                  3단계: RAG 검색 파라미터
                  <el-tag size="small" type="success">즉시 적용</el-tag>
                </h4>
                <p class="section-desc">사용자 질문과 유사한 문서를 찾는 방법을 설정합니다.</p>

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
                  >
                    <el-option label="Cosine Distance (코사인 거리)" value="cosine" />
                    <el-option label="L2 Distance (유클리드 거리)" value="l2" />
                  </el-select>
                  <div class="form-help">벡터 간 유사도를 측정하는 알고리즘 (텍스트 임베딩에는 코사인 거리 권장)</div>
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
              </div>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- NL2SQL 설정 -->
        <el-tab-pane label="NL2SQL" name="nl2sql">
          <div class="settings-section">
            <h3>NL2SQL 실행 설정</h3>
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

            <!-- 외부 비즈니스 데이터베이스 연결 설정 -->
            <el-divider />
            <h3>비즈니스 데이터베이스 연결</h3>
            <p class="section-desc">
              NL2SQL이 쿼리할 외부 데이터베이스를 설정합니다. <br>
              비활성화하면 로컬 business 스키마를 사용합니다.
            </p>

            <el-form label-position="top" class="settings-form">
              <el-form-item label="외부 DB 사용">
                <el-switch v-model="formData.external_database.enabled" />
                <span class="switch-label">{{ formData.external_database.enabled ? '활성화' : '비활성화' }}</span>
                <div class="form-help">
                  외부 DB 연결 사용 여부 (비활성화 시 로컬 DB의 business 스키마 사용)
                </div>
              </el-form-item>

              <template v-if="formData.external_database.enabled">
                <el-form-item label="DB 타입">
                  <el-select v-model="formData.external_database.db_type" style="width: 100%" @change="onDbTypeChange">
                    <el-option label="PostgreSQL" value="postgresql" />
                    <el-option label="Oracle" value="oracle" />
                    <el-option label="MySQL" value="mysql" disabled />
                    <!-- <el-option label="MS SQL Server" value="mssql" disabled /> -->
                  </el-select>
                  <div class="form-help">
                    PostgreSQL 및 Oracle을 지원합니다
                  </div>
                </el-form-item>

                <el-row :gutter="20">
                  <el-col :span="16">
                    <el-form-item label="호스트">
                      <el-input
                        v-model="formData.external_database.host"
                        placeholder="localhost"
                      />
                    </el-form-item>
                  </el-col>
                  <el-col :span="8">
                    <el-form-item label="포트">
                      <el-input-number
                        v-model="formData.external_database.port"
                        :min="1"
                        :max="65535"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item :label="formData.external_database.db_type === 'oracle' ? 'Service Name (SID)' : '데이터베이스 이름'">
                  <el-input
                    v-model="formData.external_database.database"
                    :placeholder="formData.external_database.db_type === 'oracle' ? 'ORCL' : 'chatbot_system'"
                  />
                  <div v-if="formData.external_database.db_type === 'oracle'" class="form-help">
                    Oracle Service Name 또는 SID를 입력하세요
                  </div>
                </el-form-item>

                <el-form-item :label="formData.external_database.db_type === 'oracle' ? '스키마 (Owner)' : '스키마'">
                  <el-input
                    v-model="formData.external_database.schema"
                    :placeholder="formData.external_database.db_type === 'oracle' ? 'HR' : 'business'"
                  />
                  <div class="form-help">
                    {{ formData.external_database.db_type === 'oracle'
                      ? 'Oracle에서는 CURRENT_SCHEMA로 설정됩니다 (대문자 권장)'
                      : '비즈니스 데이터가 저장된 스키마 이름' }}
                  </div>
                </el-form-item>

                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-form-item label="사용자명">
                      <el-input v-model="formData.external_database.username" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="비밀번호">
                      <el-input
                        v-model="formData.external_database.password"
                        type="password"
                        show-password
                      />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="허용 테이블 (쉼표 구분)">
                  <el-input
                    v-model="formData.external_database.allowed_tables"
                    type="textarea"
                    :rows="3"
                    placeholder="employee, department, salary, job_history, performance_review"
                  />
                  <div class="form-help">
                    <el-icon><Warning /></el-icon>
                    NL2SQL이 쿼리할 수 있는 테이블만 입력하세요. 보안상 매우 중요합니다!
                  </div>
                </el-form-item>

                <el-form-item label="연결 풀 크기">
                  <el-input-number
                    v-model="formData.external_database.connection_pool_size"
                    :min="1"
                    :max="20"
                    style="width: 100%"
                  />
                  <div class="form-help">
                    동시 접속 처리를 위한 연결 풀 크기
                  </div>
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="success"
                    @click="testExternalConnection"
                    :loading="testingConnection"
                  >
                    연결 테스트
                  </el-button>
                  <span
                    v-if="externalConnectionStatus"
                    :class="externalConnectionStatus.success ? 'text-success' : 'text-error'"
                    style="margin-left: 12px;"
                  >
                    {{ externalConnectionStatus.message }}
                  </span>
                </el-form-item>
              </template>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Agent 설정 - 추후 사용 예정 -->
        <el-tab-pane v-if="false" label="Agent" name="agent">
          <div class="settings-section">
            <h3>AI Agent 설정</h3>
            <el-form label-position="top" class="settings-form">
              <el-form-item label="Agent LLM 제공자">
                <el-select
                  v-model="formData.agent.llm_provider"
                  style="width: 100%"
                  :loading="llmProvidersLoading"
                >
                  <el-option
                    v-for="provider in llmProviders"
                    :key="provider.code_value"
                    :label="provider.code_name"
                    :value="provider.code_value"
                  />
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
                <el-checkbox-group v-model="formData.agent.enabled_tools" class="tool-checkbox-group">
                  <el-checkbox label="query_database_tool">DB 조회 (SQL 실행)</el-checkbox>
                  <el-checkbox label="search_documents_tool">문서 검색 (정책/규정)</el-checkbox>
                  <el-checkbox label="calculate_tool">계산기</el-checkbox>
                </el-checkbox-group>
                <div class="form-help">
                  Agent가 사용할 수 있는 도구를 선택하세요.<br>
                  <small>※ SQL 컨텍스트(스키마/예제/용어)는 자동으로 주입됩니다</small>
                </div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 프롬프트 설정 -->
        <el-tab-pane label="프롬프트" name="prompt">
          <div class="settings-section">
            <h3>시스템 프롬프트 관리</h3>
            <p class="section-desc">
              LLM과의 상호작용에 사용되는 시스템 프롬프트를 관리합니다.
              프롬프트 변경 시 모든 변경 이력이 자동으로 저장되며, 언제든지 이전 버전으로 원복할 수 있습니다.
            </p>

            <!-- RAG 프롬프트 -->
            <el-divider content-position="left">
              <span style="font-weight: 600;">RAG (문서 검색)</span>
            </el-divider>

            <el-form label-position="top" class="settings-form">
              <el-form-item label="RAG 시스템 프롬프트">
                <el-input
                  v-model="formData.prompt.rag_system_prompt"
                  type="textarea"
                  :rows="12"
                  placeholder="문서 검색 후 답변 생성 시 사용되는 시스템 프롬프트"
                  class="prompt-textarea"
                />
                <div class="form-help">
                  문서 검색 후 답변 생성 시 사용됩니다.
                  <el-button text type="primary" size="small" @click="showPromptPreview('rag_system_prompt')">
                  <!--  프리뷰 -->
                  </el-button>
                </div>
              </el-form-item>

              <el-form-item label="RAG 페르소나">
                <el-input
                  v-model="formData.prompt.rag_persona"
                  placeholder="예: 기업용 지식 베이스 전문가"
                  style="max-width: 500px"
                />
                <div class="form-help">RAG 시스템의 역할 정의</div>
              </el-form-item>
            </el-form>

            <!-- NL2SQL 프롬프트 -->
            <el-divider content-position="left">
              <span style="font-weight: 600;">NL2SQL (자연어 → SQL)</span>
            </el-divider>

            <el-form label-position="top" class="settings-form">
              <el-form-item label="SQL 생성 프롬프트">
                <el-input
                  v-model="formData.prompt.nl2sql_generation_prompt"
                  type="textarea"
                  :rows="15"
                  placeholder="자연어를 SQL 쿼리로 변환하는 프롬프트"
                  class="prompt-textarea"
                />
                <div class="form-help">
                  <el-icon><Warning /></el-icon>
                  {schema_description} 변수는 자동으로 DB 스키마로 치환됩니다.
                  <el-button text type="primary" size="small" @click="showPromptPreview('nl2sql_generation_prompt')">
                   <!--  프리뷰 -->
                  </el-button>
                </div>
              </el-form-item>

              <el-form-item label="답변 생성 프롬프트">
                <el-input
                  v-model="formData.prompt.nl2sql_answer_prompt"
                  type="textarea"
                  :rows="8"
                  placeholder="SQL 결과를 자연어로 변환하는 프롬프트"
                  class="prompt-textarea"
                />
                <div class="form-help">SQL 실행 결과를 사용자가 이해하기 쉽게 자연어로 변환합니다.</div>
              </el-form-item>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="SQL 생성 페르소나">
                    <el-input
                      v-model="formData.prompt.nl2sql_sql_persona"
                      placeholder="예: PostgreSQL 전문가"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="답변 생성 페르소나">
                    <el-input
                      v-model="formData.prompt.nl2sql_answer_persona"
                      placeholder="예: 데이터 분석 전문가"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>

            <!-- Agent 프롬프트 - 추후 사용 예정 -->
            <template v-if="false">
              <el-divider content-position="left">
                <span style="font-weight: 600;">Agent (도구 선택)</span>
              </el-divider>

              <el-form label-position="top" class="settings-form">
                <el-form-item label="Agent 시스템 프롬프트">
                  <el-input
                    v-model="formData.prompt.agent_system_prompt"
                    type="textarea"
                    :rows="15"
                    placeholder="Agent의 기본 동작 지침 및 도구 선택 규칙"
                    class="prompt-textarea"
                  />
                  <div class="form-help">
                    ReAct 패턴 기반 도구 선택 및 실행 시 사용됩니다.
                    <el-button text type="primary" size="small" @click="showPromptPreview('agent_system_prompt')">
                      프리뷰
                    </el-button>
                  </div>
                </el-form-item>

                <el-form-item label="Agent 페르소나">
                  <el-input
                    v-model="formData.prompt.agent_persona"
                    placeholder="예: AI assistant for corporate knowledge base"
                    style="max-width: 500px"
                  />
                </el-form-item>
              </el-form>
            </template>

            <!-- Tool 설명 - 추후 사용 예정 (현재 Tool docstring은 코드에 하드코딩됨) -->
            <template v-if="false">
              <el-divider content-position="left">
                <span style="font-weight: 600;">Tool 설명 (Agent 도구 선택 시 참조)</span>
              </el-divider>

              <el-form label-position="top" class="settings-form">
                <el-form-item label="SQL Tool 설명">
                  <el-input
                    v-model="formData.prompt.tool_sql_description"
                    type="textarea"
                    :rows="8"
                    placeholder="SQL Tool 설명"
                    class="prompt-textarea"
                  />
                  <div class="form-help">Agent가 SQL Tool을 선택할 때 참조하는 설명</div>
                </el-form-item>

                <el-form-item label="RAG Tool 설명">
                  <el-input
                    v-model="formData.prompt.tool_rag_description"
                    type="textarea"
                    :rows="8"
                    placeholder="RAG Tool 설명"
                    class="prompt-textarea"
                  />
                  <div class="form-help">Agent가 RAG Tool을 선택할 때 참조하는 설명</div>
                </el-form-item>

                <el-form-item label="Calculator Tool 설명">
                  <el-input
                    v-model="formData.prompt.tool_calculator_description"
                    type="textarea"
                    :rows="8"
                    placeholder="Calculator Tool 설명"
                    class="prompt-textarea"
                  />
                  <div class="form-help">Agent가 Calculator Tool을 선택할 때 참조하는 설명</div>
                </el-form-item>
              </el-form>
            </template>

            <!-- 프롬프트 관리 도구 -->
            <el-divider />
            <div class="prompt-actions">
              <el-button @click="showPromptHistory">
                <el-icon><Clock /></el-icon>
                변경 이력 보기
              </el-button>
              <el-button @click="exportPrompts">
                <el-icon><Download /></el-icon>
                내보내기
              </el-button>
              <el-button @click="importPrompts">
                <el-icon><Upload /></el-icon>
                가져오기
              </el-button>
            </div>
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

    <!-- 프롬프트 프리뷰 다이얼로그 -->
    <el-dialog
      v-model="promptPreviewVisible"
      :title="promptPreviewData.title"
      width="800px"
    >
      <div class="prompt-preview">
        <pre>{{ promptPreviewData.content }}</pre>
      </div>
      <template #footer>
        <el-button @click="promptPreviewVisible = false">닫기</el-button>
      </template>
    </el-dialog>

    <!-- 프롬프트 이력 다이얼로그 -->
    <el-dialog
      v-model="promptHistoryVisible"
      title="프롬프트 변경 이력"
      width="900px"
    >
      <el-table
        v-loading="promptHistoryLoading"
        :data="promptHistoryData"
        empty-text="변경 이력이 없습니다"
      >
        <el-table-column prop="key" label="프롬프트" width="200" />
        <el-table-column prop="changed_at" label="변경 일시" width="180">
          <template #default="scope">
            {{ new Date(scope.row.changed_at).toLocaleString('ko-KR') }}
          </template>
        </el-table-column>
        <el-table-column prop="changed_by" label="변경자" width="120" />
        <el-table-column prop="change_reason" label="변경 사유" min-width="150" />
        <el-table-column label="작업" width="100" align="center">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              text
              @click="restorePrompt(scope.row)"
            >
              복원
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="promptHistoryVisible = false">닫기</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Hide, Warning, Clock, Download, Upload, Edit, Connection, Search } from '@element-plus/icons-vue'
import settingsApi from '@/api/settings'
import codesApi from '@/api/codes'

const activeTab = ref('api_keys')
const isLoading = ref(false)
const isSaving = ref(false)
const showApiKey = ref(false)
const showAnthropicApiKey = ref(false)
const showGoogleApiKey = ref(false)
const testingConnection = ref(false)
const externalConnectionStatus = ref(null)

// 원본 API 키 저장 (reveal용)
const originalApiKeys = reactive({
  openai: '',
  anthropic: '',
  google: ''
})

// 코드 관리 (Phase C-2)
const embeddingModels = ref([])
const llmProviders = ref([])
const llmModelsOpenAI = ref([])
const llmModelsAnthropic = ref([])
const llmModelsGoogle = ref([])
const embeddingModelsLoading = ref(false)
const llmProvidersLoading = ref(false)
const llmModelsLoading = ref(false)

// 설정 데이터 (타입별로 구조화)
const formData = reactive({
  openai: {
    api_key: '',
    organization_id: ''
  },
  anthropic: {
    api_key: ''
  },
  google: {
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
    max_tokens: 2000,
    reasoning_effort: 'medium'
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
  external_database: {
    enabled: true,
    db_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: 'chatbot_system',
    username: 'postgres',
    password: '',
    schema: 'business',
    allowed_tables: 'employee,department,job_history,performance_review,salary',
    connection_pool_size: 5,
    connection_timeout: 10
  },
  agent: {
    llm_provider: 'openai',
    max_iterations: 10,
    timeout_seconds: 60,
    enable_memory: true,
    enabled_tools: ['query_database_tool', 'search_documents_tool', 'calculate_tool']
  },
  chunking: {
    default_chunk_size: 1000,
    default_overlap: 100
  },
  prompt: {
    rag_system_prompt: '',
    rag_persona: '',
    nl2sql_generation_prompt: '',
    nl2sql_answer_prompt: '',
    nl2sql_sql_persona: '',
    nl2sql_answer_persona: '',
    agent_system_prompt: '',
    agent_persona: '',
    tool_sql_description: '',
    tool_rag_description: '',
    tool_calculator_description: ''
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

            // 구 형식을 신 형식으로 자동 마이그레이션 (_tool 접미사 추가)
            const toolMapping = {
              'query_database': 'query_database_tool',
              'search_documents': 'search_documents_tool',
              'calculate': 'calculate_tool'
            }
            // context_search_tool은 더 이상 사용하지 않음 (자동 주입으로 대체)
            value = value.map(tool => toolMapping[tool] || tool).filter(t => t !== 'context_search_tool' && t !== 'context_search')
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

    // 탭별로 저장할 카테고리 결정
    // API 키 탭: openai + anthropic
    // NL2SQL 탭: nl2sql + external_database
    // RAG 탭: rag + embedding + chunking
    const categoriesToSave = category === 'api_keys'
      ? ['openai', 'anthropic', 'google']
      : category === 'nl2sql'
        ? ['nl2sql', 'external_database']
        : category === 'rag'
          ? ['rag', 'embedding', 'chunking']
          : [category]

    for (const cat of categoriesToSave) {
      const settings = {}

      // 현재 카테고리의 설정을 문자열로 변환
      Object.entries(formData[cat]).forEach(([key, value]) => {
        // enabled_tools는 배열을 쉼표 구분 문자열로 변환
        if (cat === 'agent' && key === 'enabled_tools' && Array.isArray(value)) {
          settings[key] = value.join(',')
        } else {
          settings[key] = stringifyValue(value)
        }
      })

      await settingsApi.updateCategory(cat, settings)

      // 원본 데이터 업데이트
      originalData.value[cat] = JSON.parse(JSON.stringify(formData[cat]))
    }

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

// LLM 제공자별 가격 정보 링크
const getPricingLink = () => {
  const provider = formData.llm.provider
  const pricingLinks = {
    openai: 'https://platform.openai.com/docs/pricing',
    anthropic: 'https://www.anthropic.com/pricing',
    google: 'https://ai.google.dev/gemini-api/docs/pricing'
  }
  return pricingLinks[provider] || pricingLinks.openai
}

// 현재 provider에 따른 LLM 모델 목록 (Phase C-2)
const currentLLMModels = computed(() => {
  const provider = formData.llm.provider
  if (provider === 'anthropic') {
    return llmModelsAnthropic.value
  } else if (provider === 'google') {
    return llmModelsGoogle.value
  }
  return llmModelsOpenAI.value
})

// Provider에 따른 Temperature 최대값 (OpenAI: 0-2, Anthropic: 0-1)
const temperatureMax = computed(() => {
  return formData.llm.provider === 'anthropic' ? 1 : 2
})

// Provider에 따른 Temperature 도움말 텍스트
const temperatureHelpText = computed(() => {
  const max = temperatureMax.value
  return `낮을수록 일관된 응답, 높을수록 창의적 응답 (0.0-${max.toFixed(1)})`
})

// GPT-5 계열 모델 여부 확인 (reasoning_effort 지원)
const isGPT5Model = computed(() => {
  const model = formData.llm.model?.toLowerCase() || ''
  return model.startsWith('gpt-5') || model.startsWith('gpt-5-mini') || model.startsWith('gpt-5-nano')
})

// reasoning_effort 옵션 목록
const reasoningEffortOptions = [
  { value: 'none', label: 'None (추론 비활성화)' },
  { value: 'minimal', label: 'Minimal (최소 추론)' },
  { value: 'low', label: 'Low (낮은 추론)' },
  { value: 'medium', label: 'Medium (중간 추론, 권장)' },
  { value: 'high', label: 'High (높은 추론)' }
]

// 코드 마스터에서 LLM 제공자 목록 로드
const loadLLMProviders = async () => {
  llmProvidersLoading.value = true
  try {
    const response = await codesApi.getByGroup('LLM_PROVIDER', false)
    llmProviders.value = response.codes
  } catch (error) {
    console.error('LLM 제공자 목록 로드 실패:', error)
    // 실패 시 빈 배열 유지 (하위 호환성)
  } finally {
    llmProvidersLoading.value = false
  }
}

// 코드 마스터에서 모델 목록 로드 (Phase C-2)
const loadEmbeddingModels = async () => {
  embeddingModelsLoading.value = true
  try {
    const response = await codesApi.getByGroup('EMBEDDING_MODEL', false)
    embeddingModels.value = response.codes
  } catch (error) {
    console.error('임베딩 모델 목록 로드 실패:', error)
    // 실패 시 빈 배열 유지 (하위 호환성)
  } finally {
    embeddingModelsLoading.value = false
  }
}

const loadLLMModels = async () => {
  llmModelsLoading.value = true
  try {
    const [openaiRes, anthropicRes, googleRes] = await Promise.all([
      codesApi.getByGroup('LLM_MODEL_OPENAI', false),
      codesApi.getByGroup('LLM_MODEL_ANTHROPIC', false),
      codesApi.getByGroup('LLM_MODEL_GOOGLE', false)
    ])
    llmModelsOpenAI.value = openaiRes.codes
    llmModelsAnthropic.value = anthropicRes.codes
    llmModelsGoogle.value = googleRes.codes
  } catch (error) {
    console.error('LLM 모델 목록 로드 실패:', error)
    // 실패 시 빈 배열 유지 (하위 호환성)
  } finally {
    llmModelsLoading.value = false
  }
}

// 임베딩 모델 변경 시 dimension 자동 설정 (Phase C-2)
const onEmbeddingModelChange = (modelValue) => {
  const selectedModel = embeddingModels.value.find(m => m.code_value === modelValue)
  if (selectedModel && selectedModel.metadata && selectedModel.metadata.dimension) {
    const dimension = selectedModel.metadata.dimension
    formData.embedding.dimension = dimension

    // 3072 차원 모델 선택 시 경고
    if (dimension !== 1536) {
      ElMessageBox.alert(
        `선택한 모델(${selectedModel.code_name})은 ${dimension} 차원을 사용합니다.\n` +
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
}

// LLM 제공자 변경 시 처리
const onLLMProviderChange = (provider) => {
  // 제공자 변경 시 모델 필드 초기화 (사용자가 직접 입력하도록)
  const currentModel = formData.llm.model
  if (provider === 'anthropic' && (currentModel.startsWith('gpt-') || currentModel.startsWith('gemini-'))) {
    formData.llm.model = ''
  } else if (provider === 'openai' && (currentModel.startsWith('claude-') || currentModel.startsWith('gemini-'))) {
    formData.llm.model = ''
  } else if (provider === 'google' && (currentModel.startsWith('gpt-') || currentModel.startsWith('claude-'))) {
    formData.llm.model = ''
  }

  // Temperature 최대값 조정 (Anthropic: 0-1, OpenAI/Google: 0-2)
  const maxTemp = provider === 'anthropic' ? 1 : 2
  if (formData.llm.temperature > maxTemp) {
    formData.llm.temperature = maxTemp
  }
}

// DB 타입 변경 시 처리
const onDbTypeChange = (dbType) => {
  // DB 타입에 따른 기본 포트 설정
  if (dbType === 'oracle') {
    formData.external_database.port = 1521
  } else if (dbType === 'postgresql') {
    formData.external_database.port = 5432
  }
}

// API 키 표시 상태 매핑
const apiKeyVisibilityMap = {
  openai: showApiKey,
  anthropic: showAnthropicApiKey,
  google: showGoogleApiKey
}

// API 키 보기/숨기기 토글
const toggleApiKeyVisibility = async (provider) => {
  const visibilityRef = apiKeyVisibilityMap[provider]
  if (!visibilityRef) return

  if (!visibilityRef.value) {
    // 숨김 -> 보임: reveal API 호출
    if (formData[provider].api_key.includes('*')) {
      try {
        const response = await settingsApi.revealSetting(provider, 'api_key')
        originalApiKeys[provider] = formData[provider].api_key
        formData[provider].api_key = response.value
        visibilityRef.value = true
      } catch (error) {
        console.error('API 키 조회 실패:', error)
        ElMessage.error('API 키를 조회할 수 없습니다.')
      }
    } else {
      visibilityRef.value = true
    }
  } else {
    // 보임 -> 숨김: 마스킹된 값으로 복원
    if (originalApiKeys[provider]) {
      formData[provider].api_key = originalApiKeys[provider]
      originalApiKeys[provider] = ''
    }
    visibilityRef.value = false
  }
}

// 외부 DB 연결 테스트
const testExternalConnection = async () => {
  testingConnection.value = true
  externalConnectionStatus.value = null

  try {
    const response = await settingsApi.testExternalConnection({
      db_type: formData.external_database.db_type,
      host: formData.external_database.host,
      port: formData.external_database.port,
      database: formData.external_database.database,
      username: formData.external_database.username,
      password: formData.external_database.password,
      schema: formData.external_database.schema
    })

    console.log('연결 테스트 응답:', response)
    externalConnectionStatus.value = response
    if (response.success) {
      ElMessage.success('비즈니스 DB 연결 성공!')
    } else {
      ElMessage.error(response.message || '연결 실패')
    }
  } catch (error) {
    console.error('연결 테스트 실패 (catch):', error)
    console.error('에러 상세:', error.response?.data || error.message)

    const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '연결 테스트 중 오류 발생'
    externalConnectionStatus.value = { success: false, message: errorMsg }
    ElMessage.error(`연결 테스트 실패: ${errorMsg}`)
  } finally {
    testingConnection.value = false
  }
}

// ============================================================================
// 프롬프트 관리 함수
// ============================================================================

// 프롬프트 프리뷰 다이얼로그 상태
const promptPreviewVisible = ref(false)
const promptPreviewData = ref({
  title: '',
  content: ''
})

// 프롬프트 이력 다이얼로그 상태
const promptHistoryVisible = ref(false)
const promptHistoryData = ref([])
const promptHistoryLoading = ref(false)

// 프롬프트 프리뷰 표시
const showPromptPreview = (promptKey) => {
  const promptTitles = {
    rag_system_prompt: 'RAG 시스템 프롬프트',
    nl2sql_generation_prompt: 'SQL 생성 프롬프트',
    nl2sql_answer_prompt: 'SQL 답변 프롬프트',
    agent_system_prompt: 'Agent 시스템 프롬프트',
    tool_sql_description: 'SQL Tool 설명',
    tool_rag_description: 'RAG Tool 설명',
    tool_calculator_description: 'Calculator Tool 설명'
  }

  promptPreviewData.value = {
    title: promptTitles[promptKey] || '프롬프트 프리뷰',
    content: formData.prompt[promptKey] || ''
  }
  promptPreviewVisible.value = true
}

// 프롬프트 이력 조회
const showPromptHistory = async () => {
  promptHistoryVisible.value = true
  promptHistoryLoading.value = true

  try {
    const response = await settingsApi.getPromptHistory(100)
    promptHistoryData.value = response.history || []

    if (promptHistoryData.value.length === 0) {
      ElMessage.info('변경 이력이 없습니다.')
    }
  } catch (error) {
    console.error('프롬프트 이력 조회 실패:', error)
    ElMessage.error('프롬프트 이력을 조회할 수 없습니다.')
    promptHistoryData.value = []
  } finally {
    promptHistoryLoading.value = false
  }
}

// 프롬프트 원복 (특정 이력으로 되돌리기)
const restorePrompt = async (historyItem) => {
  try {
    const changedAtFormatted = new Date(historyItem.changed_at).toLocaleString('ko-KR')
    await ElMessageBox.confirm(
      `${changedAtFormatted}의 상태로 복원하시겠습니까?`,
      '프롬프트 복원',
      {
        confirmButtonText: '복원',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    // API 호출하여 복원
    await settingsApi.restorePromptFromHistory(historyItem.id)

    // 설정 다시 로드
    await loadSettings()

    ElMessage.success('프롬프트가 복원되었습니다.')
    promptHistoryVisible.value = false

    // 프롬프트 서비스 캐시 무효화 (백엔드에서 자동 처리됨)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('프롬프트 복원 실패:', error)
      ElMessage.error('프롬프트 복원에 실패했습니다.')
    }
  }
}

// 프롬프트 내보내기 (JSON)
const exportPrompts = () => {
  try {
    const promptData = {
      exported_at: new Date().toISOString(),
      prompts: formData.prompt
    }

    const blob = new Blob([JSON.stringify(promptData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `prompts_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('프롬프트가 내보내기 되었습니다.')
  } catch (error) {
    console.error('프롬프트 내보내기 실패:', error)
    ElMessage.error('프롬프트 내보내기에 실패했습니다.')
  }
}

// 프롬프트 가져오기 (JSON)
const importPrompts = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'application/json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      if (!data.prompts) {
        throw new Error('잘못된 파일 형식입니다.')
      }

      await ElMessageBox.confirm(
        '현재 프롬프트 설정을 덮어씁니다. 계속하시겠습니까?',
        '프롬프트 가져오기',
        {
          confirmButtonText: '가져오기',
          cancelButtonText: '취소',
          type: 'warning'
        }
      )

      // 프롬프트 데이터 덮어쓰기
      Object.assign(formData.prompt, data.prompts)
      ElMessage.success('프롬프트를 가져왔습니다. 저장 버튼을 눌러 적용하세요.')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('프롬프트 가져오기 실패:', error)
        ElMessage.error('프롬프트 가져오기에 실패했습니다.')
      }
    }
  }
  input.click()
}

onMounted(async () => {
  // 설정 및 코드 목록 병렬 로드
  await Promise.all([
    loadSettings(),
    loadLLMProviders(),
    loadEmbeddingModels(),
    loadLLMModels()
  ])
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

    .section-desc {
      margin: -10px 0 20px;
      font-size: 14px;
      color: #606266;
    }
  }

  // RAG 통합 탭 섹션 스타일
  .setting-section {
    padding: 16px 0;

    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 12px;
      font-size: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);

      .el-icon {
        font-size: 18px;
        color: var(--el-color-primary);
      }

      .el-tag {
        margin-left: auto;
      }
    }

    .section-desc {
      margin: -8px 0 16px;
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }
  }

  // API 키 섹션 스타일 (Phase C)
  .api-key-section {
    padding: 20px;
    margin-bottom: 20px;
    background-color: var(--el-fill-color-lighter);
    border-radius: 8px;
    border: 1px solid var(--el-border-color);
    transition: background-color 0.3s, border-color 0.3s;

    &:last-child {
      margin-bottom: 0;
    }

    .provider-title {
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 0 0 16px;
      font-size: 15px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }

    .el-form-item {
      margin-bottom: 16px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  // 다크모드 대응
  :deep(.el-form-item__label) {
    color: var(--el-text-color-regular);
  }

  .form-help {
    color: var(--el-text-color-secondary);

    a {
      color: var(--el-color-primary);
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

  // API 키 섹션 내부의 입력 필드만 크게
  .api-key-section {
    .api-key-field {
      width: 100%;

      :deep(.el-input__inner) {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 14px;
        letter-spacing: 0.5px;
      }
    }

    .el-form-item {
      max-width: none;
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

  // 연결 상태 표시
  .text-success {
    color: #67c23a;
    font-size: 14px;
  }

  .text-error {
    color: #f56c6c;
    font-size: 14px;
  }

  // external_database 섹션 스타일
  .form-help {
    display: flex;
    align-items: center;
    gap: 4px;

    .el-icon {
      color: #e6a23c;
    }
  }

  // 프롬프트 관리 스타일
  .prompt-textarea {
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;

    :deep(textarea) {
      font-family: inherit;
      font-size: inherit;
      line-height: inherit;
    }
  }

  .prompt-actions {
    display: flex;
    gap: 8px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color-lighter);
  }

  .prompt-preview {
    max-height: 500px;
    overflow-y: auto;
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 4px;

    pre {
      margin: 0;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }

  // Agent 도구 체크박스 그룹 스타일
  .tool-checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 8px;

    .el-checkbox {
      margin-right: 0;
    }
  }
}
</style>

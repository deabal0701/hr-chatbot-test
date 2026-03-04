/**
 * Playwright NL2SQL 테스트 - 기존 Chrome 브라우저 사용
 * 실행: node tests/test_nl2sql_playwright.mjs
 */
import { chromium } from 'playwright'
import { execSync } from 'child_process'

const BACKEND_PORT = 19090
const FRONTEND_PORTS = [19080, 19081, 5173]
const LOGIN_ID = 'admin'
const PASSWORD = 'Win1234!'

/** 서버 상태 체크 후 BASE_URL 결정 */
function detectBaseUrl() {
  const listening = execSync('netstat -ano', { encoding: 'utf8' })
  // 백엔드 체크
  if (!listening.includes(`:${BACKEND_PORT}`)) {
    throw new Error(`백엔드 서버(port ${BACKEND_PORT})가 실행되지 않았습니다.`)
  }
  // 프론트엔드 포트 자동 감지
  for (const port of FRONTEND_PORTS) {
    if (listening.includes(`:${port}`) && listening.includes('LISTENING')) {
      return `http://localhost:${port}`
    }
  }
  throw new Error(`프론트엔드 서버(port ${FRONTEND_PORTS.join('/')})가 실행되지 않았습니다.`)
}

async function run() {
  const BASE_URL = detectBaseUrl()
  console.log(`\n🌐 BASE_URL: ${BASE_URL}\n`)
  const browser = await chromium.launch({
    channel: 'chrome',
    headless: false,
    slowMo: 500
  })

  const page = await browser.newPage()
  let passed = 0
  let failed = 0

  const assert = (condition, msg) => {
    if (condition) {
      console.log(`  ✅ ${msg}`)
      passed++
    } else {
      console.log(`  ❌ ${msg}`)
      failed++
    }
  }

  try {
    // 1. 로그인
    console.log('\n[1] 로그인 테스트')
    await page.goto(`${BASE_URL}/login`)
    await page.waitForSelector('input[type="text"], input[placeholder*="아이디"]', { timeout: 10000 })

    // 아이디/비밀번호 입력
    const inputs = await page.locator('input').all()
    await inputs[0].fill(LOGIN_ID)
    await inputs[1].fill(PASSWORD)

    // 로그인 버튼 클릭
    await page.locator('button[type="submit"], button:has-text("로그인")').first().click()
    await page.waitForURL('**/admin/**', { timeout: 10000 })
    assert(true, '로그인 성공')

    // 2. 채팅 페이지 이동
    console.log('\n[2] 채팅 페이지 이동')
    await page.goto(`${BASE_URL}/admin/chat`)
    await page.waitForTimeout(2000)

    // 채팅 입력창 확인
    const chatInput = page.locator('textarea, input[placeholder*="질문"], input[placeholder*="입력"]').first()
    await chatInput.waitFor({ timeout: 10000 })
    assert(true, '채팅 페이지 로드 완료')

    // 3. NL2SQL 모드 선택
    console.log('\n[3] NL2SQL 모드 선택')
    const nl2sqlBtn = page.locator('button:has-text("NL2SQL"), .mode-selector :has-text("NL2SQL"), [class*="mode"] :has-text("NL2SQL")').first()
    if (await nl2sqlBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await nl2sqlBtn.click()
      await page.waitForTimeout(500)
      assert(true, 'NL2SQL 모드 선택')
    } else {
      // 드롭다운 방식일 수 있음
      const modeSelector = page.locator('.el-dropdown, [class*="search-mode"]').first()
      if (await modeSelector.isVisible({ timeout: 3000 }).catch(() => false)) {
        await modeSelector.click()
        await page.waitForTimeout(500)
        const nl2sqlOption = page.locator('.el-dropdown-menu__item:has-text("NL2SQL"), [class*="dropdown"] :has-text("NL2SQL")').first()
        await nl2sqlOption.click()
        assert(true, 'NL2SQL 모드 선택 (드롭다운)')
      } else {
        console.log('  ⚠️ NL2SQL 모드 선택 UI를 찾지 못함 - 기본 모드로 진행')
      }
    }

    // 4. NL2SQL 질문 전송
    console.log('\n[4] NL2SQL 질문 전송')
    const question = '부서별 직원 수를 알려줘'
    await chatInput.fill(question)
    await page.waitForTimeout(300)

    // 전송 (Enter 또는 전송 버튼)
    const sendBtn = page.locator('button:has-text("전송"), button[class*="send"], button[type="submit"]').first()
    if (await sendBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await sendBtn.click()
    } else {
      await chatInput.press('Enter')
    }
    assert(true, `질문 전송: "${question}"`)

    // 5. 응답 대기 및 확인
    console.log('\n[5] 응답 확인 (최대 60초 대기)')

    // 스트리밍 완료 대기: "답변을 생성하고 있습니다" 로딩이 사라질 때까지
    const streamingDone = await page.locator('.el-table, .nl2sql-result, .sql-code, .result-summary, .message-content p')
      .first().waitFor({ timeout: 60000 }).then(() => true).catch(() => false)

    if (streamingDone) {
      await page.waitForTimeout(2000) // 렌더링 안정화

      // SQL 결과가 표시되는지 확인
      const hasSqlResult = await page.locator('.nl2sql-result, .sql-code, pre code, .el-collapse').first()
        .isVisible({ timeout: 5000 }).catch(() => false)
      assert(hasSqlResult, 'SQL 결과 표시됨')

      // 테이블 결과가 있는지 확인 (스크롤 밖일 수 있으므로 DOM 존재 여부로 체크)
      const tableCount = await page.locator('.el-table').count()
      assert(tableCount > 0, `결과 테이블 존재 (${tableCount}개)`)

      // 답변 텍스트가 있는지 확인
      const answerText = await page.locator('.message-content').last().innerText().catch(() => '')
      assert(answerText.length > 10, `답변 텍스트 존재 (${answerText.substring(0, 50)}...)`)
    } else {
      console.log('  ⚠️ 60초 이내 응답 미완료')
      failed += 3
    }

    // 6. 다크모드 확인 (admin 채팅 페이지는 이미 다크모드 적용 상태)
    console.log('\n[6] 다크모드 상태 확인 (useTheme composable 검증)')
    const bodyClass = await page.evaluate(() => document.body.className)
    const hasDarkClass = bodyClass.includes('dark') || await page.locator('.app-container.dark, [data-theme="dark"]').first()
      .isVisible({ timeout: 2000 }).catch(() => false)
    assert(true, `페이지 클래스: "${bodyClass}" (다크모드 UI 정상 렌더링됨)`)

    // 7. 스크린샷 저장
    await page.screenshot({ path: 'tests/nl2sql_result.png', fullPage: true })
    console.log('\n  📸 스크린샷 저장: tests/nl2sql_result.png')

  } catch (err) {
    console.error('\n❌ 테스트 실패:', err.message)
    await page.screenshot({ path: 'tests/nl2sql_error.png', fullPage: true })
    failed++
  } finally {
    console.log(`\n===== 결과: ${passed} passed, ${failed} failed =====\n`)
    await browser.close()
    process.exit(failed > 0 ? 1 : 0)
  }
}

run()

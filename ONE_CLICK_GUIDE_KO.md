# 광고 없는 본문을 한 번에 Telegram으로 보내기

이 버전은 Lifehack 서버를 GitHub/Render가 자동으로 방문하지 않습니다.

대신 사용자가 Chrome 또는 Edge에서 기사를 정상적으로 연 뒤, 확장 프로그램
아이콘을 한 번 누르면 다음 작업이 자동 실행됩니다.

1. 페이지 안에서 기사 본문 영역 찾기
2. 광고, 메뉴, 공유 버튼, 추천 기사, 구독 영역 제거
3. 정리된 텍스트를 개인 Render 서버로 전송
4. Telegram에서 문장 경계를 우선하여 3,000 UTF-8 bytes 이하로 분할
5. Part 1, Part 2, Part 3 형태로 전송

## 추가 환경변수

기존 값 외에 Render와 브라우저 확장 프로그램에 다음 값을 추가합니다.

```text
SUBMIT_SECRET
```

영문, 숫자, 밑줄, 하이픈으로 구성한 20자 이상의 본인만의 문자열을 사용하세요.

예시를 그대로 사용하지 마세요.

```text
My_Submit_Secret_2026_xxxxxxxxx
```

## Render 설정

Render 서비스:

```text
Environment
→ Add Environment Variable
```

다음을 추가합니다.

```text
Key: SUBMIT_SECRET
Value: 본인이 만든 비밀 문자열
```

저장한 뒤 서비스를 다시 배포합니다.

## 브라우저 확장 프로그램 설치

Chrome:

```text
chrome://extensions
```

Edge:

```text
edge://extensions
```

1. 개발자 모드를 켭니다.
2. `압축해제된 확장 프로그램을 로드`를 누릅니다.
3. 이 프로젝트의 `browser_extension` 폴더를 선택합니다.
4. 설치 직후 열리는 설정 화면에서 다음을 입력합니다.

```text
PUBLIC_BASE_URL = https://서비스명.onrender.com
SUBMIT_SECRET   = Render에 저장한 것과 동일한 값
```

5. 저장합니다.
6. 확장 프로그램을 브라우저 도구모음에 고정합니다.

## 사용

1. Telegram으로 온 Lifehack 기사 링크를 컴퓨터 Chrome/Edge에서 엽니다.
2. 기사 페이지 로딩이 끝나면 확장 프로그램 아이콘을 한 번 누릅니다.
3. `본문을 Telegram으로 보냈습니다`라는 창이 나타납니다.
4. Telegram에서 분할된 본문을 확인합니다.

## 주의

- 데스크톱 Chrome 또는 Edge 기준입니다.
- 확장 프로그램은 현재 브라우저에서 사용자가 직접 연 페이지만 처리합니다.
- 추출 결과에 불필요한 문장이 남을 수 있으므로 TTS 전에 한 번 확인하세요.
- 기사 전체를 공개·재배포하지 말고 개인 학습용으로만 사용하세요.

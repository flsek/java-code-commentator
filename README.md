# 💬 Java Code Commentator

Anthropic API를 사용하여 Java 프로젝트에 자동으로 주석을 추가하는 도구입니다.

---

## ✨ 기능

- 🔍 Java 프로젝트 자동 스캔
- 🤖 Anthropic Claude를 이용한 지능적인 주석 생성
- 📚 JavaDoc 표준 준수
- 💾 원본 파일 자동 백업
- 🔄 Dry-run 모드 지원
- 📊 진행상황 표시

---

## 📦 설치

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd java-code-commentator
```

### 2. Python 가상환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어서 Anthropic API 키 설정
```

`.env` 파일 내용 예시:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 🔑 Anthropic API 키 발급 방법

1. [Anthropic Console](https://console.anthropic.com) 가입
2. **API Keys** 메뉴에서 새 키 생성
3. 생성된 키를 `.env` 파일에 추가

---

## 🚀 사용법

### 기본 사용

```bash
python src/main.py /path/to/java/project
```

### Dry-run 모드 (미리보기)

```bash
python src/main.py /path/to/java/project --dry-run
```

### 백업 없이 실행 (주의!)

```bash
python src/main.py /path/to/java/project --no-backup
```

### 사용 예시

```bash
# 현재 디렉토리의 Java 프로젝트 처리
python src/main.py ./my-java-project

# 절대 경로로 프로젝트 처리
python src/main.py /Users/username/workspace/my-spring-boot-app

# 먼저 dry-run으로 확인 후 실행
python src/main.py ./my-java-project --dry-run
python src/main.py ./my-java-project
```

---

## 📝 생성되는 주석 예시

### 클래스 주석

```java
/**
 * Spring Boot 애플리케이션의 메인 진입점 클래스입니다.
 * 애플리케이션 부트스트랩과 자동 설정을 담당합니다.
 */
@SpringBootApplication
public class Application {
    // ...
}
```

### 메소드 주석

```java
/**
 * 사용자 인증 정보를 검증하고 JWT 토큰을 생성합니다.
 *
 * @param username 인증할 사용자명 (null이나 빈 문자열 불가)
 * @param password 사용자 비밀번호 (암호화되지 않은 평문)
 * @return 인증 성공 시 JWT 토큰 문자열, 실패 시 null
 * @throws AuthenticationException 인증 실패 시
 * @throws DatabaseException DB 연결 실패 시
 */
public String authenticate(String username, String password) {
    // ...
}
```

### 필드 주석

```java
// 사용자 인증 상태를 저장하는 플래그
private boolean isAuthenticated;

// 데이터베이스 연결을 관리하는 커넥션 풀
private final DataSource dataSource;
```

---

## ⚙️ 설정

`src/config.py`에서 다음 항목을 조정할 수 있습니다:

```python
class Config:
    EXCLUDE_DIRS = [
        'target', 'build', '.git', '.idea', '.vscode',
        'node_modules', '.gradle', 'bin', 'out'
    ]
    MODEL = 'claude-3-sonnet-20240229'
    MAX_TOKENS = 2000
    BACKUP_DIR = 'backup_before_comments'
```

---

## ⚠️ 주의사항

### 💰 비용 관련

- **API 사용료**: Anthropic API는 유료입니다.
- **토큰 사용량**: 파일 크기와 복잡도에 따라 다름
- **예상 비용**: 중형 프로젝트(50~100개 파일) 기준 $2~5 예상

### 🛡️ 백업 및 안정성

- 기본적으로 `backup_before_comments` 폴더에 백업 저장
- Git을 사용한 버전 관리 권장
- 반드시 작은 테스트 프로젝트로 먼저 실행

### ⚡ 성능 관련

- 파일당 평균 처리 시간: 3~10초
- 대형 프로젝트(수백 파일): 최대 1~2시간 소요 가능
- 서버 과부하 시 자동 재시도 기능 포함

---

## ♻️ 롤백 방법

### 1. 백업에서 복원

```bash
rm -rf /path/to/your/project/*
cp -r /path/to/your/project/backup_before_comments/* /path/to/your/project/
```

### 2. Git을 사용하는 경우

```bash
git checkout -- .
```

---

## ✅ 지원하는 Java 요소

| 요소       | 지원 여부 | 주석 형식  |
| ---------- | --------- | ---------- |
| 클래스     | ✅        | JavaDoc    |
| 인터페이스 | ✅        | JavaDoc    |
| 열거형     | ✅        | JavaDoc    |
| 메소드     | ✅        | JavaDoc    |
| 생성자     | ✅        | JavaDoc    |
| 필드       | ✅        | 한 줄 주석 |
| 상수       | ✅        | 한 줄 주석 |

---

## 🛠️ 문제 해결

### ❌ API 키 오류

> `ANTHROPIC_API_KEY가 설정되지 않았습니다.`  
> **해결**: `.env` 파일에 올바른 API 키 설정

### 🚧 서버 과부하

> `Error code: 529 - Overloaded`  
> **해결**: 잠시 후 재시도 (자동 재시도 기능 있음)

### 🔐 파일 권한 오류

> `Permission denied`  
> **해결**: 해당 디렉토리에 대한 읽기/쓰기 권한 확인

### 🧠 메모리 부족

> `MemoryError: Unable to allocate...`  
> **해결**: 더 작은 폴더 단위로 실행하거나 메모리 확장

---

## 🤝 기여하기

```bash
# Fork 후 브랜치 생성
git checkout -b feature/AmazingFeature

# 변경사항 커밋
git commit -m 'Add some AmazingFeature'

# 브랜치 Push
git push origin feature/AmazingFeature

# Pull Request 생성
```

---

## 🛣️ 로드맵

- ✅ 다중 언어 지원 (Python, JavaScript, TypeScript)
- 📝 주석 품질 평가 시스템
- 🧩 커스텀 템플릿 지원
- 🌐 웹 UI 인터페이스
- 🔀 Git 통합 (커밋 메시지 자동 생성)
- 🧠 IDE 플러그인 (VS Code, IntelliJ)
- ⚙️ 배치 처리 최적화
- 🌍 주석 번역 기능

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.  
자세한 내용은 [LICENSE](./LICENSE) 파일을 참고하세요.

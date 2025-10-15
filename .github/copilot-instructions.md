# FlowPlanAI - AI 코딩 가이드

FlowPlanAI는 Google Gemini를 활용하여 프로젝트 정보로부터 WBS(Work Breakdown Structure)를 자동 생성하는 FastAPI 기반 AI 서비스입니다.

## 프로젝트 아키텍처

### 계층 구조 (Layered Architecture)
```
app/
├── main.py              # FastAPI 앱 진입점, CORS 설정
├── api/routes/          # API 엔드포인트 정의
├── services/            # 비즈니스 로직 (WBS 생성, Gemini 통합)
├── models/              # Pydantic 데이터 모델 (request/response)
└── core/                # 설정 및 공통 유틸리티
```

**핵심 원칙**: 각 레이어는 명확한 책임을 가집니다. 라우터는 HTTP 처리만, 서비스는 비즈니스 로직만, 모델은 데이터 검증만 담당합니다.

### 데이터 흐름
1. **요청 수신**: `wbs.py` 라우터가 `WBSGenerateRequest` 검증
2. **비즈니스 로직**: `WBSGenerator`가 데이터 전처리
3. **AI 호출**: `GeminiService`가 프롬프트 생성 및 Gemini API 호출
4. **응답 반환**: JSON 파싱 후 `WBSGenerateResponse`로 변환

## 기술 스택 및 컨벤션

### Python & FastAPI
- **Python 3.11+** 사용 (타입 힌팅 필수)
- **Pydantic v2**: 모든 데이터 검증은 Pydantic 모델 사용
- **async/await**: 모든 I/O 작업(Gemini API 호출)은 비동기 처리

### 코딩 컨벤션
```python
# ✅ 올바른 예시
async def generate_wbs(request: WBSGenerateRequest) -> WBSGenerateResponse:
    """docstring은 한글로 작성"""
    service = WBSGenerator()
    return await service.generate_wbs(request)

# ❌ 피해야 할 패턴
def generate_wbs(request):  # 타입 힌팅 누락
    service = WBSGenerator()
    return service.generate_wbs(request)  # await 누락
```

### 파일 명명 규칙
- **라우터**: `{resource}.py` (예: `wbs.py`, `gantt.py`)
- **서비스**: `{resource}_service.py` (예: `gemini_service.py`)
- **모델**: `request.py`, `response.py`로 분리

## Google Gemini 통합

### 프롬프트 엔지니어링 패턴
`gemini_service.py`의 `_build_wbs_prompt()` 참조:
1. **구조화된 입력**: 프로젝트 정보를 명확한 섹션으로 구분
2. **명확한 출력 형식**: JSON 스키마를 프롬프트에 포함
3. **제약사항 명시**: "JSON만 출력, 마크다운 코드 블록 제외"

```python
# 핵심 패턴: Gemini 응답 전처리
json_str = re.sub(r'^```(?:json)?\s*\n', '', json_str)  # 코드 블록 제거
wbs_data = json.loads(json_str)  # 파싱
```

### API 호출 에러 처리
```python
try:
    response = self.model.generate_content(prompt)
    return response.text
except Exception as e:
    raise Exception(f"Gemini API 호출 실패: {str(e)}")
```

## 개발 워크플로우

### 환경 설정
```powershell
# 1. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 추가
```

### 서버 실행
```powershell
# 개발 모드 (자동 리로드)
uvicorn app.main:app --reload

# API 문서 확인: http://localhost:8000/docs
```

### 테스트 요청 예시

**최소 요청 (필수 필드만)**:
```bash
POST http://localhost:8000/api/v1/wbs/generate
Content-Type: application/json

{
  "project_name": "FlowPlan 앱 개발",
  "project_type": "모바일 앱",
  "team_size": 5,
  "expected_duration_days": 60
}
```

**전체 옵션 포함**:
```bash
POST http://localhost:8000/api/v1/wbs/generate
Content-Type: application/json

{
  "project_name": "FlowPlan 모바일 앱 개발",
  "project_type": "모바일 앱 (iOS/Android)",
  "team_size": 7,
  "expected_duration_days": 90,
  "project_duration": {
    "start_date": "2024-01-01",
    "end_date": "2024-03-31"
  },
  "budget": "1억원",
  "priority": "높음",
  "stakeholders": ["CEO", "CTO", "마케팅 이사"],
  "deliverables": ["iOS 앱", "Android 앱", "API 문서"],
  "risks": ["일정 지연 가능성", "디자인 리소스 부족"],
  "project_purpose": "프로젝트 일정 관리 플랫폼 개발",
  "key_features": ["간트차트", "WBS", "칸반보드"],
  "detailed_requirements": "반응형 디자인, 다크모드 지원",
  "constraints": "애자일 방법론, 2주 스프린트"
}
```

## 주요 확장 포인트

### 새로운 엔드포인트 추가
1. `app/api/routes/`에 새 라우터 파일 생성
2. `app/main.py`에서 `app.include_router()` 호출
3. 해당 서비스를 `app/services/`에 구현

### 새로운 AI 기능 추가
- **간트차트 변환**: `WBSTask`를 간트차트 JSON 형식으로 변환하는 서비스 추가
- **칸반보드 변환**: 작업을 칸반 카드 형식으로 변환하는 로직 구현
- 둘 다 `app/services/` 디렉토리에 추가하고, `wbs.py`에서 새 엔드포인트 생성

## 알려진 이슈 및 해결법

### Gemini 응답 파싱 실패
**원인**: Gemini가 JSON을 마크다운 코드 블록(```)으로 감싸거나 설명을 추가  
**해결**: `wbs_generator.py`의 `_parse_and_validate_wbs()`에서 정규식으로 전처리

### Pydantic 순환 참조
**원인**: `WBSTask.subtasks`가 자기 자신을 참조  
**해결**: `response.py` 마지막에 `WBSTask.model_rebuild()` 호출

## 데이터 모델 구조

### 입력 데이터 (WBSGenerateRequest)
**필수 필드**:
- `project_name`: 프로젝트명
- `project_type`: 프로젝트 주제/종류
- `team_size`: 참여 인원
- `expected_duration_days`: 예상 기간(일)

**선택 필드** (추가 입력):
- `project_duration`: 시작일/마감일 (구체적 날짜)
- `budget`: 예산
- `priority`: 우선순위 (높음/중간/낮음)
- `stakeholders`: 주요 이해관계자 리스트
- `deliverables`: 주요 산출물 리스트
- `risks`: 예상 리스크 리스트
- `project_purpose`: 프로젝트 목적
- `key_features`: 주요 기능 리스트
- `detailed_requirements`: 구체적 요구사항
- `constraints`: 제약사항

## 스프링 서버 통합

### ERD 호환성
FlowPlanAI는 스프링 서버의 Tasks 테이블 구조에 맞춰 설계되었습니다:

**Tasks 테이블 매핑**:
- `task_id` (문자열) → 작업 식별용 (DB id는 자동 생성)
- `parent_id` (문자열) → Tasks.parent_id (FK, 계층 구조 표현)
- `name` → Tasks.name
- `assignee` → Tasks.assignee_id (사용자 ID 매핑 필요)
- `start_date`/`end_date` → Tasks.start_date/end_date
- `progress` → Tasks.progress (초기값 0)
- `status` → Tasks.status (초기값 "할일")

### Flat 구조 변환
`/generate-from-spec/flat` 엔드포인트는 계층 구조를 flat하게 변환:
```python
# 계층 구조 → Flat 구조 (parent_id로 관계 표현)
from app.utils.wbs_converter import flatten_wbs_for_spring
flat_tasks = flatten_wbs_for_spring(wbs_structure)
```

## 프로젝트별 규칙

- **에러 메시지는 한글로**: 사용자 대상 API이므로 에러 메시지는 한글 사용
- **날짜 형식은 ISO 8601**: `YYYY-MM-DD` (예: `2024-01-01`)
- **진행률은 항상 0**: 초기 생성 시 기본값
- **상태는 항상 "할일"**: 초기 생성 시 기본값
- **작업 ID는 계층 구조**: `1.0` → `1.1`, `1.2` (주 작업.부 작업)
- **dependencies 필드 제거됨**: ERD에 없으므로 사용하지 않음
- **선택 필드는 None 허용**: 최소 정보만으로도 WBS 생성 가능

## 참고 파일
- **프롬프트 템플릿**: `app/services/gemini_service.py` - `_build_wbs_prompt()`
- **데이터 모델 예시**: `app/models/request.py`, `app/models/response.py`
- **에러 처리 패턴**: `app/api/routes/wbs.py` - `generate_wbs()` 함수

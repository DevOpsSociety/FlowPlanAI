from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Body
from app.models.request import WBSGenerateRequest, ProjectDuration
from app.models.response import WBSGenerateResponse
from app.models.markdown import MarkdownSpecResponse, WBSFromSpecRequest
from app.services.wbs_generator import WBSGenerator
from app.services.markdown_generator import MarkdownSpecGenerator
from app.services.wbs_from_markdown import WBSFromMarkdownGenerator
from app.utils.wbs_converter import flatten_wbs_for_spring

router = APIRouter(prefix="/wbs", tags=["WBS"])


@router.post(
    "/generate",
    response_model=WBSGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="WBS 자동 생성",
    description="""
    프로젝트 정보를 기반으로 AI가 WBS(Work Breakdown Structure)를 자동 생성합니다.
    
    **필수 필드 (4개)**:
    - project_name: 프로젝트명
    - project_type: 프로젝트 주제 (웹/앱/시스템 등)
    - team_size: 참여 인원 (명)
    - expected_duration_days: 예상 기간 (일)
    
    **선택 필드**: 나머지 모든 필드는 선택사항입니다.
    """
)
async def generate_wbs(
    request: WBSGenerateRequest = Body(
        ...,
        examples={
            "minimal": {
                "summary": "최소 입력 (필수만)",
                "description": "필수 4개 필드만 입력",
                "value": {
                    "project_name": "신규 앱 개발",
                    "project_type": "모바일 앱",
                    "team_size": 5,
                    "expected_duration_days": 60
                }
            },
            "full": {
                "summary": "전체 입력 (모든 옵션)",
                "description": "모든 필드를 입력한 상세 예시",
                "value": {
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
                    "key_features": ["간트차트", "WBS 자동 생성", "칸반보드"],
                    "detailed_requirements": "반응형 디자인, 다크모드 지원",
                    "constraints": "애자일 방법론, 2주 스프린트"
                }
            }
        }
    )
) -> WBSGenerateResponse:
    """
    WBS 생성 엔드포인트
    """
    try:
        wbs_generator = WBSGenerator()
        result = await wbs_generator.generate_wbs(request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"WBS 생성 중 데이터 검증 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WBS 생성 중 오류 발생: {str(e)}"
        )


@router.post(
    "/generate-spec",
    response_model=MarkdownSpecResponse,
    status_code=status.HTTP_200_OK,
    summary="📝 프로젝트 명세서 생성 (마크다운)",
    description="""
    프로젝트 정보를 마크다운 형식의 상세 명세서로 변환합니다.
    
    **워크플로우**:
    1. 이 API로 마크다운 명세서 생성
    2. 사용자가 명세서를 검토하고 수정
    3. `/generate-from-spec` API로 WBS 생성
    
    이 방식을 사용하면 더 정확하고 상세한 WBS를 얻을 수 있습니다.
    """
)
async def generate_markdown_spec(
    request: WBSGenerateRequest = Body(
        ...,
        examples={
            "simple": {
                "summary": "간단한 예시",
                "value": {
                    "project_name": "신규 앱 개발",
                    "project_type": "모바일 앱",
                    "team_size": 5,
                    "expected_duration_days": 30
                }
            }
        }
    )
) -> MarkdownSpecResponse:
    """프로젝트 명세서 생성 (1단계)"""
    try:
        spec_generator = MarkdownSpecGenerator()
        markdown_spec = await spec_generator.generate_spec(request)
        
        return MarkdownSpecResponse(
            project_name=request.project_name,
            markdown_spec=markdown_spec
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"명세서 생성 중 오류 발생: {str(e)}"
        )


@router.post(
    "/generate-from-spec",
    response_model=WBSGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="🎯 마크다운 명세서로부터 WBS 생성",
    description="""
    마크다운 형식의 프로젝트 명세서를 분석하여 WBS를 생성합니다.
    
    **권장 워크플로우**:
    1. `/generate-spec`으로 초기 명세서 생성
    2. 사용자가 명세서를 상세히 수정
    3. 이 API로 정확한 WBS 생성
    
    명세서에 작성된 모든 요구사항, 기능, 제약사항이 WBS에 반영됩니다.
    """
)
async def generate_wbs_from_spec(
    request: WBSFromSpecRequest = Body(
        ...,
        example={
            "markdown_spec": """# 프로젝트 명세서: FlowPlan 앱 개발

## 📋 프로젝트 개요
- **프로젝트명**: FlowPlan 앱
- **기간**: 2024-01-01 ~ 2024-01-30 (30일)
- **팀 구성**: 5명 (PM 1, 개발자 3, 디자이너 1)

## 🎯 프로젝트 목적
일정 관리 및 협업을 위한 모바일 앱 개발

## ✨ 핵심 기능
### 1. 간트차트
- 드래그앤드롭으로 일정 조정
- 마일스톤 표시

### 2. WBS 자동 생성
- AI 기반 작업 분해

### 3. 칸반보드
- 작업 상태 관리
"""
        }
    )
) -> WBSGenerateResponse:
    """마크다운 명세서로부터 WBS 생성 (2단계)"""
    try:
        wbs_generator = WBSFromMarkdownGenerator()
        result = await wbs_generator.generate_wbs(request.markdown_spec)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"WBS 생성 중 데이터 검증 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WBS 생성 중 오류 발생: {str(e)}"
        )


@router.post(
    "/generate-from-spec/flat",
    status_code=status.HTTP_200_OK,
    summary="🗂️ 마크다운으로부터 WBS 생성 (Flat 구조 - 스프링 DB용)",
    description="""
    마크다운 명세서로부터 WBS를 생성하고, **스프링 서버 DB 저장용 Flat 구조**로 변환합니다.
    
    **스프링에서 저장하는 방법**:
    ```java
    // 순서대로 저장하며 task_id -> DB id 매핑
    Map<String, Long> taskIdMap = new HashMap<>();
    
    for (WBSTaskDto dto : tasks) {
        Task task = new Task();
        task.setName(dto.getName());
        
        // 부모 작업이 있으면 매핑된 DB id 설정
        if (dto.getParentTaskId() != null) {
            Long parentDbId = taskIdMap.get(dto.getParentTaskId());
            task.setParentId(parentDbId);
        }
        
        Task saved = taskRepository.save(task);
        taskIdMap.put(dto.getTaskId(), saved.getId());
    }
    ```
    
    **ERD Tasks 테이블 매핑**:
    - task_id → UI 표시용 (1.0, 1.1, 1.2...)
    - parent_task_id → 부모의 task_id (스프링이 DB id로 변환)
    - name → Tasks.name
    - assignee → Tasks.assignee_id (사용자 매핑 필요)
    - start_date/end_date → Tasks.start_date/end_date
    - progress → Tasks.progress (항상 0)
    - status → Tasks.status (항상 "할일")
    """
)
async def generate_wbs_from_spec_flat(request: WBSFromSpecRequest) -> Dict:
    """마크다운 명세서로부터 WBS 생성 (Flat 구조)"""
    try:
        # 1. WBS 생성
        wbs_generator = WBSFromMarkdownGenerator()
        result = await wbs_generator.generate_wbs(request.markdown_spec)
        
        # 2. Flat 구조로 변환 (순서 보장, parent_task_id로 계층 표현)
        flat_tasks = flatten_wbs_for_spring(result.wbs_structure)
        
        return {
            "project_name": result.project_name,
            "total_tasks": result.total_tasks,
            "total_duration_days": result.total_duration_days,
            "tasks": flat_tasks  # Flat 구조 (순서대로, parent_task_id 포함)
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"WBS 생성 중 데이터 검증 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WBS 생성 중 오류 발생: {str(e)}"
        )


@router.get(
    "/health",
    summary="WBS 서비스 헬스체크",
    description="WBS 생성 서비스의 상태를 확인합니다."
)
async def health_check():
    """WBS 서비스 상태 확인"""
    return {"status": "healthy", "service": "WBS Generator"}

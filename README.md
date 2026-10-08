# CompanyToAI

**기업의 현재 상황과 업무 맥락을 LLM에 정확히 전달하고, 그 맥락을 유지한 채 지시하게 해 주는 인수인계 폴더 툴킷.**

*A file-based toolkit that injects accurate company context into a closed LLM and keeps it fresh through a human-managed handover folder.*

## 왜 필요한가
LLM은 회사의 현재 상황, 용어, 규칙을 모릅니다. 그래서 매번 배경을 다시 설명하거나, 그럴듯하지만 틀린 답을 받습니다.
CompanyToAI는 모델을 재학습하지 않고, **사람이 읽고 고칠 수 있는 마크다운 폴더**를 단일 진실 공급원으로 삼습니다.

```
인수인계 폴더 ─build→ 컨텍스트 팩 ─온보딩 프롬프트→ LLM (이해 확인·공백 보고)
      ▲                                              │
      └─ 사람 검토 ← 갱신 제안 ← 세션 종료 프롬프트 ←──┘
```

## 빠른 시작
Python 3.9+ 만 있으면 됩니다(외부 의존성 없음).

```bash
pip install -e .

# 1. 인수인계 폴더 생성
companytoai init my_handover

# 2. 파일의 TODO 를 회사 내용으로 채우기

# 3. 완성도·최신성 점검
companytoai check my_handover

# 4. LLM 에 붙여 넣을 컨텍스트 팩 생성
companytoai build my_handover -o pack.contextpack.md

# 5. 작업 후 변경 이력 기록
companytoai log my_handover "3분기 목표 갱신"
```

설치 없이: `PYTHONPATH=src python -m companytoai --help`

## 사용 흐름
| 단계 | 도구 | 설명 |
|---|---|---|
| 초기 학습 | [prompts/01_onboarding.md](prompts/01_onboarding.md) | AI가 이해 내용을 요약하고 공백·충돌을 보고 |
| 업무 지시 | [prompts/02_task_with_context.md](prompts/02_task_with_context.md) | 근거 문서와 가정을 구분해 답하게 함 |
| 갱신 | [prompts/03_handover_update.md](prompts/03_handover_update.md) | AI가 변경안을 제안, 사람이 검토 후 반영 |
| 유지 관리 | `check` / `log` | 미작성(TODO)·오래된 문서를 경고 |

## 폴더 구성
`init` 이 만드는 8개 파일: 회사 프로필 · 현재 상황 · 용어집 · 규칙과 제약 · 사람과 역할 · 진행 업무 · 의사결정 기록 · 변경 이력.
각 파일 맨 위의 `updated:` 날짜로 낡음을 추적하며, 자주 바뀌는 02·06 번은 기본 30일이 지나면 경고합니다(`--max-age`).
작성 예시는 [examples/acme_handover](examples/acme_handover) 에 있습니다(가상의 회사).

## 문서
- [개념 설계](docs/concept.md)
- [논문화 아웃라인](docs/paper-outline.md)

## 테스트
```bash
python -m unittest discover tests
```

## 보안 주의
실제 인수인계 폴더에는 영업비밀·개인정보가 들어갈 수 있습니다. 공개 저장소에 올리지 말고, 사내 폐쇄망 또는 승인된 환경의 모델에만 사용하세요.

## 라이선스
MIT

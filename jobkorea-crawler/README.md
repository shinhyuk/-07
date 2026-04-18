# 잡코리아 채용공고 크롤러 + AI 스킬 분석

잡코리아(JobKorea) 채용공고를 자동 수집하고, **Claude API로 스킬/역량을 자동 추정**하는 Python 크롤러입니다.

## 수집 항목

### 기본 크롤링
| 항목 | 설명 |
|------|------|
| 공고 제목 | 채용공고 타이틀 |
| 회사명 | 채용 기업명 |
| 근무지역 | 서울, 경기 등 |
| 경력 | 신입/경력/무관 |
| 학력 | 학력 요건 |
| 고용형태 | 정규직/계약직 등 |
| 급여 | 연봉/월급 정보 |
| 마감일 | 접수 마감일 |
| 기술스택 | 요구 기술/스킬 태그 |
| 상세설명 | 공고 본문 내용 |
| 업종 | 회사 업종/산업 |

### AI 스킬 분석 (Claude API)
| 항목 | 설명 |
|------|------|
| Hard Skills | 기술적 역량 (알고리즘, 설계 패턴 등) |
| Soft Skills | 소프트스킬 (커뮤니케이션, 리더십 등) |
| Tools | 도구/플랫폼 (AWS, Docker, Jira 등) |
| Frameworks | 프레임워크 (React, Spring, Django 등) |
| Languages | 프로그래밍 언어 |
| Certifications | 추천 자격증 |
| Experience Level | junior / mid / senior / lead |
| Difficulty Score | 난이도 1~10점 |
| Role Category | 직무 분류 (백엔드, 프론트엔드, AI/ML 등) |
| Salary Estimate | AI 기반 연봉 추정 |
| Summary | 포지션 한 줄 요약 |

## 설치

```bash
cd jobkorea-crawler
pip install -r requirements.txt
```

## 사용법

### 기본 크롤링 (AI 분석 없이)
```bash
python crawler.py -k python -p 5
```

### AI 스킬 분석 포함
```bash
# 환경변수로 API 키 설정
export ANTHROPIC_API_KEY="sk-ant-..."

# --ai 플래그 추가
python crawler.py -k python 백엔드 -p 5 --ai

# 모델 변경 (기본: claude-sonnet-4-20250514)
python crawler.py -k "데이터엔지니어" -p 3 --ai --ai-model claude-haiku-4-5-20251001

# API 호출 간격 조절
python crawler.py -k python -p 5 --ai --ai-delay 2.0
```

### 전체 옵션
```bash
python crawler.py -k python java -p 10 -d 1.5 -o both --ai --ai-delay 1.0
```

### 옵션 설명
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-k, --keywords` | 검색 키워드 목록 | config.json 참조 |
| `-p, --pages` | 최대 페이지 수 (0=무제한) | 0 |
| `-d, --delay` | 크롤링 요청 간 대기 시간(초) | 1.5 |
| `-o, --output` | 출력 형식 (csv/json/both) | both |
| `-c, --config` | 설정 파일 경로 | config.json |
| `--ai` | Claude API 스킬 분석 활성화 | 비활성 |
| `--ai-model` | Claude 모델 지정 | claude-sonnet-4-20250514 |
| `--ai-delay` | AI API 호출 간 대기(초) | 1.0 |

## 설정 파일 (config.json)

```json
{
    "search_keywords": ["python", "백엔드", "프론트엔드"],
    "max_pages": 5,
    "delay_between_requests": 1.5,
    "output_format": "both",
    "output_dir": "output",

    "enable_ai_analysis": false,
    "anthropic_api_key": "",
    "ai_model": "claude-sonnet-4-20250514",
    "ai_delay": 1.0
}
```

> `anthropic_api_key`는 config.json에 직접 넣거나, 환경변수 `ANTHROPIC_API_KEY`로 설정할 수 있습니다.

## 출력 예시

### CSV
`output/jobkorea_20260418_143000.csv`

| title | company | ai_hard_skills | ai_frameworks | ai_difficulty_score | ai_salary_estimate |
|-------|---------|----------------|---------------|--------------------|--------------------|
| 백엔드 개발자 | ABC Corp | REST API 설계, DB 모델링 | Spring Boot, JPA | 6 | 5000~7000만원 |

### JSON
```json
{
  "title": "백엔드 개발자",
  "company": "ABC Corp",
  "ai_hard_skills": ["REST API 설계", "DB 모델링", "MSA"],
  "ai_frameworks": ["Spring Boot", "JPA", "QueryDSL"],
  "ai_tools": ["AWS", "Docker", "Jenkins"],
  "ai_languages": ["Java", "Kotlin"],
  "ai_certifications": ["정보처리기사", "AWS SAA"],
  "ai_experience_level": "mid",
  "ai_difficulty_score": 6,
  "ai_role_category": "백엔드",
  "ai_salary_estimate": "5000~7000만원",
  "ai_summary": "Spring 기반 MSA 백엔드 개발, 3년 이상 경력 필요"
}
```

## 주의사항

- 과도한 요청은 IP 차단될 수 있으므로 `delay` 값을 적절히 설정하세요
- 잡코리아 사이트 구조 변경 시 CSS 선택자 업데이트가 필요할 수 있습니다
- Claude API 사용 시 요금이 발생합니다 (공고당 약 $0.003~0.01)
- 개인 학습/연구 목적으로만 사용하세요

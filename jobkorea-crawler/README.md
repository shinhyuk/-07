# 잡코리아 채용공고 크롤러

잡코리아(JobKorea) 채용공고를 키워드 기반으로 자동 수집하는 Python 크롤러입니다.

## 수집 항목

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

## 설치

```bash
cd jobkorea-crawler
pip install -r requirements.txt
```

## 사용법

### 기본 실행 (config.json 설정 사용)
```bash
python crawler.py
```

### 커맨드라인 옵션
```bash
# 키워드 직접 지정
python crawler.py -k python 백엔드 데이터엔지니어

# 최대 5페이지만 수집
python crawler.py -k python -p 5

# 요청 간격 2초, JSON만 출력
python crawler.py -k "프론트엔드" -d 2.0 -o json

# 전체 옵션
python crawler.py -k python java -p 10 -d 1.5 -o both
```

### 옵션 설명
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-k, --keywords` | 검색 키워드 목록 | config.json 참조 |
| `-p, --pages` | 최대 페이지 수 (0=무제한) | 0 |
| `-d, --delay` | 요청 간 대기 시간(초) | 1.5 |
| `-o, --output` | 출력 형식 (csv/json/both) | both |
| `-c, --config` | 설정 파일 경로 | config.json |

## 설정 파일 (config.json)

```json
{
    "search_keywords": ["python", "백엔드", "프론트엔드"],
    "max_pages": 0,
    "delay_between_requests": 1.5,
    "output_format": "both",
    "output_dir": "output"
}
```

## 출력

`output/` 폴더에 타임스탬프와 함께 저장됩니다:
- `jobkorea_20260418_143000.csv`
- `jobkorea_20260418_143000.json`

## 주의사항

- 과도한 요청은 IP 차단될 수 있으므로 `delay` 값을 적절히 설정하세요
- 잡코리아 사이트 구조 변경 시 선택자 업데이트가 필요할 수 있습니다
- 개인 학습/연구 목적으로만 사용하세요

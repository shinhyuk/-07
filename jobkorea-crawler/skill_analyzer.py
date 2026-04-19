"""
Claude API 기반 채용공고 스킬 분석기
- 공고 설명에서 기술 스택, 역량, 난이도를 자동 추정
- 배치 처리로 API 호출 최소화
"""

import anthropic
import json
import logging
import time
from dataclasses import dataclass, field, asdict

log = logging.getLogger(__name__)

SKILL_ANALYSIS_PROMPT = """\
당신은 채용공고 분석 전문가입니다. 아래 채용공고 정보를 분석하여 JSON 형식으로 결과를 반환하세요.

## 채용공고
- 제목: {title}
- 회사: {company}
- 공고 내용:
{description}

## 분석 항목

다음 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요:

{{
  "hard_skills": ["기술스킬1", "기술스킬2", ...],
  "soft_skills": ["소프트스킬1", "소프트스킬2", ...],
  "tools": ["도구/플랫폼1", "도구/플랫폼2", ...],
  "frameworks": ["프레임워크1", "프레임워크2", ...],
  "languages": ["프로그래밍언어1", "프로그래밍언어2", ...],
  "certifications": ["관련자격증1", "관련자격증2", ...],
  "experience_level": "junior|mid|senior|lead",
  "difficulty_score": 1~10,
  "role_category": "백엔드|프론트엔드|풀스택|데이터|AI/ML|DevOps|모바일|보안|QA|PM|디자인|기타",
  "salary_estimate": "추정 연봉 범위 (예: 4000~6000만원)",
  "summary": "이 포지션에 대한 한 줄 요약"
}}

규칙:
- 공고에 명시되지 않았더라도 맥락상 필요한 스킬을 추정하여 포함
- hard_skills: 기술적 역량 (알고리즘, 설계 패턴, DB 설계 등)
- tools: 구체적 도구/서비스 (AWS, Docker, Jira 등)
- frameworks: 프레임워크/라이브러리 (React, Spring, Django 등)
- languages: 프로그래밍 언어만
- certifications: 이 직무에 도움되는 자격증 추천
- difficulty_score: 1(매우 쉬움) ~ 10(최상위 전문가급)
- salary_estimate: 경력, 직무, 회사 규모 기반 추정"""


@dataclass
class SkillAnalysis:
    hard_skills: list = field(default_factory=list)
    soft_skills: list = field(default_factory=list)
    tools: list = field(default_factory=list)
    frameworks: list = field(default_factory=list)
    languages: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    experience_level: str = ""
    difficulty_score: int = 0
    role_category: str = ""
    salary_estimate: str = ""
    summary: str = ""


class SkillAnalyzer:
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.request_count = 0

    def analyze(self, title: str, company: str, description: str) -> SkillAnalysis:
        if not description or len(description.strip()) < 20:
            log.debug(f"설명이 너무 짧아 분석 생략: {title}")
            return SkillAnalysis()

        prompt = SKILL_ANALYSIS_PROMPT.format(
            title=title,
            company=company,
            description=description[:2500],
        )

        for attempt in range(3):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                self.request_count += 1

                raw = message.content[0].text.strip()
                # JSON 블록 추출
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                    raw = raw.strip()

                data = json.loads(raw)
                return SkillAnalysis(**{
                    k: v for k, v in data.items()
                    if k in SkillAnalysis.__dataclass_fields__
                })

            except anthropic.RateLimitError:
                wait = (attempt + 1) * 15
                log.warning(f"API Rate limit. {wait}초 대기...")
                time.sleep(wait)
            except json.JSONDecodeError as e:
                log.warning(f"JSON 파싱 실패 (시도 {attempt+1}): {e}")
                time.sleep(2)
            except anthropic.APIError as e:
                log.error(f"API 오류: {e}")
                return SkillAnalysis()

        return SkillAnalysis()

    def analyze_batch(self, jobs: list, delay: float = 1.0) -> list[SkillAnalysis]:
        results = []
        for i, job in enumerate(jobs):
            log.info(f"스킬 분석 중... ({i+1}/{len(jobs)}) {job.get('title', '')[:40]}")

            analysis = self.analyze(
                title=job.get("title", ""),
                company=job.get("company", ""),
                description=job.get("description", ""),
            )
            results.append(analysis)
            time.sleep(delay)

        log.info(f"스킬 분석 완료! API 호출 횟수: {self.request_count}")
        return results

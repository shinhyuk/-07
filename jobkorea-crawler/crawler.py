"""
잡코리아 채용공고 크롤러
- 키워드 기반 채용공고 수집
- 상세 페이지 파싱
- CSV/JSON 저장
"""

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import json
import csv
import os
import re
import logging
from datetime import datetime
from urllib.parse import urlencode, quote
from tqdm import tqdm
from dataclasses import dataclass, asdict, field
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


@dataclass
class JobPosting:
    title: str = ""
    company: str = ""
    location: str = ""
    experience: str = ""
    education: str = ""
    employment_type: str = ""
    salary: str = ""
    deadline: str = ""
    skills: list = field(default_factory=list)
    url: str = ""
    description: str = ""
    industry: str = ""
    posted_date: str = ""
    scraped_at: str = ""


class JobKoreaCrawler:
    BASE_URL = "https://www.jobkorea.co.kr"
    SEARCH_URL = "https://www.jobkorea.co.kr/Search"
    LIST_API_URL = "https://www.jobkorea.co.kr/Search/Ajax/GiList"

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.ua = UserAgent()
        self._update_headers()
        self.results: list[JobPosting] = []
        self.output_dir = self.config.get("output_dir", "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_config(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            log.warning("config.json 없음, 기본 설정 사용")
            return {
                "search_keywords": ["python"],
                "max_pages": 5,
                "delay_between_requests": 1.5,
                "output_format": "both",
                "output_dir": "output",
            }

    def _update_headers(self):
        self.session.headers.update({
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": self.BASE_URL,
        })

    def _request(self, url: str, params: dict = None, method: str = "GET") -> Optional[requests.Response]:
        delay = self.config.get("delay_between_requests", 1.5)
        time.sleep(delay)

        for attempt in range(3):
            try:
                self._update_headers()
                if method == "POST":
                    resp = self.session.post(url, data=params, timeout=15)
                else:
                    resp = self.session.get(url, params=params, timeout=15)

                if resp.status_code == 200:
                    return resp

                if resp.status_code == 429:
                    wait = (attempt + 1) * 10
                    log.warning(f"Rate limited. {wait}초 대기...")
                    time.sleep(wait)
                    continue

                log.error(f"HTTP {resp.status_code}: {url}")
                return None

            except requests.RequestException as e:
                log.error(f"요청 실패 (시도 {attempt+1}/3): {e}")
                time.sleep(3 * (attempt + 1))

        return None

    def _init_session(self, keyword: str):
        """검색 페이지 초기 접근으로 쿠키/세션 설정"""
        params = {"stext": keyword, "tabType": "recruit"}
        self._request(self.SEARCH_URL, params=params)

    def search_jobs(self, keyword: str, max_pages: int = 0) -> list[dict]:
        """키워드로 채용공고 목록 검색"""
        log.info(f'검색 키워드: "{keyword}"')
        self._init_session(keyword)

        all_jobs = []
        page = 1

        with tqdm(desc=f"[{keyword}] 페이지 수집", unit="page") as pbar:
            while True:
                if max_pages > 0 and page > max_pages:
                    break

                jobs = self._fetch_list_page(keyword, page)
                if not jobs:
                    log.info(f"페이지 {page}: 결과 없음. 수집 종료.")
                    break

                all_jobs.extend(jobs)
                pbar.update(1)
                pbar.set_postfix({"총 공고": len(all_jobs)})
                page += 1

        log.info(f'"{keyword}" 총 {len(all_jobs)}개 공고 목록 수집 완료')
        return all_jobs

    def _fetch_list_page(self, keyword: str, page: int) -> list[dict]:
        """검색 결과 목록 페이지 파싱"""
        params = {
            "stext": keyword,
            "tabType": "recruit",
            "Page_No": page,
            "ord": "RegDt",
        }

        resp = self._request(self.SEARCH_URL, params=params)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        # 채용공고 목록 파싱
        job_items = soup.select("article.list-item") or soup.select("li.list-post")

        if not job_items:
            # 대체 선택자
            job_items = soup.select("div.recruit-info") or soup.select("div.post-list-info")

        if not job_items:
            # 테이블 형태
            job_items = soup.select("tr.devlotion_wrap") or soup.select("div.list-default")

        for item in job_items:
            job = self._parse_list_item(item)
            if job and job.get("url"):
                jobs.append(job)

        return jobs

    def _parse_list_item(self, item) -> Optional[dict]:
        """목록 아이템에서 기본 정보 추출"""
        try:
            # 제목 & URL
            title_el = (
                item.select_one("a.list-item-title") or
                item.select_one("a.title") or
                item.select_one("div.post-list-info a") or
                item.select_one("a[href*='Recruit']") or
                item.select_one("a.dev_view")
            )

            if not title_el:
                return None

            title = title_el.get_text(strip=True)
            url = title_el.get("href", "")
            if url and not url.startswith("http"):
                url = self.BASE_URL + url

            # 회사명
            company_el = (
                item.select_one("a.list-item-corp") or
                item.select_one("a.corp-name") or
                item.select_one("div.post-list-corp a") or
                item.select_one("a[href*='company']") or
                item.select_one("a.dev_corp")
            )
            company = company_el.get_text(strip=True) if company_el else ""

            # 메타 정보 (경력, 학력, 지역 등)
            meta_items = (
                item.select("span.chip-information-item") or
                item.select("p.option span") or
                item.select("span.cell") or
                item.select("div.post-list-info span")
            )

            experience = ""
            education = ""
            location = ""
            employment_type = ""

            for idx, meta in enumerate(meta_items):
                text = meta.get_text(strip=True)
                if any(k in text for k in ["경력", "신입", "년"]):
                    experience = text
                elif any(k in text for k in ["대졸", "초대졸", "고졸", "학력", "석사", "박사", "무관"]):
                    education = text
                elif any(k in text for k in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]):
                    location = text
                elif any(k in text for k in ["정규직", "계약직", "인턴", "파견", "프리랜서", "아르바이트"]):
                    employment_type = text

            # 마감일
            deadline_el = (
                item.select_one("span.date") or
                item.select_one("span.deadline") or
                item.select_one("p.option span.date")
            )
            deadline = deadline_el.get_text(strip=True) if deadline_el else ""

            return {
                "title": title,
                "company": company,
                "url": url,
                "experience": experience,
                "education": education,
                "location": location,
                "employment_type": employment_type,
                "deadline": deadline,
            }

        except Exception as e:
            log.debug(f"목록 파싱 오류: {e}")
            return None

    def fetch_detail(self, job_url: str) -> dict:
        """채용공고 상세 페이지에서 추가 정보 수집"""
        resp = self._request(job_url)
        if not resp:
            return {}

        soup = BeautifulSoup(resp.text, "lxml")
        detail = {}

        try:
            # 상세 설명
            desc_el = (
                soup.select_one("div.view-detail-content") or
                soup.select_one("div.tbRow") or
                soup.select_one("div.view-content") or
                soup.select_one("div#divContent") or
                soup.select_one("div.recruit-view-body")
            )
            if desc_el:
                detail["description"] = desc_el.get_text(separator="\n", strip=True)[:3000]

            # 기술 스택 / 우대사항
            skills = []
            skill_els = soup.select("span.chip-keyword") or soup.select("li.tag") or soup.select("span.tag")
            for s in skill_els:
                text = s.get_text(strip=True)
                if text:
                    skills.append(text)
            detail["skills"] = skills

            # 급여
            salary_el = soup.find(string=re.compile(r"급여|연봉|월급"))
            if salary_el:
                parent = salary_el.find_parent()
                if parent:
                    sibling = parent.find_next_sibling()
                    if sibling:
                        detail["salary"] = sibling.get_text(strip=True)

            # 산업/업종
            industry_el = soup.find(string=re.compile(r"업종|산업"))
            if industry_el:
                parent = industry_el.find_parent()
                if parent:
                    sibling = parent.find_next_sibling()
                    if sibling:
                        detail["industry"] = sibling.get_text(strip=True)

        except Exception as e:
            log.debug(f"상세 파싱 오류: {e}")

        return detail

    def crawl(self):
        """전체 크롤링 실행"""
        keywords = self.config.get("search_keywords", ["python"])
        max_pages = self.config.get("max_pages", 0)

        log.info("=" * 60)
        log.info("잡코리아 채용공고 크롤러 시작")
        log.info(f"키워드: {keywords}")
        log.info(f"최대 페이지: {'무제한' if max_pages == 0 else max_pages}")
        log.info("=" * 60)

        all_jobs = []
        for keyword in keywords:
            jobs = self.search_jobs(keyword, max_pages)
            all_jobs.extend(jobs)

        # URL 기준 중복 제거
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                unique_jobs.append(job)

        log.info(f"중복 제거 후 총 {len(unique_jobs)}개 공고")

        # 상세 페이지 크롤링
        log.info("상세 페이지 수집 중...")
        for job in tqdm(unique_jobs, desc="상세 수집", unit="건"):
            detail = self.fetch_detail(job["url"])

            posting = JobPosting(
                title=job.get("title", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                experience=job.get("experience", ""),
                education=job.get("education", ""),
                employment_type=job.get("employment_type", ""),
                salary=detail.get("salary", ""),
                deadline=job.get("deadline", ""),
                skills=detail.get("skills", []),
                url=job.get("url", ""),
                description=detail.get("description", ""),
                industry=detail.get("industry", ""),
                scraped_at=datetime.now().isoformat(),
            )
            self.results.append(posting)

        log.info(f"크롤링 완료! 총 {len(self.results)}개 채용공고 수집")
        self._save()

    def _save(self):
        """결과 저장"""
        fmt = self.config.get("output_format", "both")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if fmt in ("csv", "both"):
            self._save_csv(timestamp)
        if fmt in ("json", "both"):
            self._save_json(timestamp)

    def _save_csv(self, timestamp: str):
        filepath = os.path.join(self.output_dir, f"jobkorea_{timestamp}.csv")
        if not self.results:
            log.warning("저장할 데이터 없음")
            return

        fieldnames = [
            "title", "company", "location", "experience", "education",
            "employment_type", "salary", "deadline", "skills",
            "url", "industry", "posted_date", "scraped_at",
        ]

        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for job in self.results:
                row = asdict(job)
                row["skills"] = ", ".join(row["skills"])
                row.pop("description", None)
                writer.writerow(row)

        log.info(f"CSV 저장: {filepath}")

    def _save_json(self, timestamp: str):
        filepath = os.path.join(self.output_dir, f"jobkorea_{timestamp}.json")
        if not self.results:
            log.warning("저장할 데이터 없음")
            return

        data = [asdict(job) for job in self.results]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        log.info(f"JSON 저장: {filepath}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="잡코리아 채용공고 크롤러")
    parser.add_argument("-k", "--keywords", nargs="+", help="검색 키워드 (예: python 백엔드)")
    parser.add_argument("-p", "--pages", type=int, default=0, help="최대 페이지 수 (0=무제한)")
    parser.add_argument("-d", "--delay", type=float, default=1.5, help="요청 간 대기 시간(초)")
    parser.add_argument("-o", "--output", choices=["csv", "json", "both"], default="both", help="출력 형식")
    parser.add_argument("-c", "--config", default="config.json", help="설정 파일 경로")
    args = parser.parse_args()

    crawler = JobKoreaCrawler(config_path=args.config)

    if args.keywords:
        crawler.config["search_keywords"] = args.keywords
    if args.pages:
        crawler.config["max_pages"] = args.pages
    if args.delay:
        crawler.config["delay_between_requests"] = args.delay
    if args.output:
        crawler.config["output_format"] = args.output

    crawler.crawl()


if __name__ == "__main__":
    main()

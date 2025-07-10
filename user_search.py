import json
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock
from typing import List, Dict, Optional
from urllib.parse import quote

class JobSearcher:
    def __init__(self):
        self.jobs_db = Path("processed_data/posted_jobs.json")
        self.lock = Lock()
        self._categories = {}
        self._locations = {}
        self._jobs_cache = []
        self._initialize_resources()

    def _initialize_resources(self):
        self._load_categories()
        self._load_locations()
        self._refresh_jobs_cache()

    def _load_categories(self):
        try:
            with open("categories.json", encoding="utf-8") as f:
                self._categories = json.load(f)
                for cat_data in self._categories.values():
                    cat_data["keywords_lower"] = [
                        str(kw).lower() for kw in cat_data.get("keywords", [])
                    ]
        except Exception as e:
            print(f"هەڵە لە بارکردنی بەشەکان: {e}")
            self._categories = {}

    def _load_locations(self):
        try:
            with open("locations.json", encoding="utf-8") as f:
                self._locations = json.load(f)
                for loc_data in self._locations.values():
                    loc_data["aliases_lower"] = [
                        str(a).strip().lower() for a in loc_data.get("aliases", [])
                    ]
        except Exception as e:
            print(f"هەڵە لە بارکردنی شوێنەکان: {e}")
            self._locations = {}

    def _refresh_jobs_cache(self):
        with self.lock:
            try:
                with open(self.jobs_db, encoding="utf-8") as f:
                    raw_data = json.load(f)
                    self._jobs_cache = [
                        job for job in raw_data
                        if isinstance(job, dict) and job.get('posted_at')
                    ]
            except Exception as e:
                print(f"هەڵە لە بارکردنی کارەکان: {e}")
                self._jobs_cache = []

    @property
    def categories(self):
        return self._categories

    @property
    def locations(self):
        return self._locations

    def search(self, category_key: str, location_input: Optional[str], max_days: str) -> List[Dict]:
        try:
            if not category_key:
                return []

            keywords = self._categories.get(category_key, {}).get("keywords_lower", [])
            if not keywords:
                return []

            # Location normalization & filtering
            location_key = None
            if location_input:
                loc_in = str(location_input).strip().lower()
                if loc_in == "all" or loc_in == "هەموو شوێنەکان":
                    location_key = None
                else:
                    for loc_key, loc_data in self._locations.items():
                        if loc_in in loc_data.get("aliases_lower", []):
                            location_key = loc_key
                            break

            # Time filtering
            now = datetime.now()
            try:
                days = int(max_days)
                cutoff_dt = now - timedelta(days=days)
            except ValueError:
                cutoff_dt = now - timedelta(days=7)

            cutoff_ts = int(cutoff_dt.timestamp())
            now_ts = int(now.timestamp())

            results = []
            for job in self._jobs_cache:
                if self._job_matches(job, keywords, location_key, cutoff_ts, now_ts):
                    results.append(self._format_job(job))

            return results
        except Exception as e:
            print(f"هەڵە لە گەڕان: {e}")
            return []

    def _job_matches(self, job: Dict, keywords: List[str], location: Optional[str], cutoff: int, now_ts: int) -> bool:
        try:
            job_posted = int(job.get("posted_at", 0))
            if not (cutoff <= job_posted <= now_ts):
                return False
        except Exception:
            return False

        # Strict location matching
        if location is not None:
            job_loc = str(job.get("location", "")).strip().lower()
            if len(job_loc) <= 1:  # Block single-character locations
                return False
            loc_aliases = self._locations.get(location, {}).get("aliases_lower", [])
            if job_loc not in loc_aliases:
                return False

        # Category matching
        job_cat = str(job.get("category", "")).lower()
        job_cat_kurdish = str(job.get("category_kurdish", "")).lower()
        return any(kw in job_cat for kw in keywords) or any(kw in job_cat_kurdish for kw in keywords)

    def _format_job(self, job: Dict) -> Dict:
        contact = job.get("contact", "")
        email = job.get("email", "")
        contact_display = email if email else contact
        contact_type = "📧 ئیمەیڵ" if email else "📞 پەیوەندی"

        return {
            "id": job.get("id", ""),
            "title": job.get("title", "نادیار"),
            "category": job.get("category", ""),
            "category_kurdish": job.get("category_kurdish", ""),
            "location": job.get("location", "نادیار"),
            "salary": job.get("salary", "نادیار"),
            "requirements": job.get("requirements", "نادیار"),
            "description": job.get("description", "نادیار"),
            "contact": contact_display,
            "contact_type": contact_type,
            "email": email,
            "phone": contact if not email else "",
            "posted_at": job.get("posted_at", 0),
            "posted_time": self._format_posted_time(job.get("posted_at", 0)),
            "channel_message_id": job.get("channel_message_id", ""),
            "cv_method": job.get("cv_method", 1),
            "messaging_app": job.get("messaging_app", 1)
        }

    def _format_posted_time(self, timestamp: int) -> str:
        if not timestamp:
            return "نادیار"
        try:
            delta = datetime.now() - datetime.fromtimestamp(timestamp)
            if delta.days == 0:
                return "ئەمڕۆ"
            elif delta.days == 1:
                return "دوێنێ"
            elif delta.days < 7:
                return f"{delta.days} ڕۆژ لەمەوبەر"
            elif delta.days < 30:
                weeks = delta.days // 7
                return f"{weeks} هەفتە لەمەوبەر" if weeks > 1 else "هەفتە لەمەوبەر"
            months = delta.days // 30
            return f"{months} مانگ لەمەوبەر" if months > 1 else "مانگ لەمەوبەر"
        except Exception:
            return "نادیار"
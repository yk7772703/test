"""
Regulatory updates service.
Monitors RSS/Atom feeds from:
  - US Federal Register (regulations.gov / federalregister.gov)
  - UK FCA (fca.org.uk)
  - Canada OSFI (osfi-bsif.gc.ca)
  - GDPR / EU (edpb.europa.eu)
"""
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.models.compliance import RegulatoryUpdate, AlertSeverity

logger = logging.getLogger(__name__)

FEEDS = [
    {
        "jurisdiction": "US",
        "category": "Regulatory",
        "name": "US Federal Register - Financial",
        "url": "https://www.federalregister.gov/api/v1/articles.json?conditions[agencies][]=financial-crimes-enforcement-network&per_page=20&order=newest",
        "type": "json_federal_register",
    },
    {
        "jurisdiction": "US",
        "category": "Sanctions",
        "name": "US OFAC Recent Actions",
        "url": "https://home.treasury.gov/rss.xml",
        "type": "rss",
    },
    {
        "jurisdiction": "UK",
        "category": "Regulatory",
        "name": "UK FCA News",
        "url": "https://www.fca.org.uk/news/rss.xml",
        "type": "rss",
    },
    {
        "jurisdiction": "EU",
        "category": "GDPR",
        "name": "EDPB News",
        "url": "https://edpb.europa.eu/news/news_en.rss",
        "type": "rss",
    },
    {
        "jurisdiction": "CA",
        "category": "Regulatory",
        "name": "OSFI News",
        "url": "https://www.osfi-bsif.gc.ca/en/rss-feed",
        "type": "rss",
    },
]


def _parse_rss(content: bytes, jurisdiction: str, category: str) -> list[dict]:
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        items = []
        for item in root.findall(".//item")[:10]:
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            items.append({
                "jurisdiction": jurisdiction,
                "category": category,
                "title": title[:500] if title else "No title",
                "summary": description[:2000] if description else "",
                "source_url": link,
                "severity": AlertSeverity.MEDIUM,
                "requires_action": False,
            })
        return items
    except Exception as e:
        logger.error("RSS parse error: %s", e)
        return []


def _parse_federal_register(content: bytes, jurisdiction: str, category: str) -> list[dict]:
    try:
        import json
        data = json.loads(content)
        items = []
        for article in data.get("results", [])[:10]:
            items.append({
                "jurisdiction": jurisdiction,
                "category": category,
                "title": article.get("title", "")[:500],
                "summary": article.get("abstract", "")[:2000],
                "source_url": article.get("html_url", ""),
                "severity": AlertSeverity.MEDIUM,
                "requires_action": True,
            })
        return items
    except Exception as e:
        logger.error("Federal Register parse error: %s", e)
        return []


async def fetch_regulatory_updates(db: Session) -> int:
    """Fetch regulatory updates from all feeds. Returns count of new items."""
    total = 0
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for feed in FEEDS:
            try:
                resp = await client.get(
                    feed["url"],
                    headers={"User-Agent": "ComplianceERP/1.0", "Accept": "application/rss+xml, application/json, text/xml"},
                )
                resp.raise_for_status()
                content = resp.content

                if feed["type"] == "rss":
                    items = _parse_rss(content, feed["jurisdiction"], feed["category"])
                elif feed["type"] == "json_federal_register":
                    items = _parse_federal_register(content, feed["jurisdiction"], feed["category"])
                else:
                    items = []

                for item_data in items:
                    # Avoid duplicates by checking title + jurisdiction
                    existing = db.query(RegulatoryUpdate).filter(
                        RegulatoryUpdate.title == item_data["title"],
                        RegulatoryUpdate.jurisdiction == item_data["jurisdiction"],
                    ).first()
                    if not existing:
                        update = RegulatoryUpdate(**item_data)
                        db.add(update)
                        total += 1

                db.commit()
            except Exception as e:
                logger.error("Feed fetch error for %s: %s", feed["name"], e)

    logger.info("Fetched %d new regulatory updates", total)
    return total

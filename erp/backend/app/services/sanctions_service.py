"""
Sanctions screening service.
Fetches and updates sanction lists from:
  - US OFAC (SDN + Consolidated) — treasury.gov free download
  - UK HM Treasury — gov.uk CSV
  - UN Security Council — scsanctions.un.org XML
  - EU Financial Sanctions — ec.europa.eu XML
  - Canada SEMA — international.gc.ca XML
"""
import hashlib
import logging
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.compliance import (
    ComplianceAlert, AlertSeverity, AlertStatus,
    SanctionedEntity, SanctionList, SanctionListSource
)

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.85


def _similarity(a: str, b: str) -> float:
    a, b = a.lower().strip(), b.lower().strip()
    return SequenceMatcher(None, a, b).ratio()


def _hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def _fetch(url: str) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "ComplianceERP/1.0"})
            resp.raise_for_status()
            return resp.content
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return None


def _parse_ofac_xml(content: bytes) -> list[dict]:
    """Parse OFAC SDN XML into list of entity dicts."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        ns = {"o": "http://tempuri.org/sdnList.xsd"}
        entities = []
        for entry in root.findall(".//o:sdnEntry", ns):
            uid = entry.findtext("o:uid", namespaces=ns)
            last_name = entry.findtext("o:lastName", namespaces=ns, default="")
            first_name = entry.findtext("o:firstName", namespaces=ns, default="")
            sdn_type = entry.findtext("o:sdnType", namespaces=ns, default="")

            names = [{"type": "primary", "name": f"{last_name} {first_name}".strip()}]
            for aka in entry.findall(".//o:aka", ns):
                aka_type = aka.findtext("o:type", namespaces=ns, default="")
                aka_ln = aka.findtext("o:lastName", namespaces=ns, default="")
                aka_fn = aka.findtext("o:firstName", namespaces=ns, default="")
                names.append({"type": aka_type, "name": f"{aka_ln} {aka_fn}".strip()})

            programs = [p.text for p in entry.findall(".//o:program", ns) if p.text]
            addresses = []
            for addr in entry.findall(".//o:address", ns):
                addresses.append({
                    "city": addr.findtext("o:city", namespaces=ns),
                    "country": addr.findtext("o:country", namespaces=ns),
                })

            entities.append({
                "external_id": uid,
                "entity_type": sdn_type.lower() if sdn_type else "individual",
                "names": names,
                "addresses": addresses,
                "programs": programs,
                "nationalities": [],
                "dates_of_birth": [],
                "id_numbers": [],
                "remarks": entry.findtext("o:remarks", namespaces=ns),
            })
        return entities
    except Exception as e:
        logger.error("OFAC XML parse error: %s", e)
        return []


def _parse_uk_hmt_csv(content: bytes) -> list[dict]:
    """Parse UK HM Treasury CSV sanctions list."""
    try:
        import csv
        import io
        reader = csv.DictReader(io.StringIO(content.decode("utf-8", errors="replace")))
        entities = []
        for row in reader:
            name = row.get("Name 6", "") or row.get("Name 1", "")
            if not name:
                continue
            entities.append({
                "external_id": row.get("Unique ID", ""),
                "entity_type": row.get("Group Type", "individual").lower(),
                "names": [{"type": "primary", "name": name}],
                "addresses": [{"country": row.get("Country", "")}],
                "programs": [row.get("Regime", "")],
                "nationalities": [row.get("Nationality", "")] if row.get("Nationality") else [],
                "dates_of_birth": [row.get("DOB", "")] if row.get("DOB") else [],
                "id_numbers": [],
                "remarks": row.get("Other Information", ""),
            })
        return entities
    except Exception as e:
        logger.error("UK HMT CSV parse error: %s", e)
        return []


def _parse_un_xml(content: bytes) -> list[dict]:
    """Parse UN Security Council Consolidated Sanctions XML."""
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)
        entities = []
        for ind in root.findall(".//INDIVIDUAL"):
            first = ind.findtext("FIRST_NAME", "")
            second = ind.findtext("SECOND_NAME", "")
            third = ind.findtext("THIRD_NAME", "")
            name = " ".join(filter(None, [first, second, third]))
            dataid = ind.findtext("DATAID", "")
            entities.append({
                "external_id": f"UN-{dataid}",
                "entity_type": "individual",
                "names": [{"type": "primary", "name": name}],
                "addresses": [],
                "programs": ["UN Security Council"],
                "nationalities": [ind.findtext("NATIONALITY/VALUE", "")],
                "dates_of_birth": [ind.findtext("INDIVIDUAL_DATE_OF_BIRTH/DATE", "")],
                "id_numbers": [],
                "remarks": ind.findtext("COMMENTS1", ""),
            })
        for ent in root.findall(".//ENTITY"):
            name = ent.findtext("FIRST_NAME", "")
            dataid = ent.findtext("DATAID", "")
            entities.append({
                "external_id": f"UN-{dataid}",
                "entity_type": "entity",
                "names": [{"type": "primary", "name": name}],
                "addresses": [],
                "programs": ["UN Security Council"],
                "nationalities": [],
                "dates_of_birth": [],
                "id_numbers": [],
                "remarks": ent.findtext("COMMENTS1", ""),
            })
        return entities
    except Exception as e:
        logger.error("UN XML parse error: %s", e)
        return []


async def update_sanction_list(source: SanctionListSource, url: str, db: Session, parser) -> int:
    """Download, parse, and upsert a sanction list. Returns count of entities saved."""
    content = await _fetch(url)
    if not content:
        return 0

    checksum = _hash_content(content)

    existing = db.query(SanctionList).filter(
        SanctionList.source == source, SanctionList.is_current == True
    ).first()

    if existing and existing.checksum == checksum:
        logger.info("Sanction list %s unchanged (checksum match)", source.value)
        return existing.entry_count

    # Mark old list inactive
    if existing:
        existing.is_current = False
        db.add(existing)

    entities_data = parser(content)

    sanction_list = SanctionList(
        source=source,
        last_updated=datetime.now(timezone.utc),
        entry_count=len(entities_data),
        checksum=checksum,
        is_current=True,
    )
    db.add(sanction_list)
    db.flush()

    # Bulk insert entities
    for e in entities_data:
        entity = SanctionedEntity(
            sanction_list_id=sanction_list.id,
            **e,
        )
        db.add(entity)

    db.commit()
    logger.info("Sanction list %s updated: %d entities", source.value, len(entities_data))
    return len(entities_data)


async def run_daily_update(db: Session) -> dict:
    """Run daily sanctions update for all sources."""
    results = {}

    tasks = [
        (SanctionListSource.OFAC_SDN, settings.OFAC_SDN_URL, _parse_ofac_xml),
        (SanctionListSource.UK_HMT, settings.UK_SANCTIONS_URL, _parse_uk_hmt_csv),
        (SanctionListSource.UN, settings.UN_SANCTIONS_URL, _parse_un_xml),
    ]

    for source, url, parser in tasks:
        try:
            count = await update_sanction_list(source, url, db, parser)
            results[source.value] = {"status": "ok", "count": count}
        except Exception as e:
            logger.error("Failed to update %s: %s", source.value, e)
            results[source.value] = {"status": "error", "error": str(e)}

    return results


def screen_name(name: str, db: Session, threshold: float = MATCH_THRESHOLD) -> list[dict]:
    """Screen a name against all active sanctioned entities. Returns matches above threshold."""
    if not name or len(name.strip()) < 3:
        return []

    name_clean = name.lower().strip()
    matches = []

    # Get all active entities
    entities = db.query(SanctionedEntity).filter(SanctionedEntity.is_active == True).all()

    for entity in entities:
        best_score = 0.0
        best_match_name = ""

        for n in (entity.names or []):
            candidate = n.get("name", "")
            if not candidate:
                continue
            score = _similarity(name_clean, candidate)
            if score > best_score:
                best_score = score
                best_match_name = candidate

        if best_score >= threshold:
            sanction_list = db.query(SanctionList).filter(
                SanctionList.id == entity.sanction_list_id
            ).first()
            matches.append({
                "entity_id": str(entity.id),
                "matched_name": best_match_name,
                "score": round(best_score, 3),
                "source": sanction_list.source.value if sanction_list else "unknown",
                "entity_type": entity.entity_type,
                "programs": entity.programs,
            })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


def create_sanctions_alert(
    entity_type: str,
    entity_id,
    entity_name: str,
    matches: list[dict],
    db: Session,
) -> Optional[ComplianceAlert]:
    if not matches:
        return None

    top_match = matches[0]
    severity = (
        AlertSeverity.CRITICAL if top_match["score"] >= 0.95
        else AlertSeverity.HIGH if top_match["score"] >= 0.90
        else AlertSeverity.MEDIUM
    )

    alert = ComplianceAlert(
        alert_type="sanctions_match",
        severity=severity,
        status=AlertStatus.OPEN,
        title=f"Possible sanctions match: {entity_name}",
        description=(
            f"Entity '{entity_name}' matched '{top_match['matched_name']}' "
            f"on {top_match['source']} list (score: {top_match['score']:.1%})"
        ),
        entity_type=entity_type,
        entity_id=entity_id,
        match_score=top_match["score"],
        alert_metadata={"all_matches": matches},
    )
    db.add(alert)
    db.commit()
    return alert

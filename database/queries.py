from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database.models import DiscoveredTender

class Queries:
    @staticmethod
    def upsert_tenders(db: Session, tenders: List[Dict[str, Any]]):
        for tender in tenders:
            existing = db.query(DiscoveredTender).filter_by(
                tender_id=tender.get('tender_id', '')
            ).first()
            if existing:
                continue
            db.add(DiscoveredTender(
                tender_id=tender.get('tender_id'),
                source=tender.get('source'),
                title=tender.get('title', '')[:500],
                description=tender.get('description', '')[:3000],
                deadline=tender.get('deadline'),
                estimated_value=tender.get('estimated_value', 0),
                organization=tender.get('organization', ''),
                location=tender.get('location', ''),
                document_url=tender.get('document_url', ''),
                raw_data=tender
            ))
        db.commit()
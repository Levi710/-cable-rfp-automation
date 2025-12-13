import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import json
import csv
from pathlib import Path

logger = logging.getLogger(__name__)

class SalesAgent:
    """Sales Agent: Identifies RFPs due in next 3 months, summarizes, and selects top RFP."""
    
    def __init__(self):
        # Load client policy and experience for smarter qualification
        self.policy = self._load_client_policy()
        self.experience = self._load_client_experience()
        self.rotation_file = Path('output/last_selected.json')
    
    def _load_client_policy(self) -> Dict:
        try:
            p = Path(__file__).resolve().parent.parent / 'config' / 'client_policy.json'
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {
                'qualification': {'weights': {'deadline': 0.3, 'product_coverage': 0.3, 'past_experience': 0.25, 'estimated_value': 0.15}, 'min_score': 0.6},
                'capabilities': {'voltage_classes': ['11 kV', '22 kV', '33 kV', '440V']}
            }
    
    def _load_client_experience(self) -> Dict:
        try:
            p = Path(__file__).resolve().parent.parent / 'data' / 'client_experience.json'
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {'organizations': []}
    
    def filter_by_deadline(self, tenders: List[Dict]) -> List[Dict]:
        """Filter tenders due for submission in next 3 months (90 days)."""
        
        from datetime import timezone
        
        current_date = datetime.now(timezone.utc)
        cutoff_date = current_date + timedelta(days=90)
        
        filtered = []
        for tender in tenders:
            deadline_str = tender.get('deadline')
            if not deadline_str:
                # If no deadline, include it (assume it's valid)
                filtered.append(tender)
                continue
                
            try:
                # Parse ISO format deadline
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                
                # Make sure deadline is timezone-aware
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                
                # Check if deadline is between now and 3 months
                if current_date <= deadline <= cutoff_date:
                    filtered.append(tender)
            except Exception as e:
                logger.warning(f"Could not parse deadline for tender {tender.get('tender_id')}: {e}")
                # Include tender even if date parsing fails
                filtered.append(tender)
                continue
        
        logger.info(f"Filtered {len(filtered)} tenders with deadlines in next 3 months (from {len(tenders)} total)")
        return filtered
    
    def summarize_rfp(self, tender: Dict) -> Dict:
        """Create comprehensive RFP summary with due date and requirements."""
        
        title = tender.get('title', '')
        description = tender.get('description', '')
        text = f"{title} {description}".lower()
        
        # Extract product requirements
        product_summary = self._extract_product_requirements(text, tender)
        
        # Extract testing requirements
        test_requirements = self._extract_test_requirements(text, tender)
        
        # Get deadline info
        deadline_str = tender.get('deadline', 'Not specified')
        try:
            deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
            days_until_due = (deadline - datetime.now()).days
        except:
            days_until_due = None
        
        return {
            'tender_id': tender.get('tender_id'),
            'title': title,
            'organization': tender.get('organization', 'Unknown'),
            'estimated_value': tender.get('estimated_value', 0),
            'deadline': deadline_str,
            'days_until_due': days_until_due,
            'location': tender.get('location', 'Unknown'),
            'product_requirements': product_summary,
            'test_requirements': test_requirements,
            'cable_type': self._extract_cable_type(text),
            'voltage_class': tender.get('voltage_class', self._extract_voltage(text)),
            'scope_of_supply': self._extract_scope(text, tender)
        }
    
    def _extract_product_requirements(self, text: str, tender: Dict) -> Dict:
        """Extract product requirements from RFP."""
        
        return {
            'cable_type': self._extract_cable_type(text),
            'voltage': tender.get('voltage_class', self._extract_voltage(text)),
            'length_km': tender.get('length_km', self._extract_length(text)),
            'conductor_material': self._extract_conductor_material(text),
            'insulation_type': self._extract_insulation_type(text),
            'armoring': 'Armored' if 'armor' in text else 'Unarmored',
            'cores': self._extract_cores(text),
            'standards': self._extract_standards(text)
        }
    
    def _extract_test_requirements(self, text: str, tender: Dict) -> List[str]:
        """Extract testing and acceptance requirements."""
        
        test_requirements = []
        
        # Standard tests
        if any(x in text for x in ['routine test', 'acceptance test']):
            test_requirements.append('Routine tests as per applicable standards')
        
        if any(x in text for x in ['type test', 'qualification']):
            test_requirements.append('Type tests for product qualification')
        
        # Specific test types
        if any(x in text for x in ['voltage', 'dielectric', 'withstand']):
            test_requirements.append('High voltage withstand test')
        
        if 'conductor resistance' in text or 'dc resistance' in text:
            test_requirements.append('DC resistance measurement')
        
        if 'insulation resistance' in text:
            test_requirements.append('Insulation resistance test')
        
        if 'partial discharge' in text:
            test_requirements.append('Partial discharge test')
        
        # Visual and physical
        test_requirements.append('Visual inspection and dimensional check')
        test_requirements.append('Mechanical tests (tensile, elongation)')
        
        # Standards-based tests
        standards = self._extract_standards(text)
        if standards:
            test_requirements.append(f'Tests as per {standards[0]}')
        
        return test_requirements if test_requirements else ['Standard acceptance tests']
    
    def _extract_scope(self, text: str, tender: Dict) -> List[Dict]:
        """Extract scope of supply items."""
        
        # For now, create a single item from the main tender
        return [{
            'item_no': 1,
            'description': tender.get('title', 'Cable supply'),
            'cable_type': self._extract_cable_type(text),
            'voltage': tender.get('voltage_class', self._extract_voltage(text)),
            'quantity': tender.get('length_km', 1),
            'unit': 'km'
        }]
    
    def qualify_tender(self, tender: dict) -> dict:
        """Qualify if tender is worth bidding on using client policy (deadline, coverage, experience, value)."""
        
        weights = self.policy.get('qualification', {}).get('weights', {})
        min_score = self.policy.get('qualification', {}).get('min_score', 0.6)
        capabilities = self.policy.get('capabilities', {})
        supported_voltages = set([v.lower() for v in capabilities.get('voltage_classes', [])])
        
        # DEADLINE score (prefer 8-60 days window)
        deadline_score = 0.5
        deadline_str = tender.get('deadline')
        try:
            deadline = datetime.fromisoformat(str(deadline_str).replace('Z', '+00:00'))
            days_until = (deadline - datetime.now()).days
            if days_until <= 7:
                deadline_score = 0.4
            elif days_until <= 30:
                deadline_score = 1.0
            elif days_until <= 60:
                deadline_score = 0.8
            elif days_until <= 90:
                deadline_score = 0.5
            else:
                deadline_score = 0.2
        except Exception:
            deadline_score = 0.5
        
        # PRODUCT COVERAGE score (voltage/type support)
        voltage = (tender.get('voltage_class') or '').lower()
        coverage_score = 1.0 if (not voltage or voltage in supported_voltages) else 0.5
        
        # PAST EXPERIENCE score
        org = tender.get('organization', '')
        org_lower = org.lower()
        exp_orgs = [o for o in self.experience.get('organizations', []) if o.get('name', '').lower() in org_lower]
        experience_score = 1.0 if exp_orgs else 0.6  # modest default if unknown
        
        # ESTIMATED VALUE score
        est_val = tender.get('estimated_value', 0) or 0
        if est_val >= 100_000_000:  # >= Rs 10 Cr
            value_score = 1.0
        elif est_val >= 50_000_000:  # >= Rs 5 Cr
            value_score = 0.85
        elif est_val > 0:
            value_score = 0.7
        else:
            value_score = 0.5
        
        # Aggregate score
        total_w = sum(weights.values()) or 1.0
        final_score = (
            weights.get('deadline', 0.0) * deadline_score +
            weights.get('product_coverage', 0.0) * coverage_score +
            weights.get('past_experience', 0.0) * experience_score +
            weights.get('estimated_value', 0.0) * value_score
        ) / total_w
        
        return {
            'is_qualified': final_score >= min_score,
            'qualification_score': round(final_score, 3),
            'breakdown': {
                'deadline_score': round(deadline_score, 2),
                'coverage_score': round(coverage_score, 2),
                'experience_score': round(experience_score, 2),
                'value_score': round(value_score, 2)
            },
            'cable_type': self._extract_cable_type((tender.get('title', '') + ' ' + tender.get('description', '')).lower())
        }
    
    def calculate_priority(self, tender: dict) -> float:
        """Calculate priority score (0-1) for RFP selection."""
        
        priority = 0.5
        
        # High value tenders (slightly reduced bias)
        estimated_value = tender.get('estimated_value', 0)
        if estimated_value > 100000000:
            priority += 0.20
        elif estimated_value > 50000000:
            priority += 0.10
        
        # Organization prestige (reduced bias)
        org = tender.get('organization', '').lower()
        if any(s in org for s in ['powergrid', 'power grid']):
            priority += 0.05
        elif any(s in org for s in ['ntpc']):
            priority += 0.05
        elif any(s in org for s in ['electricity', 'power', 'grid']):
            priority += 0.05
        
        # Urgency (sooner deadlines get higher priority)
        deadline_str = tender.get('deadline')
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
                days_until = (deadline - datetime.now()).days
                if days_until < 30:
                    priority += 0.10
                elif days_until < 60:
                    priority += 0.05
            except:
                pass
        
        return min(priority, 1.0)
    
    def _load_rotation(self) -> List[str]:
        try:
            if self.rotation_file.exists():
                import json
                data = json.loads(self.rotation_file.read_text(encoding='utf-8'))
                return data.get('last_selected_ids', [])
        except Exception:
            pass
        return []
    
    def _save_rotation(self, tender_ids: List[str]):
        try:
            self.rotation_file.parent.mkdir(parents=True, exist_ok=True)
            import json
            self.rotation_file.write_text(json.dumps({'last_selected_ids': tender_ids}), encoding='utf-8')
        except Exception:
            pass
    
    def select_top_rfp(self, tenders: List[Dict]) -> Optional[Dict]:
        """Select the top 1 RFP to pursue based on combined qualification + priority (with rotation)."""
        
        if not tenders:
            return None
        
        # Rotation: skip last selected if present
        skip_ids = set(self._load_rotation())
        filtered = [t for t in tenders if str(t.get('tender_id')) not in skip_ids] or tenders
        
        # Score each tender
        scored_tenders = []
        for tender in filtered:
            priority = self.calculate_priority(tender)
            qual_score = tender.get('_qualification_score', 0.7)
            combined = min(priority * 0.6 + qual_score * 0.4, 1.0)
            scored_tenders.append({
                'tender': tender,
                'priority_score': priority,
                'qualification_score': qual_score,
                'combined_score': combined
            })
        
        scored_tenders.sort(key=lambda x: x['combined_score'], reverse=True)
        winner = scored_tenders[0]
        top_rfp = winner['tender']
        self._save_rotation([str(top_rfp.get('tender_id'))])
        
        logger.info(
            f"Selected top RFP: {top_rfp.get('tender_id')} | combined={winner['combined_score']:.2f} "
            f"(priority={winner['priority_score']:.2f}, qual={winner['qualification_score']:.2f})"
        )
        
        return top_rfp
    
    def process_rfps(self, tenders: List[Dict]) -> Dict:
        """Complete Sales Agent workflow: filter, summarize, and select."""
        
        # Step 1: Filter by deadline (next 3 months)
        filtered_tenders = self.filter_by_deadline(tenders)
        
        if not filtered_tenders:
            logger.warning("No tenders found with deadlines in next 3 months")
            return {
                'status': 'no_tenders',
                'message': 'No RFPs due in next 3 months',
                'selected_rfp': None
            }
        
        # Step 2: Qualify each tender
        qualified_tenders = []
        for tender in filtered_tenders:
            qualification = self.qualify_tender(tender)
            # attach score for later prioritization
            tender['_qualification_score'] = qualification.get('qualification_score', 0.7)
            tender['_qualification_breakdown'] = qualification.get('breakdown', {})
            if qualification['is_qualified']:
                qualified_tenders.append(tender)
        
        if not qualified_tenders:
            logger.warning("No qualified cable tenders found")
            return {
                'status': 'no_qualified',
                'message': 'No qualified cable RFPs found',
                'selected_rfp': None
            }
        
        # Step 3: Select top RFP
        top_rfp = self.select_top_rfp(qualified_tenders)
        
        # Step 4: Create comprehensive summary
        rfp_summary = self.summarize_rfp(top_rfp)

        # Persist selection to a CSV log for audit/analytics (with extended summary fields)
        try:
            self._append_selection_csv(top_rfp, {
                'combined': scored_tenders[0]['combined_score'] if 'scored_tenders' in locals() else top_rfp.get('_qualification_score', 0.7),
                'priority': self.calculate_priority(top_rfp),
                'qualification': top_rfp.get('_qualification_score', 0.7)
            }, rfp_summary=rfp_summary)
        except Exception:
            pass
        
        logger.info(f"Sales Agent processed {len(tenders)} tenders:")
        logger.info(f"  - Filtered to {len(filtered_tenders)} with deadlines in next 3 months")
        logger.info(f"  - Qualified {len(qualified_tenders)} cable tenders")
        logger.info(f"  - Selected top RFP: {rfp_summary['tender_id']}")
        
        return {
            'status': 'success',
            'total_tenders': len(tenders),
            'filtered_count': len(filtered_tenders),
            'qualified_count': len(qualified_tenders),
            'selected_rfp': top_rfp,
            'rfp_summary': rfp_summary
        }
    
    def _append_selection_csv(self, tender: Dict, scores: Dict, rfp_summary: Optional[Dict] = None):
        """Append the selected RFP to a CSV file for audit/analytics, with extended fields."""
        out_path = Path('output') / 'sales_selected_rfps.csv'
        out_path.parent.mkdir(parents=True, exist_ok=True)
        header = [
            'timestamp', 'tender_id', 'title', 'organization', 'estimated_value',
            'deadline', 'days_until_due', 'priority_score', 'qualification_score', 'combined_score',
            'cable_type', 'voltage', 'length_km', 'cores', 'armoring', 'conductor_material', 'insulation_type', 'standards'
        ]
        write_header = not out_path.exists()
        # Compute days_until_due
        days_until = None
        dl = tender.get('deadline')
        if dl:
            try:
                d = datetime.fromisoformat(str(dl).replace('Z', '+00:00'))
                days_until = (d - datetime.now()).days
            except Exception:
                days_until = None
        # Extended fields from summary
        pr = (rfp_summary or {}).get('product_requirements') or {}
        row = [
            datetime.now().isoformat(timespec='seconds'),
            tender.get('tender_id'),
            tender.get('title'),
            tender.get('organization'),
            tender.get('estimated_value', 0),
            tender.get('deadline'),
            days_until if days_until is not None else '',
            f"{scores.get('priority', 0):.3f}",
            f"{scores.get('qualification', 0):.3f}",
            f"{scores.get('combined', 0):.3f}",
            pr.get('cable_type') or (rfp_summary or {}).get('cable_type') or '',
            pr.get('voltage') or (rfp_summary or {}).get('voltage_class') or '',
            pr.get('length_km') or '',
            pr.get('cores') or '',
            pr.get('armoring') or '',
            pr.get('conductor_material') or '',
            pr.get('insulation_type') or '',
            ', '.join(pr.get('standards', [])) if isinstance(pr.get('standards'), list) else (pr.get('standards') or '')
        ]
        with out_path.open('a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(header)
            w.writerow(row)

    def _extract_cable_type(self, text: str) -> str:
        """Extract cable type from text."""
        
        if 'xlpe' in text:
            return 'XLPE'
        elif 'pvc' in text:
            return 'PVC'
        elif 'armored' in text or 'armoured' in text:
            return 'Armored'
        else:
            return 'General'
    
    def _extract_voltage(self, text: str) -> str:
        """Extract voltage class from text."""
        
        # Look for voltage patterns: 11kV, 33 kV, 440V, etc.
        voltage_pattern = r'(\d+)\s*k?v'
        match = re.search(voltage_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        return 'Unknown'
    
    def _extract_length(self, text: str) -> float:
        """Extract cable length from text."""
        
        # Look for length patterns: 10km, 500 KM, 350 meters
        km_pattern = r'(\d+)\s*km'
        match = re.search(km_pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        
        # Check for meters
        meter_pattern = r'(\d+)\s*meters?'
        match = re.search(meter_pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1)) / 1000
        
        return 0
    
    def _extract_conductor_material(self, text: str) -> str:
        """Extract conductor material."""
        
        if 'aluminum' in text or 'aluminium' in text:
            return 'Aluminum'
        elif 'copper' in text:
            return 'Copper'
        return 'Copper'  # Default
    
    def _extract_insulation_type(self, text: str) -> str:
        """Extract insulation type."""
        
        if 'xlpe' in text:
            return 'XLPE'
        elif 'pvc' in text:
            return 'PVC'
        elif 'epr' in text:
            return 'EPR'
        return 'XLPE'  # Default for power cables
    
    def _extract_cores(self, text: str) -> str:
        """Extract number of cores."""
        
        core_pattern = r'(\d+)[-\s]?core'
        match = re.search(core_pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}-core"
        return '3-core'  # Default
    
    def _extract_standards(self, text: str) -> List[str]:
        """Extract applicable standards."""
        
        standards = []
        
        # Indian standards
        if re.search(r'is\s*\d+', text, re.IGNORECASE):
            standards.append('IS 7098')
        
        # IEC standards
        if 'iec' in text:
            standards.append('IEC 60502')
        
        # BS standards
        if 'bs' in text:
            standards.append('BS 6622')
        
        return standards if standards else ['IS 7098']

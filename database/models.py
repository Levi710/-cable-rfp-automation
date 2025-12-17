from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from config.database import Base
from datetime import datetime

class DiscoveredTender(Base):
    """Store discovered tenders from web crawlers."""
    __tablename__ = 'discovered_tenders'
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(200), unique=True, index=True)
    source = Column(String(100), index=True)  # GeM, POWERGRID, State SEB, etc.
    title = Column(String(500))
    description = Column(String(3000))
    deadline = Column(DateTime, index=True)
    publication_date = Column(DateTime)
    estimated_value = Column(Float)
    estimated_value_currency = Column(String(10), default='INR')
    organization = Column(String(200))
    location = Column(String(100))
    cable_type = Column(String(100))
    voltage_class = Column(String(50))
    estimated_length_km = Column(Float)
    document_url = Column(String(500))
    raw_data = Column(JSON)
    processed = Column(Boolean, default=False, index=True)
    discovered_at = Column(DateTime, default=datetime.now, index=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CableProduct(Base):
    """Store cable products catalog."""
    __tablename__ = 'cable_products'
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, index=True)
    product_name = Column(String(300))
    conductor_type = Column(String(50))  # Copper, Aluminum
    cross_section_sqmm = Column(Float)
    voltage_rating = Column(String(50), index=True)
    current_capacity_amps = Column(Float)
    insulation_type = Column(String(50))  # PVC, XLPE, FRLS
    armor = Column(Boolean, default=False)
    flexible = Column(Boolean, default=False)
    price_per_meter = Column(Float)
    standards = Column(String(500))  # IS 1554, IEC 60228, etc.
    availability = Column(Boolean, default=True)
    min_order_meters = Column(Integer)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class CableQuote(Base):
    """Store generated quotes."""
    __tablename__ = 'cable_quotes'
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(200), index=True)
    quote_breakdown = Column(JSON)
    material_cost = Column(Float)
    test_costs = Column(Float)
    transportation_cost = Column(Float)
    total_value_inr = Column(Float)
    discount_percent = Column(Float)
    final_quote = Column(Float)
    delivery_weeks = Column(Integer)
    valid_until = Column(DateTime)
    generated_at = Column(DateTime, default=datetime.now)

class RFPAnalysis(Base):
    """Store RFP analysis and recommendations."""
    __tablename__ = 'rfp_analysis'
    
    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(200), index=True)
    sales_score = Column(Float)
    technical_match_percent = Column(Float)
    price_competitiveness = Column(Float)
    win_probability = Column(Float)
    confidence_level = Column(String(50))  # HIGH, MEDIUM, LOW
    recommendation = Column(String(20))  # BID, SKIP
    key_factors = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
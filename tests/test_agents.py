import pytest
from agents.sales_agent import SalesAgent


def test_sales_qualification_simple():
    agent = SalesAgent()
    tender = {"title": "Supply of XLPE cable", "description": "Armored cable"}
    result = agent.qualify_tender(tender)
    assert result["is_qualified"] is True

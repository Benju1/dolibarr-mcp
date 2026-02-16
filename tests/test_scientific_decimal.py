"""Tests for ScientificDecimal type and scientific notation support."""

import pytest
import json
import re
from decimal import Decimal

from dolibarr_mcp.models import (
    ScientificDecimal,
    InvoiceResult,
    InvoiceLine,
    ProposalResult,
    ProposalLine,
    ProductResult,
)


class TestScientificDecimalBasics:
    """Test basic ScientificDecimal functionality."""
    
    def test_parse_scientific_notation(self):
        """Test parsing values in scientific notation."""
        test_cases = [
            ("0E-8", Decimal("0E-8")),
            ("1.5E-10", Decimal("1.5E-10")),
            ("2.3e+5", Decimal("2.3e+5")),
            ("-5.67E+3", Decimal("-5.67E+3")),
        ]
        
        for input_val, expected in test_cases:
            result = ScientificDecimal(input_val)
            assert result == expected, f"Failed for {input_val}"
    
    def test_parse_normal_decimals(self):
        """Test parsing normal decimal values."""
        test_cases = [
            ("123.45", Decimal("123.45")),
            ("-67.89", Decimal("-67.89")),
            ("0.00000001", Decimal("0.00000001")),
            ("1000", Decimal("1000")),
        ]
        
        for input_val, expected in test_cases:
            result = ScientificDecimal(input_val)
            assert result == expected, f"Failed for {input_val}"
    
    def test_arithmetic_operations(self):
        """Test that ScientificDecimal behaves like Decimal."""
        a = ScientificDecimal("100.50")
        b = ScientificDecimal("0E-8")
        
        # Addition
        assert a + b == Decimal("100.50")
        
        # Multiplication
        assert a * Decimal("2") == Decimal("201.00")
        
        # Comparison
        assert b == Decimal("0")
        assert a > b


class TestScientificDecimalJSONSchema:
    """Test JSON Schema generation for ScientificDecimal."""
    
    def test_json_schema_pattern(self):
        """Test that JSON schema includes pattern for scientific notation."""
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            value: ScientificDecimal = Field(...)
        
        schema = TestModel.model_json_schema()
        value_schema = schema['properties']['value']
        
        # Should have anyOf with number and string pattern
        assert 'anyOf' in value_schema
        
        # Extract the pattern
        pattern = None
        for option in value_schema['anyOf']:
            if 'pattern' in option:
                pattern = option['pattern']
                break
        
        assert pattern is not None
        assert '([eE][+-]?\\d+)?' in pattern
    
    def test_regex_pattern_matches_scientific_notation(self):
        """Test that the regex pattern matches scientific notation."""
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            value: ScientificDecimal
        
        schema = TestModel.model_json_schema()
        
        # Extract pattern
        pattern = None
        for option in schema['properties']['value']['anyOf']:
            if 'pattern' in option:
                pattern = option['pattern']
                break
        
        regex = re.compile(pattern)
        
        # Test values that SHOULD match
        valid_values = ['0E-8', '1.5E-10', '123.45', '-5.67E+3', '0.00000001', '1000']
        for val in valid_values:
            assert regex.match(val), f"Pattern should match '{val}'"
        
        # Test values that should NOT match
        invalid_values = ['+.', '+-', '...', 'abc', '']
        for val in invalid_values:
            assert not regex.match(val), f"Pattern should not match '{val}'"


class TestInvoiceWithScientificNotation:
    """Test Invoice models with scientific notation values."""
    
    def test_invoice_result_with_zero_e_notation(self):
        """Test InvoiceResult with 0E-8 values."""
        invoice = InvoiceResult(
            id=140,
            ref="FA1234",
            socid=42,
            date=1640000000,
            total_ht=ScientificDecimal("0E-8"),
            total_tva=ScientificDecimal("0E-8"),
            total_ttc=ScientificDecimal("1200.00"),
            paye=0,
            status=1
        )
        
        assert invoice.total_ht == Decimal("0E-8")
        assert invoice.total_tva == Decimal("0E-8")
        assert invoice.total_ttc == Decimal("1200.00")
    
    def test_invoice_result_serialization(self):
        """Test that InvoiceResult serializes correctly with scientific notation."""
        invoice = InvoiceResult(
            id=140,
            ref="FA1234",
            socid=42,
            date=1640000000,
            total_ht=ScientificDecimal("0E-8"),
            total_tva=ScientificDecimal("0E-8"),
            total_ttc=ScientificDecimal("1200.00"),
            paye=0,
            status=1
        )
        
        json_output = invoice.model_dump_json()
        parsed = json.loads(json_output)
        
        # Should contain the scientific notation
        assert parsed['total_ht'] == '0E-8'
        assert parsed['total_tva'] == '0E-8'
        assert parsed['total_ttc'] == '1200.00'
    
    def test_invoice_line_with_small_quantity(self):
        """Test InvoiceLine with very small quantity."""
        line = InvoiceLine(
            desc="Test product",
            subprice=ScientificDecimal("100.00"),
            qty=ScientificDecimal("1.5E-10"),
            tva_tx=ScientificDecimal("20.0"),
            product_id=42,
            product_type=0
        )
        
        assert line.qty == Decimal("1.5E-10")
        
        json_output = line.model_dump_json()
        parsed = json.loads(json_output)
        assert parsed['qty'] == '1.5E-10'
    
    def test_parse_from_api_response(self):
        """Test parsing invoice from API response with scientific notation."""
        api_response = {
            "id": 140,
            "ref": "FA1234",
            "socid": 42,
            "date": 1640000000,
            "total_ht": "0E-8",  # From Dolibarr API
            "total_tva": "0E-8",
            "total_ttc": "1200.00",
            "paye": 0,
            "status": 1
        }
        
        invoice = InvoiceResult(**api_response)
        
        assert invoice.id == 140
        assert invoice.total_ht == Decimal("0E-8")
        assert invoice.total_tva == Decimal("0E-8")


class TestProposalWithScientificNotation:
    """Test Proposal models with scientific notation values."""
    
    def test_proposal_result_with_scientific_notation(self):
        """Test ProposalResult with scientific notation."""
        proposal = ProposalResult(
            id=100,
            ref="PR2024-001",
            socid=42,
            date=1640000000,
            total_ht=ScientificDecimal("5000.00"),
            total_tva=ScientificDecimal("0E-8"),  # No tax
            total_ttc=ScientificDecimal("5000.00"),
            status=1,
            project_id=10
        )
        
        assert proposal.total_tva == Decimal("0E-8")
        
        json_output = proposal.model_dump_json()
        parsed = json.loads(json_output)
        assert parsed['total_tva'] == '0E-8'
    
    def test_proposal_line_with_scientific_notation(self):
        """Test ProposalLine with scientific notation."""
        line = ProposalLine(
            id=1,
            description="Test service",
            unit_price=ScientificDecimal("100.00"),
            qty=ScientificDecimal("0.5"),
            vat_rate=ScientificDecimal("0E-8"),  # No VAT
            total_ht=ScientificDecimal("50.00"),
            total_ttc=ScientificDecimal("50.00"),
            product_id=None
        )
        
        assert line.vat_rate == Decimal("0E-8")


class TestProductWithScientificNotation:
    """Test Product models with scientific notation values."""
    
    def test_product_with_zero_vat(self):
        """Test ProductResult with zero VAT rate in scientific notation."""
        product = ProductResult(
            id=1,
            ref="PROD001",
            label="Test Product",
            description="Test",
            type=0,
            price=ScientificDecimal("99.99"),
            price_ttc=ScientificDecimal("99.99"),
            tva_tx=ScientificDecimal("0E-8"),  # Tax-free product
            stock_reel=100.0
        )
        
        assert product.tva_tx == Decimal("0E-8")


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_very_large_exponential(self):
        """Test very large numbers in exponential notation."""
        invoice = InvoiceResult(
            id=1,
            ref="TEST",
            socid=1,
            date=1640000000,
            total_ht=ScientificDecimal("1.5E+10"),
            total_tva=ScientificDecimal("3E+9"),
            total_ttc=ScientificDecimal("1.8E+10"),
            paye=0,
            status=1
        )
        
        assert invoice.total_ht == Decimal("1.5E+10")
    
    def test_negative_exponential(self):
        """Test negative numbers in exponential notation."""
        line = InvoiceLine(
            desc="Credit note",
            subprice=ScientificDecimal("-100.00"),
            qty=ScientificDecimal("1"),
            tva_tx=ScientificDecimal("20.0")
        )
        
        assert line.subprice < 0
    
    def test_mixed_formats_in_same_model(self):
        """Test mix of scientific and normal notation in same model."""
        invoice = InvoiceResult(
            id=1,
            ref="TEST",
            socid=1,
            date=1640000000,
            total_ht=ScientificDecimal("1000.00"),  # Normal
            total_tva=ScientificDecimal("0E-8"),    # Scientific
            total_ttc=ScientificDecimal("1.2E+3"),  # Scientific
            paye=0,
            status=1
        )
        
        assert invoice.total_ht == Decimal("1000.00")
        assert invoice.total_tva == Decimal("0")
        assert invoice.total_ttc == Decimal("1200")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

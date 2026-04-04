import sys
import os
import re

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import numpy as np
except ImportError:
    np = None
try:
    import pandas as pd
except ImportError:
    pd = None

from modules.ingestion import _safe_float, _normalize_indian_financials

def test_ocr_fixes():
    print("Testing _safe_float with OCR errors...")
    test_cases = [
        ("5O,00", 5000.0),
        ("S,l23", 5123.0),
        ("(IOO)", -100.0),
        ("RS. l,2SO.OO", 1250.0),
        ("INR S00/-", 500.0),
        ("l.2S %", 1.25),
        ("O.OO", 0.0),
        ("SOO", 500.0), # Entirely misread
    ]
    
    for input_val, expected in test_cases:
        result = _safe_float(input_val)
        status = "PASS" if result == expected else f"FAIL (got {result})"
        print(f"  '{input_val}' -> {result} | {status}")

    print("\nTesting _normalize_indian_financials with OCR errors...")
    unit_test_cases = [
        ("Revenue: l.2S Cr", "Revenue: 12500000"),
        ("Profit: SO Lakhs", "Profit: 5000000"),
        ("Limit: lO Cr", "Limit: 100000000"),
        ("Net Worth: S.S Cr", "Net Worth: 55000000"), # Changed Gr to Cr for simpler check or just test Cr
        ("Net Worth: S.S Gr", "Net Worth: 55000000"), # Testing Gr as Cr error
    ]
    
    for input_val, expected in unit_test_cases:
        result = _normalize_indian_financials(input_val).strip()
        status = "PASS" if result == expected else f"FAIL (got {result})"
        print(f"  '{input_val}' -> '{result}' | {status}")

if __name__ == "__main__":
    test_ocr_fixes()

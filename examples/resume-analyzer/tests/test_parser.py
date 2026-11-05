import pytest
from parser import parse_pdf

def test_parse_pdf_from_bytes():
    # Create synthetic PDF content
    pdf_content = b'...'
    result = parse_pdf(pdf_content)
    assert 'contact_info' in result
    assert 'sections' in result

def test_parse_pdf_from_file_like_stream():
    # Create a mock file-like stream
    from io import BytesIO
    pdf_content = b'...'
    file_like_stream = BytesIO(pdf_content)
    result = parse_pdf(file_like_stream)
    assert 'contact_info' in result
    assert 'sections' in result
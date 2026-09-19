import pytest

from analyst_studio.services.data import read_csv


@pytest.mark.parametrize('encoding', ['utf-8-sig', 'utf-16', 'utf-16-be', 'utf-32', 'cp874'])
def test_import_preserves_thai_text(encoding):
    text = 'ชื่อ;ยอดขาย\nสมชาย;120\n'
    payload = text.encode(encoding)
    if encoding == 'utf-16-be':
        payload = b'\xfe\xff' + payload
    frame = read_csv(payload, 'sales.csv')
    assert list(frame.columns) == ['ชื่อ', 'ยอดขาย']
    assert frame.iloc[0].tolist() == ['สมชาย', 120]


@pytest.mark.parametrize('delimiter', [',', ';', '\t', '|'])
def test_detect_separator_with_quoted_multiline_values(delimiter):
    text = f'name{delimiter}amount\n"a,b; c|d\nsecond line"{delimiter}12\n'
    frame = read_csv(text.encode(), 'sales.csv')
    assert frame.shape == (1, 2)
    assert frame.iloc[0].tolist() == ['a,b; c|d\nsecond line', 12]


def test_excel_separator_directive():
    frame = read_csv(b'sep=;\r\nname;amount\r\nAda;12\r\n', 'excel.csv')
    assert frame.iloc[0].tolist() == ['Ada', 12]


@pytest.mark.parametrize('text,line', [
    ('name;amount\nAda;12\nBob;13;extra\n', 3),
    ('name;amount\nAda;12\nBob\n', 3),
    ('sep=;\nname;amount\nBob;13;extra\n', 3),
])
def test_bad_width_reports_physical_line_and_expected_count(text, line):
    with pytest.raises(ValueError) as error:
        read_csv(text.encode(), 'bad.csv')
    assert f'บรรทัด {line}' in str(error.value)
    assert '2' in str(error.value)


def test_unclosed_quote_reports_start_line():
    with pytest.raises(ValueError) as error:
        read_csv(b'name,amount\nAda,12\n"Bob\nstill open,13\n', 'bad.csv')
    assert 'บรรทัด 3' in str(error.value)
    assert 'เครื่องหมายคำพูด' in str(error.value)


def test_explicit_encoding_for_ambiguous_western_text():
    frame = read_csv('name;amount\ncafé;12\n'.encode('cp1252'), 'sales.csv', encoding='Windows-1252', delimiter='Semicolon (;)')
    assert frame.iloc[0].tolist() == ['café', 12]


def test_explicit_wrong_encoding_is_not_silently_replaced():
    with pytest.raises(ValueError, match='encoding'):
        read_csv('ชื่อ,ยอด\nสมชาย,12'.encode('cp874'), 'sales.csv', encoding='UTF-8')


def test_single_column_and_escaped_quotes():
    frame = read_csv(b'name\n"Ada ""A"""\nBob\n', 'names.csv')
    assert frame.name.tolist() == ['Ada "A"', 'Bob']


def test_large_quoted_cell_is_valid_within_upload_limit():
    value = 'a' * 140_000
    frame = read_csv(f'name,amount\n"{value}",12\n'.encode(), 'large-cell.csv')
    assert frame.name.iloc[0] == value


def test_quoted_blank_and_blank_lines_are_not_confused():
    frame = read_csv(b'name\n\n" "\nBob\n', 'names.csv')
    assert frame.name.tolist() == [' ', 'Bob']

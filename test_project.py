# test_main.py
from project import generate_random_identifier, format_message, display_subject, parse_date
import uuid, datetime

def test_generate_random_identifier():
    identifier = generate_random_identifier()
    try:
        uuid_obj = uuid.UUID(identifier, version=4)
    except ValueError:
        assert False, "generate_random_identifier does not return valid UUID4"
    assert str(uuid_obj) == identifier, "UUID generated is not in string representation"

def test_format_message():
    input_text = "Hello\nWorld"
    expected_output = "Hello<br>World"
    assert format_message(input_text) == expected_output 
    assert format_message("**Hello** world") == "**Hello** world"
    assert format_message("") == ""     

def test_display_subject():
    # Test cases for display_subject function
    assert display_subject("**Hello** world") == "**Hello**"
    assert display_subject("This is **Bing**") == "**Bing**"
    assert display_subject("No asterisks here") == "**No asterisks here**"
    assert display_subject("**Multiple** asterisks **here**") == "**Multiple**"
    assert display_subject("") == "****"

def test_parse_date():
    # Test cases for parse_date function
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    last_week = today - datetime.timedelta(days=5)
    last_month = today - datetime.timedelta(days=20)
    older = today - datetime.timedelta(days=40)

    assert parse_date(today.isoformat()) == "Today"
    assert parse_date(yesterday.isoformat()) == "Yesterday"
    assert parse_date(last_week.isoformat()) == "Last week"
    assert parse_date(last_month.isoformat()) == "Last month"
    assert parse_date(older.isoformat()) == "Older"    
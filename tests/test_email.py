from mcp_outlook.email import (
    EmailBodyType,
    SendMailRequest,
    parse_send_mail_request,
)


def test_send_mail_request_deduplicates_recipients():
    request = SendMailRequest.model_validate(
        {
            "subject": "Subject",
            "body": {"content": "Hello", "content_type": EmailBodyType.TEXT},
            "to": ["user@example.com", "USER@example.com"],
            "cc": ["cc@example.com", "cc@example.com"],
            "bcc": [],
        }
    )

    assert len(request.to) == 1
    assert request.to[0].address == "user@example.com"
    assert len(request.cc) == 1


def test_to_graph_payload_includes_default_sender():
    request = parse_send_mail_request(
        {
            "subject": "Subject",
            "body": {"content": "Hi", "content_type": "Text"},
            "to": ["user@example.com"],
        }
    )

    payload = request.to_graph_payload("sender@example.com")
    assert payload["message"]["from"]["emailAddress"]["address"] == "sender@example.com"
    assert payload["message"]["toRecipients"][0]["emailAddress"]["address"] == "user@example.com"


def test_parse_send_mail_request_validates_email_addresses():
    try:
        parse_send_mail_request(
            {
                "subject": "Subject",
                "body": {"content": "Hi", "content_type": "Text"},
                "to": ["not-an-email"],
            }
        )
    except ValueError as exc:
        assert "value is not a valid email address" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid email address")

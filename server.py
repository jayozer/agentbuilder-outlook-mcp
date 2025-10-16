from __future__ import annotations

import json
import logging
from typing import Optional, Sequence, Union

import httpx
from fastmcp import FastMCP

from mcp_outlook.auth import GraphAuthError, GraphTokenManager
from mcp_outlook.config import ConfigurationError, get_graph_settings
from mcp_outlook.email import (
    EmailBodyType,
    FileAttachment,
    MessageBody,
    SendMailRequest,
)


mcp = FastMCP("Outlook Mailer")

_logger = logging.getLogger("mcp_outlook.server")


def _build_sendmail_url(sender: Optional[str]) -> str:
    from urllib.parse import quote

    if sender:
        encoded = quote(sender)
        return f"https://graph.microsoft.com/v1.0/users/{encoded}/sendMail"
    return "https://graph.microsoft.com/v1.0/me/sendMail"


def _make_mail_request(
    subject: str,
    body: str,
    to: Sequence[str],
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    *,
    body_type: Union[EmailBodyType, str] = EmailBodyType.TEXT,
    attachments: Optional[Sequence[Union[FileAttachment, dict]]] = None,
    save_to_sent_items: bool = True,
    sender: Optional[str] = None,
    dry_run: bool = False,
) -> SendMailRequest:
    payload = {
        "subject": subject,
        "body": {"content": body, "content_type": body_type},
        "to": list(to),
        "cc": list(cc) if cc else [],
        "bcc": list(bcc) if bcc else [],
        "attachments": attachments or [],
        "save_to_sent_items": save_to_sent_items,
        "sender_override": sender,
        "dry_run": dry_run,
    }
    return SendMailRequest.model_validate(payload)


def send_outlook_mail_impl(
    subject: str,
    body: str,
    to: Sequence[str],
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    body_type: Union[EmailBodyType, str] = EmailBodyType.TEXT,
    attachments: Optional[Sequence[Union[FileAttachment, dict]]] = None,
    save_to_sent_items: bool = True,
    sender: Optional[str] = None,
    dry_run: bool = False,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    access_token: Optional[str] = None,
) -> str:
    _logger.info(
        "Preparing sendMail request: subject=%s, to_count=%d, dry_run=%s",
        subject,
        len(to),
        dry_run,
    )
    try:
        mail_request = _make_mail_request(
            subject=subject,
            body=body,
            to=to,
            cc=cc,
            bcc=bcc,
            body_type=body_type,
            attachments=attachments,
            save_to_sent_items=save_to_sent_items,
            sender=sender,
            dry_run=dry_run,
        )
    except ValueError as exc:
        _logger.error("Invalid email payload: %s", exc)
        raise ValueError(f"Invalid email payload: {exc}") from exc

    try:
        settings = get_graph_settings()
    except ConfigurationError as exc:
        _logger.error("Configuration error: %s", exc)
        raise RuntimeError(f"Configuration error: {exc}") from exc

    graph_payload = mail_request.to_graph_payload(settings.default_sender)
    resolved_sender = mail_request.resolve_sender(settings.default_sender)

    if mail_request.dry_run:
        preview = json.dumps(graph_payload, indent=2, sort_keys=True)
        _logger.info(
            "Dry run prepared for subject=%s, to_count=%d",
            mail_request.subject,
            len(mail_request.to),
        )
        return f"[DRY RUN] Payload ready for {resolved_sender or 'me'}:\n{preview}"

    # Create per-request token manager with user-provided credentials
    # Priority: parameters > environment variables
    token_manager = GraphTokenManager(
        settings=settings,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
    )
    try:
        token = token_manager.get_token()
    except GraphAuthError as exc:
        _logger.error("Failed to acquire access token: %s", exc)
        raise RuntimeError(f"Failed to acquire Graph access token: {exc}") from exc

    url = _build_sendmail_url(resolved_sender)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, headers=headers, json=graph_payload, timeout=20.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        friendly = detail
        try:
            error_json = exc.response.json()
            friendly = (
                error_json.get("error", {}).get("message")
                or error_json.get("message")
                or detail
            )
        except ValueError:
            friendly = detail
        _logger.warning(
            "Graph sendMail HTTP error: status=%s detail=%s",
            exc.response.status_code,
            detail,
        )
        raise RuntimeError(
            f"Microsoft Graph sendMail failed ({exc.response.status_code}): {friendly}"
        ) from exc
    except httpx.HTTPError as exc:
        _logger.error("Network error calling Microsoft Graph: %s", exc)
        raise RuntimeError(f"Network error calling Microsoft Graph: {exc}") from exc

    _logger.info(
        "Microsoft Graph accepted message: subject=%s, to_count=%d",
        mail_request.subject,
        len(mail_request.to),
    )
    return (
        "Microsoft Graph accepted the message "
        f"for {len(mail_request.to)} recipient(s)."
    )


@mcp.tool
def send_outlook_mail(
    subject: str,
    body: str,
    to: Sequence[str],
    cc: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    body_type: Union[EmailBodyType, str] = EmailBodyType.TEXT,
    attachments: Optional[Sequence[Union[FileAttachment, dict]]] = None,
    save_to_sent_items: bool = True,
    sender: Optional[str] = None,
    dry_run: bool = False,
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    access_token: Optional[str] = None,
) -> str:
    """
    Send email via Microsoft Graph API.

    Multi-tenant support: Users can provide credentials in two ways:
    1. Delegated token: Pass access_token (from Graph Explorer or OAuth flow)
    2. Client credentials: Pass tenant_id, client_id, client_secret

    Server-side environment variables are used as fallback if parameters not provided.

    Args:
        subject: Email subject line
        body: Email body content
        to: List of recipient email addresses
        cc: Optional list of CC recipients
        bcc: Optional list of BCC recipients
        body_type: Email body format (TEXT or HTML)
        attachments: Optional list of file attachments
        save_to_sent_items: Save to sent items folder (default: True)
        sender: Optional sender email override
        dry_run: Preview payload without sending (default: False)
        tenant_id: Microsoft Entra tenant ID (for client credentials flow)
        client_id: App registration client ID (for client credentials flow)
        client_secret: Client secret (for client credentials flow)
        access_token: Delegated access token (alternative to client credentials)

    Returns:
        Success message or dry-run preview

    Raises:
        ValueError: Invalid email payload
        RuntimeError: Configuration, authentication, or API errors
    """
    return send_outlook_mail_impl(
        subject=subject,
        body=body,
        to=to,
        cc=cc,
        bcc=bcc,
        body_type=body_type,
        attachments=attachments,
        save_to_sent_items=save_to_sent_items,
        sender=sender,
        dry_run=dry_run,
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
        access_token=access_token,
    )


if __name__ == "__main__":
    mcp.run()

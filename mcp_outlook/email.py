from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator


class EmailBodyType(str, Enum):
    TEXT = "Text"
    HTML = "HTML"


class Recipient(BaseModel):
    address: EmailStr

    @model_validator(mode="before")
    def _coerce_from_str(cls, value):
        if isinstance(value, str):
            return {"address": value}
        return value

    def to_graph(self) -> dict:
        return {"emailAddress": {"address": self.address}}


class MessageBody(BaseModel):
    content: str
    content_type: EmailBodyType = EmailBodyType.TEXT

    def to_graph(self) -> dict:
        return {"contentType": self.content_type.value, "content": self.content}


class FileAttachment(BaseModel):
    name: str
    content_bytes: str
    content_type: str = "application/octet-stream"

    def to_graph(self) -> dict:
        return {
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": self.name,
            "contentType": self.content_type,
            "contentBytes": self.content_bytes,
        }


class SendMailRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    body: MessageBody
    to: List[Recipient] = Field(..., min_length=1)
    cc: List[Recipient] = Field(default_factory=list)
    bcc: List[Recipient] = Field(default_factory=list)
    attachments: List[FileAttachment] = Field(default_factory=list)
    save_to_sent_items: bool = True
    sender_override: Optional[EmailStr] = None
    dry_run: bool = False

    @field_validator("cc", "bcc", mode="before")
    @classmethod
    def _coerce_recipient_iterables(cls, value):
        if value is None:
            return []
        if isinstance(value, (str, EmailStr)):
            return [value]
        return list(value)

    @model_validator(mode="after")
    def _ensure_unique_recipients(self):
        def dedupe(items: List[Recipient]) -> List[Recipient]:
            seen = set()
            unique: List[Recipient] = []
            for item in items:
                addr = item.address.casefold()
                if addr not in seen:
                    seen.add(addr)
                    unique.append(item)
            return unique

        self.to = dedupe(self.to)
        self.cc = dedupe(self.cc)
        self.bcc = dedupe(self.bcc)
        return self

    def resolve_sender(self, default_sender: Optional[str]) -> Optional[str]:
        sender = self.sender_override or default_sender
        return sender

    def to_graph_payload(self, default_sender: Optional[str]) -> dict:
        message = {
            "subject": self.subject,
            "body": self.body.to_graph(),
            "toRecipients": [recipient.to_graph() for recipient in self.to],
        }
        if self.cc:
            message["ccRecipients"] = [recipient.to_graph() for recipient in self.cc]
        if self.bcc:
            message["bccRecipients"] = [recipient.to_graph() for recipient in self.bcc]
        if self.attachments:
            message["attachments"] = [attachment.to_graph() for attachment in self.attachments]

        sender = self.resolve_sender(default_sender)
        if sender:
            message["from"] = {"emailAddress": {"address": sender}}

        return {
            "message": message,
            "saveToSentItems": self.save_to_sent_items,
        }


def parse_send_mail_request(data: dict) -> SendMailRequest:
    try:
        return SendMailRequest.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

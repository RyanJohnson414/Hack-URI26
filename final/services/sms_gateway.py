from typing import Optional

try:
    from twilio.rest import Client
except Exception:
    Client = None

from config import config


class SMSGateway:
    def __init__(self) -> None:
        self.enabled = bool(config.twilio_account_sid and config.twilio_auth_token and config.twilio_from_number and Client)
        self.client = None
        if self.enabled:
            self.client = Client(config.twilio_account_sid, config.twilio_auth_token)

    def send(self, to_number: str, body: str) -> Optional[str]:
        if not self.enabled or not self.client:
            return None
        message = self.client.messages.create(
            body=body,
            from_=config.twilio_from_number,
            to=to_number,
        )
        return message.sid

from typing import List, Dict
import imaplib
import email
import logging
import os

logger = logging.getLogger(__name__)

class EmailMonitor:
    """Monitor an IMAP inbox for RFP emails and extract tenders."""

    def __init__(self,
                 server: str = None,
                 address: str = None,
                 password: str = None):
        self.server = server or os.getenv('EMAIL_IMAP_SERVER', 'imap.gmail.com')
        self.address = address or os.getenv('EMAIL_ADDRESS')
        self.password = password or os.getenv('EMAIL_PASSWORD')

    def fetch_new_tenders(self) -> List[Dict]:
        tenders: List[Dict] = []
        if not (self.address and self.password):
            logger.info("Email credentials not configured; skipping email monitor")
            return tenders
        try:
            mail = imaplib.IMAP4_SSL(self.server)
            mail.login(self.address, self.password)
            mail.select('inbox')
            status, data = mail.search(None, '(UNSEEN)')
            ids = data[0].split()
            for num in ids[:50]:  # limit
                status, msg_data = mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get('Subject', '')
                if any(k in subject.lower() for k in ['tender', 'rfp', 'bid']):
                    tenders.append({
                        'source': 'Email',
                        'tender_id': f"EMAIL-{num.decode()}",
                        'title': subject,
                        'description': subject
                    })
            mail.logout()
        except Exception as e:
            logger.error(f"Email monitor error: {e}")
        return tenders

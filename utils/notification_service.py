
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Third-party imports (to be installed if needed, but we'll use requests/built-ins where possible or just standard libs)
# For production, we'd use 'twilio' and 'python-telegram-bot' or raw requests.
# We'll use raw requests/aiohttp to keep dependencies minimal if possible, or assume simple REST calls.
import requests

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service to send multi-channel notifications (WhatsApp, Telegram) 
    with pipeline execution results.
    """
    
    def __init__(self, settings: Any):
        self.settings = settings
        self.enabled = True
        
        # Load config
        self.twilio_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
        self.twilio_from = getattr(settings, 'TWILIO_FROM_NUMBER', '')
        self.twilio_to = getattr(settings, 'TWILIO_TO_NUMBER', '')
        
        self.telegram_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.telegram_chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', '')
        
        # Check if fully configured
        self.whatsapp_enabled = all([self.twilio_account_sid, self.twilio_auth_token, self.twilio_from, self.twilio_to])
        self.telegram_enabled = all([self.telegram_token, self.telegram_chat_id])
        
        if not (self.whatsapp_enabled or self.telegram_enabled):
            logger.warning("NotificationService initialized but no credentials found. Notifications disabled.")
            self.enabled = False

    def format_report(self, results: Dict[str, Any]) -> str:
        """
        Format the pipeline results into a report string matching the user's preferred layout.
        
        Format:
        *CABLE RFP AUTOMATION REPORT*
        ----------------------------------
        Date: DD MMM YYYY, HH:MM
        
        Execution Time: XX.XXs
        Status: COMPLETE
        
        *DISCOVERY SUMMARY*
        Total Tenders: X
        - [Source]: X
        
        *SELECTED TENDER*
        ID: [ID]
        Title: [Title truncated]
        Org: [Org]
        Value: Rs [Value]
        
        *DECISION*
        Recommendation: BID/NO-BID
        Win Probability: XX.X%
        Quoted Value: Rs X,XXX,XXX
        
        *PRICING SUMMARY*
        Material Cost: Rs X,XXX,XXX
        Services Cost: Rs XX,XXX
        Grand Total: Rs X,XXX,XXX
        
        *PRODUCTS SELECTED*
        - [SKU]
        
        ----------------------------------
        Cable RFP Automation v2.0
        """
        
        pipeline_info = results.get("pipeline_info", {})
        discovery = results.get("discovery", {})
        processing = results.get("processing", {}) or {}
        
        # Basic Info
        timestamp_str = pipeline_info.get("timestamp", datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp_str)
            date_str = dt.strftime("%d %b %Y, %H:%M")
        except:
            date_str = timestamp_str
            
        exec_time = pipeline_info.get("execution_time", 0)
        status = pipeline_info.get("status", "UNKNOWN").upper()
        
        # Header
        lines = [
            "*CABLE RFP AUTOMATION REPORT*",
            "----------------------------------",
            f"Date: {date_str}",
            "",
            f"Execution Time: {exec_time}s",
            f"Status: {status}",
            ""
        ]
        
        # Discovery
        lines.append("*DISCOVERY SUMMARY*")
        lines.append(f"Total Tenders: {discovery.get('total_discovered', 0)}")
        sources = discovery.get("sources", {})
        for src, count in sources.items():
            lines.append(f"- {src}: {count}")
        lines.append("")
        
        # Selected Tender
        selected = processing.get("selected_rfp", {})
        if selected:
            lines.append("*SELECTED TENDER*")
            lines.append(f"ID: {selected.get('tender_id', 'N/A')}")
            title = selected.get('title', 'N/A')
            if len(title) > 50:
                title = title[:47] + "..."
            lines.append(f"Title: {title}")
            lines.append(f"Org: {selected.get('organization', 'N/A')}")
            est_val = selected.get('estimated_value', 0)
            lines.append(f"Value: Rs {est_val:,.0f}" if est_val else "Value: Rs 0")
            lines.append("")
            
            # Decision
            decision = processing.get("decision", {})
            lines.append("*DECISION*")
            lines.append(f"Recommendation: {decision.get('recommendation', 'N/A')}")
            win_prob = decision.get("win_probability", 0)
            lines.append(f"Win Probability: {win_prob:.1f}%")
            quoted = decision.get("quoted_value", 0)
            lines.append(f"Quoted Value: Rs {quoted:,.0f}")
            lines.append("")
            
            # Pricing Summary
            pricing_out = processing.get("pricing_agent_output", {})
            pricing_details = pricing_out.get("pricing_details", {})
            if pricing_details:
                lines.append("*PRICING SUMMARY*")
                mat_cost = pricing_details.get("total_material_cost", 0)
                svc_cost = pricing_details.get("total_services_cost", 0)
                g_total = pricing_details.get("grand_total", 0)
                lines.append(f"Material Cost: Rs {mat_cost:,.0f}")
                lines.append(f"Services Cost: Rs {svc_cost:,.0f}")
                lines.append(f"Grand Total: Rs {g_total:,.0f}")
                lines.append("")
            
            # Products Selected (from Tech output)
            tech_out = processing.get("technical_agent_output", {})
            final_sel = tech_out.get("final_selection", [])
            if final_sel:
                lines.append("*PRODUCTS SELECTED*")
                for p in final_sel:
                    # Using 'selected_sku' or 'sku'
                    sku = p.get('selected_sku') or p.get('sku', 'N/A')
                    lines.append(f"- {sku}")
                lines.append("")
        
        else:
            lines.append("*NO TENDER SELECTED*")
            lines.append(processing.get("message", ""))
            lines.append("")

        # Footer
        lines.append("----------------------------------")
        lines.append("Cable RFP Automation v2.0")
        
        return "\n".join(lines)

    def send_notifications(self, results: Dict[str, Any]):
        """Send formatted report to all enabled channels."""
        if not self.enabled:
            logger.info("Notifications disabled (missing credentials).")
            return
            
        report = self.format_report(results)
        
        if self.whatsapp_enabled:
            self._send_whatsapp(report)
            
        if self.telegram_enabled:
            self._send_telegram(report)

    def _send_whatsapp(self, message: str):
        """Send via Twilio WhatsApp API."""
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
            data = {
                "From": f"whatsapp:{self.twilio_from}",
                "To": f"whatsapp:{self.twilio_to}",
                "Body": message
            }
            auth = (self.twilio_account_sid, self.twilio_auth_token)
            
            logger.info("Sending WhatsApp notification...")
            response = requests.post(url, data=data, auth=auth, timeout=10)
            
            if response.status_code in (200, 201):
                logger.info("WhatsApp notification sent successfully.")
            else:
                logger.error(f"Failed to send WhatsApp: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {str(e)}")

    def _send_telegram(self, message: str):
        """Send via Telegram Bot API."""
        try:
            # Telegram uses markdown or HTML. We'll strip basic markdown or use it.
            # The report uses *bold*, which works in Telegram Markdown.
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown" 
            }
            
            logger.info("Sending Telegram notification...")
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully.")
            else:
                logger.error(f"Failed to send Telegram: {response.text}")
                
        except Exception as e:
            logger.error(f"Error sending Telegram: {str(e)}")

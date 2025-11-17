"""
Price Alert and Monitoring System
Tracks product prices and sends alerts when targets are met
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


@dataclass
class PriceAlert:
    """Price alert data model"""
    id: str
    user_email: str
    product_name: str
    product_url: str
    marketplace: str
    target_price: float
    current_price: float
    created_at: str
    is_active: bool = True
    last_checked: Optional[str] = None
    alert_sent: bool = False


class PriceAlertManager:
    """
    Manages price alerts and monitoring.
    Stores alerts and checks prices periodically.
    """
    
    def __init__(self, storage_path: str = './data/price_alerts.json'):
        """
        Initialize price alert manager.
        
        Args:
            storage_path: Path to store alerts
        """
        self.storage_path = storage_path
        self.alerts: Dict[str, PriceAlert] = {}
        self.price_history: Dict[str, List[Dict]] = {}
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        self._load_alerts()
        logger.info(f"Price Alert Manager initialized with {len(self.alerts)} alerts")
    
    def create_alert(
        self,
        user_email: str,
        product_name: str,
        product_url: str,
        marketplace: str,
        target_price: float,
        current_price: float
    ) -> str:
        """
        Create a new price alert.
        
        Args:
            user_email: User's email for notifications
            product_name: Product name
            product_url: Product URL
            marketplace: Marketplace name
            target_price: Target price to alert at
            current_price: Current product price
            
        Returns:
            Alert ID
        """
        import uuid
        alert_id = str(uuid.uuid4())
        
        alert = PriceAlert(
            id=alert_id,
            user_email=user_email,
            product_name=product_name,
            product_url=product_url,
            marketplace=marketplace,
            target_price=target_price,
            current_price=current_price,
            created_at=datetime.now().isoformat(),
            is_active=True
        )
        
        self.alerts[alert_id] = alert
        self._save_alerts()
        
        # Initialize price history
        self._add_price_history(alert_id, current_price)
        
        logger.info(f"Created price alert: {alert_id} for {product_name}")
        return alert_id
    
    def get_alert(self, alert_id: str) -> Optional[PriceAlert]:
        """Get alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_user_alerts(self, user_email: str, active_only: bool = True) -> List[PriceAlert]:
        """
        Get all alerts for a user.
        
        Args:
            user_email: User's email
            active_only: Return only active alerts
            
        Returns:
            List of alerts
        """
        alerts = []
        for alert in self.alerts.values():
            if alert.user_email == user_email:
                if not active_only or alert.is_active:
                    alerts.append(alert)
        return alerts
    
    def update_alert(self, alert_id: str, target_price: float) -> bool:
        """
        Update alert target price.
        
        Args:
            alert_id: Alert ID
            target_price: New target price
            
        Returns:
            Success status
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        
        alert.target_price = target_price
        alert.alert_sent = False  # Reset alert sent flag
        self._save_alerts()
        
        logger.info(f"Updated alert {alert_id} target price to {target_price}")
        return True
    
    def delete_alert(self, alert_id: str) -> bool:
        """
        Delete an alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Success status
        """
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self._save_alerts()
            logger.info(f"Deleted alert: {alert_id}")
            return True
        return False
    
    def deactivate_alert(self, alert_id: str) -> bool:
        """
        Deactivate an alert without deleting it.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Success status
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
        
        alert.is_active = False
        self._save_alerts()
        logger.info(f"Deactivated alert: {alert_id}")
        return True
    
    def check_alert(self, alert_id: str, current_price: float) -> bool:
        """
        Check if alert should be triggered.
        
        Args:
            alert_id: Alert ID
            current_price: Current product price
            
        Returns:
            True if alert triggered
        """
        alert = self.alerts.get(alert_id)
        if not alert or not alert.is_active:
            return False
        
        # Update current price
        alert.current_price = current_price
        alert.last_checked = datetime.now().isoformat()
        
        # Add to price history
        self._add_price_history(alert_id, current_price)
        
        # Check if target met
        if current_price <= alert.target_price and not alert.alert_sent:
            # Send alert
            self._send_alert_email(alert, current_price)
            alert.alert_sent = True
            self._save_alerts()
            logger.info(f"Alert triggered: {alert_id} at price {current_price}")
            return True
        
        self._save_alerts()
        return False
    
    def check_all_alerts(self, price_fetcher_func) -> Dict[str, Any]:
        """
        Check all active alerts.
        
        Args:
            price_fetcher_func: Function to fetch current prices
            
        Returns:
            Check results
        """
        results = {
            'total_checked': 0,
            'alerts_triggered': 0,
            'errors': 0,
            'triggered_alerts': []
        }
        
        for alert_id, alert in self.alerts.items():
            if not alert.is_active:
                continue
            
            results['total_checked'] += 1
            
            try:
                # Fetch current price
                current_price = price_fetcher_func(alert.product_url, alert.marketplace)
                
                if current_price and self.check_alert(alert_id, current_price):
                    results['alerts_triggered'] += 1
                    results['triggered_alerts'].append(alert_id)
            
            except Exception as e:
                logger.error(f"Error checking alert {alert_id}: {str(e)}")
                results['errors'] += 1
        
        return results
    
    def get_price_history(
        self,
        alert_id: str,
        days: int = 30
    ) -> List[Dict]:
        """
        Get price history for an alert.
        
        Args:
            alert_id: Alert ID
            days: Number of days of history
            
        Returns:
            Price history
        """
        history = self.price_history.get(alert_id, [])
        
        # Filter by date range
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) >= cutoff
        ]
        
        return filtered
    
    def get_price_trend(self, alert_id: str) -> Dict[str, Any]:
        """
        Analyze price trend for an alert.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Trend analysis
        """
        history = self.get_price_history(alert_id)
        
        if len(history) < 2:
            return {'trend': 'insufficient_data'}
        
        prices = [h['price'] for h in history]
        first_price = prices[0]
        last_price = prices[-1]
        
        change = last_price - first_price
        change_percent = (change / first_price) * 100 if first_price > 0 else 0
        
        trend = 'stable'
        if change_percent > 5:
            trend = 'rising'
        elif change_percent < -5:
            trend = 'falling'
        
        return {
            'trend': trend,
            'change': change,
            'change_percent': change_percent,
            'min_price': min(prices),
            'max_price': max(prices),
            'avg_price': sum(prices) / len(prices),
            'current_price': last_price
        }
    
    def _send_alert_email(self, alert: PriceAlert, current_price: float):
        """
        Send alert email to user.
        
        Args:
            alert: Alert object
            current_price: Current price that triggered alert
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP not configured, skipping email")
            return
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🎉 Price Alert: {alert.product_name}"
            msg['From'] = self.smtp_user
            msg['To'] = alert.user_email
            
            # Email body
            html = f"""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2>🎉 Price Drop Alert!</h2>
                <p>Good news! The price for <strong>{alert.product_name}</strong> has dropped!</p>
                
                <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                  <p style="margin: 5px 0;"><strong>Current Price:</strong> ${current_price:.2f}</p>
                  <p style="margin: 5px 0;"><strong>Your Target:</strong> ${alert.target_price:.2f}</p>
                  <p style="margin: 5px 0;"><strong>Marketplace:</strong> {alert.marketplace.title()}</p>
                </div>
                
                <a href="{alert.product_url}" 
                   style="display: inline-block; background: #4285f4; color: white; 
                          padding: 12px 24px; text-decoration: none; border-radius: 5px; margin-top: 10px;">
                  View Product
                </a>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                  This alert was created on {datetime.fromisoformat(alert.created_at).strftime('%B %d, %Y')}
                </p>
              </body>
            </html>
            """
            
            part = MIMEText(html, 'html')
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Alert email sent to {alert.user_email}")
        
        except Exception as e:
            logger.error(f"Failed to send alert email: {str(e)}")
    
    def _add_price_history(self, alert_id: str, price: float):
        """Add price point to history"""
        if alert_id not in self.price_history:
            self.price_history[alert_id] = []
        
        self.price_history[alert_id].append({
            'price': price,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 90 days
        cutoff = datetime.now() - timedelta(days=90)
        self.price_history[alert_id] = [
            h for h in self.price_history[alert_id]
            if datetime.fromisoformat(h['timestamp']) >= cutoff
        ]
    
    def _load_alerts(self):
        """Load alerts from storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.alerts = {
                        k: PriceAlert(**v) for k, v in data.get('alerts', {}).items()
                    }
                    self.price_history = data.get('price_history', {})
        except Exception as e:
            logger.error(f"Failed to load alerts: {str(e)}")
    
    def _save_alerts(self):
        """Save alerts to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                data = {
                    'alerts': {k: asdict(v) for k, v in self.alerts.items()},
                    'price_history': self.price_history
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save alerts: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        total_alerts = len(self.alerts)
        active_alerts = sum(1 for a in self.alerts.values() if a.is_active)
        triggered_alerts = sum(1 for a in self.alerts.values() if a.alert_sent)
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'triggered_alerts': triggered_alerts,
            'inactive_alerts': total_alerts - active_alerts
        }
import pandas as pd
from pathlib import Path
from datetime import datetime
import random
import uuid
import logging
from typing import Optional, Dict, List, Any, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataService:
    def __init__(self):
        """Load all CSVs into memory on initialization"""
        self.data_dir = Path(__file__).parent.parent / "data"
        self._load_data()

    def _load_data(self):
        """Helper to load all CSVs with error handling"""
        csv_files = {
            "customers": "customers.csv",
            "sites": "sites.csv",
            "site_issues": "site_issues.csv",
            "weekly_metrics": "weekly_metrics.csv",
            "proposals": "proposals.csv",
            "proposal_template": "proposal_template.csv",
            "service_tickets": "service_tickets.csv",
            "agent_availability": "agent_availability.csv",
            "crm_opportunities": "crm_opportunities.csv",
            "prospects": "prospects.csv",
            "email_otp": "email_otp.csv",
            "sms_otp": "sms_otp.csv",
            "component_info": "component_info.csv"
        }

        for attr, filename in csv_files.items():
            file_path = self.data_dir / filename
            try:
                if file_path.exists():
                    setattr(self, f"df_{attr}", pd.read_csv(file_path))
                else:
                    logger.warning(f"File not found: {filename}. Initializing empty DataFrame.")
                    setattr(self, f"df_{attr}", pd.DataFrame())
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
                setattr(self, f"df_{attr}", pd.DataFrame())

    def lookup_customer(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Search by email OR phone in customers.csv"""
        try:
            if self.df_customers.empty:
                return None
                
            # Try email match
            match = self.df_customers[self.df_customers['email'] == identifier]
            if match.empty:
                # Try phone match
                match = self.df_customers[self.df_customers['phone'] == identifier]
            
            if not match.empty:
                return match.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Error looking up customer {identifier}: {e}")
            return None
    
    def get_site_status(self, site_id: int) -> Dict[str, Any]:
        """Get site info, using site_issues.csv as authoritative source for issue_flag"""
        try:
            if self.df_sites.empty:
                 return {"error": "Site database empty"}

            # Get base site info
            site = self.df_sites[self.df_sites['site_id'] == site_id]
            if site.empty:
                return {"error": "Site not found"}
            
            site_dict = site.iloc[0].to_dict()
            
            # Override with site_issues.csv (authoritative)
            if not self.df_site_issues.empty:
                issue = self.df_site_issues[self.df_site_issues['site_id'] == site_id]
                if not issue.empty:
                    issue_dict = issue.iloc[0].to_dict()
                    site_dict['issue_flag'] = issue_dict['issue_flag']
                    site_dict['issue_text'] = issue_dict.get('issue_text', '')
                    site_dict['recommended_action_text'] = issue_dict.get('recommended_action_text', '')
            
            return site_dict
        except Exception as e:
            logger.error(f"Error getting site status for {site_id}: {e}")
            return {"error": f"Internal error: {str(e)}"}
    
    def get_site_issues(self, site_id: int) -> List[Dict[str, Any]]:
        """Get all active issues for a site from site_issues.csv"""
        try:
            if self.df_site_issues.empty:
                return []
            issues = self.df_site_issues[
                (self.df_site_issues['site_id'] == site_id) & 
                (self.df_site_issues['issue_flag'] == True)
            ]
            return issues.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting issues for site {site_id}: {e}")
            return []

    def get_weekly_metrics(self, site_id: int, days: int = 7) -> Dict[str, Any]:
        """Get last N days of metrics and compute aggregates"""
        try:
            if self.df_weekly_metrics.empty:
                return self._empty_metrics()

            metrics = self.df_weekly_metrics[self.df_weekly_metrics['site_id'] == site_id]
            
            if metrics.empty:
                return self._empty_metrics()
            
            # Sort by date descending and take last N days
            metrics = metrics.sort_values('date', ascending=False).head(days)
            
            avg_cloudiness = metrics['cloudiness_percentage'].mean()
            total_production = metrics['production_kwh'].sum()
            avg_performance = metrics['performance_score'].mean()
            
            return {
                "rows": metrics.to_dict('records'),
                "avg_cloudiness": round(avg_cloudiness, 1),
                "total_production": round(total_production, 1),
                "avg_performance": round(avg_performance, 1),
                "is_cloudy": avg_cloudiness > 60,
                "is_underperforming": avg_performance < 75
            }
        except Exception as e:
            logger.error(f"Error getting metrics for {site_id}: {e}")
            return self._empty_metrics()

    def _empty_metrics(self):
        return {
            "rows": [],
            "avg_cloudiness": 0,
            "total_production": 0,
            "avg_performance": 0,
            "is_cloudy": False,
            "is_underperforming": False
        }
    
    def get_proposals(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all proposals for a customer from proposals.csv (3xx IDs)"""
        try:
            if self.df_proposals.empty:
                return []
            props = self.df_proposals[self.df_proposals['customer_id'] == customer_id]
            return props.to_dict('records')
        except Exception as e:
            logger.error(f"Error getting proposals for customer {customer_id}: {e}")
            return []
    
    def simulate_otp(self, identifier: str, channel: str) -> str:
        """Generate and store OTP (Deterministic for testing)"""
        try:
            otp_code = "123456" # Hardcoded for test suite compatibility
            timestamp = datetime.now().isoformat()
            
            new_row = pd.DataFrame([{
                channel: identifier,  # 'email' or 'phone' as column name
                'otp': int(otp_code),
                'timestamp': timestamp
            }])
            
            if channel == 'email':
                self.df_email_otp = pd.concat([self.df_email_otp, new_row], ignore_index=True)
                self._save_df(self.df_email_otp, 'email_otp.csv')
            else:  # phone
                self.df_sms_otp = pd.concat([self.df_sms_otp, new_row], ignore_index=True)
                self._save_df(self.df_sms_otp, 'sms_otp.csv')
            
            print(f"📱 SIMULATED OTP for {identifier}: {otp_code}")
            logger.info(f"Generated OTP for {identifier}")
            return otp_code
        except Exception as e:
            logger.error(f"Error generating OTP for {identifier}: {e}")
            return "000000" # Fallback/Error code
    
    def verify_otp(self, identifier: str, channel: str, entered_code: str) -> bool:
        """Verify OTP (no 'used' tracking, just check latest)"""
        try:
            df = self.df_email_otp if channel == 'email' else self.df_sms_otp
            
            if df.empty:
                return False

            # Filter by identifier
            matches = df[df[channel] == identifier]
            if matches.empty:
                return False
            
            # Get latest OTP
            latest = matches.sort_values('timestamp', ascending=False).iloc[0]
            return str(latest['otp']) == str(entered_code)
        except Exception as e:
            logger.error(f"Error verifying OTP for {identifier}: {e}")
            return False
    
    def create_service_ticket(self, ticket_data: Dict[str, Any]) -> str:
        """Append new ticket to service_tickets.csv"""
        try:
            # Generate ticket_id (find max existing ID and increment)
            max_id = 400
            if not self.df_service_tickets.empty:
                max_id = self.df_service_tickets['ticket_id'].max()
                if pd.isna(max_id): max_id = 400
            
            ticket_id = int(max_id) + 1
            
            ticket_data['ticket_id'] = ticket_id
            ticket_data['date_created'] = datetime.now().strftime('%Y-%m-%d')
            ticket_data.setdefault('status', 'Open')
            
            new_row = pd.DataFrame([ticket_data])
            self.df_service_tickets = pd.concat([self.df_service_tickets, new_row], ignore_index=True)
            self._save_df(self.df_service_tickets, 'service_tickets.csv')
            
            return str(ticket_id)
        except Exception as e:
            logger.error(f"Error creating service ticket: {e}")
            return "ERROR"
    
    def create_crm_opportunity(self, opp_data: Dict[str, Any]) -> str:
        """Append new opportunity to crm_opportunities.csv"""
        try:
            # Generate opportunity_id
            max_id = 900
            if not self.df_crm_opportunities.empty:
                max_id = self.df_crm_opportunities['opportunity_id'].max()
                if pd.isna(max_id): max_id = 900
            
            opp_id = int(max_id) + 1
            
            opp_data['opportunity_id'] = opp_id
            opp_data['next_action_date'] = datetime.now().strftime('%Y-%m-%d')
            opp_data.setdefault('status', 'New')
            
            new_row = pd.DataFrame([opp_data])
            self.df_crm_opportunities = pd.concat([self.df_crm_opportunities, new_row], ignore_index=True)
            self._save_df(self.df_crm_opportunities, 'crm_opportunities.csv')
            
            return str(opp_id)
        except Exception as e:
            logger.error(f"Error creating CRM opportunity: {e}")
            return "ERROR"
    
    def check_agent_availability(self, role: str) -> Optional[Dict[str, Any]]:
        """Find available agent by department (Sales/Service)"""
        try:
            if self.df_agent_availability.empty:
                return None

            # Map role to department
            dept = "Sales" if "sales" in role.lower() else "Service"
            
            available = self.df_agent_availability[
                (self.df_agent_availability['department'] == dept) &
                (self.df_agent_availability['is_online'] == True)
            ]
            
            if not available.empty:
                return available.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Error checking agent availability: {e}")
            return None
    
    def generate_proposals(self, sales_profile: Dict[str, Any], num_proposals: int = 1) -> List[Dict[str, Any]]:
        """DETERMINISTIC proposal generation using proposal_template.csv"""
        try:
            if self.df_proposal_template.empty:
                return []

            # Calculate system size
            monthly_bill = float(sales_profile.get("monthly_bill", 5000))
            growth_pct = float(sales_profile.get("growth_pct", 0))
            
            avg_tariff = 8  # Rs per kWh
            monthly_kwh = monthly_bill / avg_tariff
            annual_kwh = monthly_kwh * 12
            system_kw = annual_kwh / 1200  # 1200 units/kW/year
            growth_factor = 1 + (growth_pct / 100)
            final_kw = system_kw * growth_factor
            
            # Round to nearest available size in CSV
            available_sizes = self.df_proposal_template['system_size_kw'].unique()
            if len(available_sizes) > 0:
                final_kw = min(available_sizes, key=lambda x: abs(x - final_kw))
            
            logger.info(f"Calculated system size={final_kw}kW from bill={monthly_bill}, growth={growth_pct}%")
            
            # Filter templates
            tier_prefs = sales_profile.get("tier_prefs", ["Standard"])
            # Ensure tier_prefs is a list
            if isinstance(tier_prefs, str):
                tier_prefs = [tier_prefs]

            templates = self.df_proposal_template[
                (self.df_proposal_template['category'].isin(tier_prefs)) &
                (self.df_proposal_template['system_size_kw'] == final_kw)
            ]
            
            if templates.empty:
                # Fallback: just get any matching size
                templates = self.df_proposal_template[
                    self.df_proposal_template['system_size_kw'] == final_kw
                ]
            
            if templates.empty:
                # Ultimate fallback: get first available template
                logger.warning(f"No templates found for size {final_kw}kW, using first available")
                templates = self.df_proposal_template.head(num_proposals)

            # If we have fewer templates than requested, broaden search
            if len(templates) < num_proposals:
                # Get all templates matching the requested tiers, sorted by closeness to final_kw
                broader = self.df_proposal_template[
                    self.df_proposal_template['category'].isin(tier_prefs)
                ].copy()
                broader['_distance'] = (broader['system_size_kw'] - final_kw).abs()
                broader = broader.sort_values('_distance')
                # Merge with existing, avoiding duplicates
                combined_ids = set(templates['proposal_id'].tolist())
                for _, row in broader.iterrows():
                    if len(templates) >= num_proposals:
                        break
                    if row['proposal_id'] not in combined_ids:
                        templates = pd.concat([templates, pd.DataFrame([row])], ignore_index=True)
                        combined_ids.add(row['proposal_id'])

            templates = templates.head(num_proposals)
            
            # Convert to proposal format
            proposals = []
            for _, tmpl in templates.iterrows():
                proposals.append({
                    "proposal_id": f"PROP-{uuid.uuid4().hex[:6].upper()}",
                    "customer_id": sales_profile.get("customer_id"),
                    "name": tmpl['proposal_name'],
                    "system_size": f"{tmpl['system_size_kw']} kWp",
                    "inverter_brand": tmpl['inverter_brand'],
                    "module_brand": tmpl['module_brand'],
                    "tier": tmpl['category'],
                    "price": tmpl['approx_price'],
                    "yearly_savings": tmpl['estimated_yearly_savings'],
                    "date_created": datetime.now().strftime('%Y-%m-%d'),
                    "status": "Generated"
                })
            
            return proposals
        except Exception as e:
            logger.error(f"Error generating proposals: {e}")
            return []
    
    def _save_df(self, df: pd.DataFrame, filename: str):
        """Save DataFrame to CSV"""
        try:
            df.to_csv(self.data_dir / filename, index=False)
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}")

# Singleton
_instance = None

def get_instance() -> DataService:
    global _instance
    if _instance is None:
        _instance = DataService()
    return _instance

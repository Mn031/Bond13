import re
import pandas as pd
from typing import Dict, List, Any, Optional

class BondScreenerAgent:
    def __init__(self, company_database_path: str, financial_metrics_path: str, news_database_path: str):
        """
        Initialize the Bond Screener Agent with company database and financial metrics
        
        Args:
            company_database_path: Path to the company information database
            financial_metrics_path: Path to the financial metrics database
            news_database_path: Path to the news articles database
        """
        self.company_db = pd.read_csv(company_database_path)
        self.financial_metrics_db = pd.read_csv(financial_metrics_path)
        self.news_db = pd.read_csv(news_database_path)
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load templates for different types of responses"""
        return {
            'company_summary': (
                "## Summary for {company_name}\n\n"
                "**Rating**: {rating}\n"
                "**Sector**: {sector}\n"
                "**Industry**: {industry}\n\n"
                "### Key Metrics\n"
                "- EPS: {eps}\n"
                "- Current Ratio: {current_ratio}\n"
                "- Debt/Equity: {debt_equity}\n"
                "- Debt/EBITDA: {debt_ebitda}\n"
                "- Interest Coverage Ratio: {interest_coverage}\n\n"
                "{company_description}"
            ),
            'company_metric': (
                "The {metric_name} for {company_name} is {metric_value}."
            ),
            'compare_metrics': (
                "## Comparison: {metric_name}\n\n"
                "| Company | {metric_name} |\n"
                "|---------|{dash_line}|\n"
                "{comparison_rows}\n\n"
                "{conclusion}"
            ),
            'pros_cons': (
                "## PROS and CONS for {company_name}\n\n"
                "### PROS\n{pros}\n\n"
                "### CONS\n{cons}"
            ),
            'lenders_list': (
                "## Lenders for {company_name}\n\n"
                "{lenders_list}\n\n"
                "Top 3 lenders: {top_lenders}"
            ),
            'recent_news': (
                "## Recent News for {company_name}\n\n"
                "{news_items}"
            ),
            'error_company_not_found': "Company '{company_name}' was not found in our database."
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a bond screener related query
        
        Args:
            query: User's input query
            
        Returns:
            Dictionary containing the response data
        """
        # Extract company name from query
        company_name = self._extract_company_name(query)
        
        # Check for company summary request
        if re.search(r'(summary|information|about)\s+(for|about|on)\s+', query, re.IGNORECASE):
            if company_name:
                return self._get_company_summary(company_name)
        
        # Check for specific metric request
        metric_match = re.search(r'(what|get|show).+(is|the)\s+(EPS|current ratio|debt[/\\]equity|debt[/\\]EBITDA|interest coverage|operating cashflow|ROE|ROA)', query, re.IGNORECASE)
        if metric_match and company_name:
            metric = metric_match.group(3)
            return self._get_company_metric(company_name, metric)
        
        # Check for metric comparison request
        compare_match = re.search(r'compare\s+(EPS|current ratio|debt[/\\]equity|debt[/\\]EBITDA|interest coverage|operating cashflow|ROE|ROA).+(\w+).+(\w+)', query, re.IGNORECASE)
        if compare_match:
            metric = compare_match.group(1)
            companies = self._extract_multiple_companies(query)
            if len(companies) >= 2:
                return self._compare_company_metrics(companies, metric)
        
        # Check for pros and cons request
        if re.search(r'(pros|cons|strengths|weaknesses)', query, re.IGNORECASE) and company_name:
            return self._get_pros_cons(company_name)
        
        # Check for lenders request
        if re.search(r'(lenders|lent|borrowed|loan)', query, re.IGNORECASE) and company_name:
            return self._get_lenders(company_name)
        
        # Check for news request
        if re.search(r'(news|recent|updates|articles)', query, re.IGNORECASE) and company_name:
            return self._get_recent_news(company_name)
        
        # If company name found but no specific request, return summary
        if company_name:
            return self._get_company_summary(company_name)
        
        # If no specific pattern matches, provide general help
        return {
            'response_type': 'general_help',
            'message': (
                "I can help you analyze companies in our bond screener. "
                "You can ask about:\n\n"
                "- Company summaries and key metrics\n"
                "- Specific financial metrics (EPS, Debt/Equity, etc.)\n"
                "- Compare metrics between companies\n"
                "- Pros and cons of a company\n"
                "- Lenders of a company\n"
                "- Recent news about a company"
            )
        }
    
    def _extract_company_name(self, query: str) -> Optional[str]:
        """Extract company name from query"""
        # Try to find company name patterns
        patterns = [
            r'(for|about|on)\s+([A-Za-z\s]+?)\s+(company|limited|ltd)',
            r'([A-Za-z\s]+?)\s+(company|limited|ltd)',
            r'([A-Za-z\s]+?)\s+(rating|EPS|sector|industry)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Get the company name from the appropriate capture group
                company_name = match.group(2) if 'for|about|on' in pattern else match.group(1)
                # Clean up the company name
                company_name = company_name.strip()
                # Verify that it exists in our database
                if any(self.company_db['company_name'].str.contains(company_name, case=False, na=False)):
                    return company_name
        
        return None
    
    def _extract_multiple_companies(self, query: str) -> List[str]:
        """Extract multiple company names from query for comparison"""
        companies = []
        
        # First try to extract explicit company names
        matches = re.findall(r'([A-Za-z\s]+?)\s+(company|limited|ltd|and|with|to)', query, re.IGNORECASE)
        for match in matches:
            company_name = match[0].strip()
            if any(self.company_db['company_name'].str.contains(company_name, case=False, na=False)):
                companies.append(company_name)
        
        # If we didn't find at least two companies, look for additional patterns
        if len(companies) < 2:
            words = query.split()
            for word in words:
                if word not in companies and len(word) > 3:  # Avoid short words
                    if any(self.company_db['company_name'].str.contains(word, case=False, na=False)):
                        companies.append(word)
        
        return companies
    
    def _get_company_summary(self, company_name: str) -> Dict[str, Any]:
        """Get summary for a specific company"""
        return self._get_cash_flow_schedule(isin)
        
        # If no specific pattern matches, provide general help
        return {
            'response_type': 'general_help',
            'message': (
                "I can help you find information about bonds in our directory. "
                "You can ask about specific ISINs, issuers, filter bonds by criteria, "
                "check maturity dates, or get cash flow schedules. For example:\n\n"
                "- 'Show me details for ISIN INE123456789'\n"
                "- 'Show me all issuances by Ugro Capital'\n"
                "- 'Find secured debentures with coupon rate above 10% and maturity after 2026'\n"
                "- 'Which bonds are maturing in 2025?'\n"
                "- 'Show me the cash flow schedule for ISIN INE567890123'"
            )
        }
    
    def _get_isin_details(self, isin: str) -> Dict[str, Any]:
        """Get details for a specific ISIN"""
        bond = self.bonds_db[self.bonds_db['isin'] == isin]
        
        if bond.empty:
            return {
                'response_type': 'error',
                'message': self.response_templates['error_isin_not_found'].format(isin=isin)
            }
        
        bond_data = bond.iloc[0].to_dict()
        
        return {
            'response_type': 'isin_details',
            'isin': isin,
            'message': self.response_templates['isin_details'].format(
                isin=isin,
                issuer=bond_data.get('issuer_name', 'N/A'),
                issuer_type=bond_data.get('issuer_type', 'N/A'),
                sector=bond_data.get('sector', 'N/A'),
                coupon_rate=bond_data.get('coupon_rate', 'N/A'),
                instrument_name=bond_data.get('instrument_name', 'N/A'),
                face_value=bond_data.get('face_value', 'N/A'),
                issue_size=bond_data.get('issue_size', 'N/A'),
                redemption_date=bond_data.get('redemption_date', 'N/A'),
                credit_rating=bond_data.get('credit_rating', 'N/A'),
                listing_details=bond_data.get('listing_details', 'N/A'),
                documents=bond_data.get('key_documents', 'N/A')
            ),
            'data': bond_data
        }
    
    def _get_issuer_issuances(self, issuer: str) -> Dict[str, Any]:
        """Get all issuances by a specific issuer"""
        bonds = self.bonds_db[self.bonds_db['issuer_name'].str.contains(issuer, case=False, na=False)]
        
        if bonds.empty:
            return {
                'response_type': 'error',
                'message': self.response_templates['error_issuer_not_found'].format(issuer=issuer)
            }
        
        total_bonds = len(bonds)
        active_bonds = len(bonds[bonds['status'] == 'Active'])
        matured_bonds = total_bonds - active_bonds
        
        # Create table of ISINs
        isins_table = ""
        for _, bond in bonds.iterrows():
            isins_table += f"{bond['isin']} | {bond['coupon_rate']}% | {bond['redemption_date']} | ₹{bond['face_value']} | {bond['credit_rating']} | {bond['issue_size']} cr\n"
        
        return {
            'response_type': 'issuer_issuances',
            'issuer': issuer,
            'message': self.response_templates['issuer_issuances'].format(
                issuer=issuer,
                total_bonds=total_bonds,
                active_bonds=active_bonds,
                matured_bonds=matured_bonds,
                isins_table=isins_table
            ),
            'data': bonds.to_dict('records')
        }
    
    def _filter_bonds(self, query: str) -> Dict[str, Any]:
        """Filter bonds based on query criteria"""
        filtered_bonds = self.bonds_db.copy()
        
        # Apply filters based on query
        if re.search(r'secured', query, re.IGNORECASE):
            filtered_bonds = filtered_bonds[filtered_bonds['security_type'] == 'Secured']
        
        if re.search(r'coupon.+above\s+(\d+\.?\d*)%', query, re.IGNORECASE):
            rate_match = re.search(r'coupon.+above\s+(\d+\.?\d*)%', query, re.IGNORECASE)
            if rate_match:
                min_rate = float(rate_match.group(1))
                filtered_bonds = filtered_bonds[filtered_bonds['coupon_rate'] > min_rate]
        
        if re.search(r'maturity.+after\s+(\d{4})', query, re.IGNORECASE):
            year_match = re.search(r'maturity.+after\s+(\d{4})', query, re.IGNORECASE)
            if year_match:
                year = int(year_match.group(1))
                # Convert redemption_date to datetime for comparison
                filtered_bonds['redemption_date'] = pd.to_datetime(filtered_bonds['redemption_date'], errors='coerce')
                filtered_bonds = filtered_bonds[filtered_bonds['redemption_date'].dt.year > year]
        
        count = len(filtered_bonds)
        
        if count == 0:
            return {
                'response_type': 'no_results',
                'message': "No bonds match your specified criteria."
            }
        
        # Create preview of filtered bonds
        bonds_preview = ""
        for _, bond in filtered_bonds.head(5).iterrows():
            bonds_preview += (
                f"● ISIN: {bond['isin']}\n"
                f"● Issuer: {bond['issuer_name']}\n"
                f"● Coupon Rate: {bond['coupon_rate']}%\n"
                f"● Redemption Date: {bond['redemption_date']}\n"
                f"● Security: {bond['security_type']}\n\n"
            )
        
        if count > 5:
            bonds_preview += f"... and {count - 5} more bonds.\n"
        
        return {
            'response_type': 'filtered_bonds',
            'count': count,
            'message': self.response_templates['filtered_bonds'].format(
                count=count,
                bonds_preview=bonds_preview
            ),
            'data': filtered_bonds.to_dict('records')
        }
    
    def _get_bonds_by_maturity_year(self, year: str) -> Dict[str, Any]:
        """Get bonds maturing in a specific year"""
        # Convert redemption_date to datetime for comparison
        self.bonds_db['redemption_date'] = pd.to_datetime(self.bonds_db['redemption_date'], errors='coerce')
        maturing_bonds = self.bonds_db[self.bonds_db['redemption_date'].dt.year == int(year)]
        
        count = len(maturing_bonds)
        
        if count == 0:
            return {
                'response_type': 'no_results',
                'message': f"No bonds found maturing in {year}."
            }
        
        # Create list of maturing bonds
        bonds_list = ""
        for _, bond in maturing_bonds.head(10).iterrows():
            bonds_list += f"● {bond['isin']} | {bond['issuer_name']} | {bond['redemption_date'].strftime('%d-%m-%Y')}\n"
        
        if count > 10:
            bonds_list += f"\n... and {count - 10} more bonds maturing in {year}."
        
        return {
            'response_type': 'maturity_bonds',
            'year': year,
            'count': count,
            'message': f"Found {count} bonds maturing in {year}:\n\n{bonds_list}",
            'data': maturing_bonds.to_dict('records')
        }
    
    def _get_cash_flow_schedule(self, isin: str) -> Dict[str, Any]:
        """Get cash flow schedule for a specific ISIN"""
        # In a real implementation, this would fetch from a cash flow database
        # For this demo, we'll create a simplified example
        bond = self.bonds_db[self.bonds_db['isin'] == isin]
        
        if bond.empty:
            return {
                'response_type': 'error',
                'message': self.response_templates['error_isin_not_found'].format(isin=isin)
            }
        
        bond_data = bond.iloc[0]
        
        # Generate synthetic cash flow schedule based on bond data
        redemption_date = pd.to_datetime(bond_data['redemption_date'])
        coupon_rate = bond_data['coupon_rate']
        
        # Create cash flow schedule with semi-annual payments
        schedule = []
        current_date = redemption_date
        
        # Add principal payment
        schedule.append({
            'date': current_date.strftime('%d-%m-%Y'),
            'type': 'Principal + Interest'
        })
        
        # Add interest payments (semi-annual)
        for i in range(1, 6):  # Up to 3 years of payments
            current_date = current_date - pd.DateOffset(months=6)
            if current_date < pd.Timestamp.now():
                break
                
            schedule.append({
                'date': current_date.strftime('%d-%m-%Y'),
                'type': 'Interest Payment'
            })
        
        schedule.reverse()  # Sort chronologically
        
        # Format the schedule as a table
        schedule_table = "Date | Type\n-----|-----\n"
        for payment in schedule:
            schedule_table += f"{payment['date']} | {payment['type']}\n"
        
        return {
            'response_type': 'cash_flow_schedule',
            'isin': isin,
            'message': f"Cash flow schedule for ISIN {isin}:\n\n{schedule_table}",
            'data': schedule
        }

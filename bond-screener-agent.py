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
        #
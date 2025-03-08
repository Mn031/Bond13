import re
import pandas as pd
from typing import Dict, List, Any, Optional

class BondDirectoryAgent:
    def __init__(self, bonds_database_path: str):
        """
        Initialize the Bond Directory Agent with the bonds database
        
        Args:
            bonds_database_path: Path to the bonds database CSV file
        """
        self.bonds_db = pd.read_csv(bonds_database_path)
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load templates for different types of responses"""
        return {
            'isin_details': (
                "Here are the details for ISIN {isin}:\n\n"
                "● Issuer Name: {issuer}\n"
                "● Type of Issuer: {issuer_type}\n"
                "● Sector: {sector}\n"
                "● Coupon Rate: {coupon_rate}%\n"
                "● Instrument Name: {instrument_name}\n"
                "● Face Value: ₹{face_value}\n"
                "● Total Issue Size: ₹{issue_size} Cr\n"
                "● Redemption Date: {redemption_date}\n"
                "● Credit Rating: {credit_rating}\n"
                "● Listing Details: {listing_details}\n"
                "● Key Documents: {documents}"
            ),
            'issuer_issuances': (
                "{issuer} has issued {total_bonds} bonds in total.\n"
                "{active_bonds} are active, and {matured_bonds} have matured.\n\n"
                "Table of ISINs:\n\n"
                "ISIN | Coupon Rate | Maturity Date | Face Value | Credit Rating | Issuance Size\n"
                "----|-------------|--------------|-----------|--------------|-------------\n"
                "{isins_table}"
            ),
            'filtered_bonds': (
                "There are {count} bonds which fit your criteria. Here are some details:\n\n"
                "{bonds_preview}"
            ),
            'error_isin_not_found': "Sorry, the ISIN {isin} was not found in our database.",
            'error_issuer_not_found': "Sorry, no bonds from {issuer} were found in our database.",
            'error_mismatch': "The given ISIN does not belong to {issuer}. It is associated with {correct_issuer}."
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a bond directory related query
        
        Args:
            query: User's input query
            
        Returns:
            Dictionary containing the response data
        """
        # Check for ISIN lookup
        isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
        if isin_match:
            isin = isin_match.group(1)
            return self._get_isin_details(isin)
        
        # Check for issuer issuances
        issuer_match = re.search(r'(issuances|issued|bonds).+(by|from)\s+([A-Za-z\s]+)', query, re.IGNORECASE)
        if issuer_match:
            issuer = issuer_match.group(3).strip()
            return self._get_issuer_issuances(issuer)
        
        # Check for filtered search
        if re.search(r'(find|search|filter).+(bonds|debentures)', query, re.IGNORECASE):
            return self._filter_bonds(query)
        
        # Check for maturity date lookup
        if re.search(r'(maturing|maturity).+(\d{4})', query, re.IGNORECASE):
            year_match = re.search(r'(\d{4})', query)
            if year_match:
                year = year_match.group(1)
                return self._get_bonds_by_maturity_year(year)
        
        # Check for cash flow schedule
        if re.search(r'(cash\s+flow|schedule).+ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                return self._get_cash_flow_schedule(isin)
        
        # If no specific pattern matches, provide general help
        return {
            'response_type': 'general_help',
            'message': (
                "I can help you find information about bonds in our directory. "
                "You can ask about specific ISINs, issuers,
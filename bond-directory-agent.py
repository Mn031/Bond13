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
            
            # Check if there's also an issuer mentioned
            issuer_match = re.search(r'(issuances|issued|bonds|by|from)\s+([A-Za-z\s]+)', query, re.IGNORECASE)
            if issuer_match:
                issuer = issuer_match.group(2).strip()
                return self._check_isin_issuer_match(isin, issuer)
            
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
        
        # Check for security details inquiry
        if re.search(r'(security|secured).+ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                return self._get_security_details(isin)
        
        # Check for document retrieval
        if re.search(r'(document|doc|offer|trust).+(ISIN|for)\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                return self._get_document_links(isin)
            
            # Check if there's an issuer mentioned instead
            issuer_match = re.search(r'document.+\s+([A-Za-z\s]+)', query, re.IGNORECASE)
            if issuer_match:
                issuer = issuer_match.group(1).strip()
                return self._get_issuer_documents(issuer)
        
        # Check for debenture trustee inquiry
        if re.search(r'(trustee|debenture\s+trustee).+ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                return self._get_debenture_trustee(isin)
        
        # Check for listing exchange & trading status
        if re.search(r'(listing|listed|exchange|trading).+ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                return self._get_listing_details(isin)
        
        # Check for face value inquiry
        if re.search(r'(face\s+value).+ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE):
            isin_match = re.search(r'ISIN\s+([A-Z0-9]+)', query, re.IGNORECASE)
            if isin_match:
                isin = isin_match.group(1)
                
                # Check if there's also an issuer mentioned
                issuer_match = re.search(r'(face\s+value).+([A-Za-z\s]+)\s+bond', query, re.IGNORECASE)
                if issuer_match:
                    issuer = issuer_match.group(2).strip()
                    return self._check_isin_issuer_match(isin, issuer, 'face_value')
                
                return self._get_face_value(isin)
        
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
        
        # Filter by credit rating if specified
        if re.search(r'rated\s+([A-Z]+[+-]?)', query, re.IGNORECASE):
            rating_match = re.search(r'rated\s+([A-Z]+[+-]?)', query, re.IGNORECASE)
            if rating_match:
                rating = rating_match.group(1)
                filtered_bonds = filtered_bonds[filtered_bonds['credit_rating'].str.contains(rating, na=False)]
        
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

import re
import pandas as pd
from typing import Dict, List, Any, Tuple

class BondFinderAgent:
    def __init__(self, bond_finder_database_path: str):
        """
        Initialize the Bond Finder Agent with the bond finder database
        
        Args:
            bond_finder_database_path: Path to the bond finder database CSV file
        """
        self.finder_db = pd.read_csv(bond_finder_database_path)
        self.platforms = ['SMEST', 'FixedIncome']  # Currently tied up with only these two
        self.response_templates = self._load_response_templates()
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load templates for different types of responses"""
        return {
            'general_info': (
                "Currently showcasing bonds available on SMEST and FixedIncome.\n\n"
                "Sample bonds:\n\n"
                "Issuer | Rating | Yield | Available at\n"
                "-------|--------|-------|------------\n"
                "{bonds_table}"
            ),
            'platform_availability': (
                "{issuer} bonds available on {platforms} with a yield range of {yield_range}."
            ),
            'yield_based_search': (
                "Bonds with yield more than {min_yield}%:\n\n"
                "Issuer | Rating | Yield | Available at\n"
                "-------|--------|-------|------------\n"
                "{bonds_table}"
            ),
            'best_yield_comparison': (
                "{platform} offers the highest yield at {yield_value}% for {term}-year bonds."
            ),
            'error_issuer_not_found': "Bonds from {issuer} are currently not available."
        }
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a bond finder related query
        
        Args:
            query: User's input query
            
        Returns:
            Dictionary containing the response data
        """
        # Check for general inquiry
        if re.search(r'(show|what).+(available|bonds).+(bond\s+finder)', query, re.IGNORECASE):
            return self._get_general_info()
        
        # Check for platform availability
        issuer_match = re.search(r'(where|which platform).+(buy|purchase|find).+from\s+([A-Za-z\s]+)', query, re.IGNORECASE)
        if issuer_match:
            issuer = issuer_match.group(3).strip()
            return self._get_platform_availability(issuer)
        
        # Check for yield-based search
        yield_match = re.search(r'(yield|bonds).+(more|greater|higher|above)\s+than\s+(\d+\.?\d*)', query, re.IGNORECASE)
        if yield_match:
            min_yield = float(yield_match.group(3))
            return self._get_bonds_by_yield(min_yield)
        
        # Check for best yield comparison
        if re.search(r'(best|highest|maximum).+(yield|return)', query, re.IGNORECASE):
            # Check if there's a term specified
            term_match = re.search(r'(\d+)[\s-]year', query, re.IGNORECASE)
            term = int(term_match.group(1)) if term_match else None
            return self._get_best_yield_comparison(term)
        
        # Check for credit rating-based search
        rating_match = re.search(r'(rating|rated).+(of|as|with)\s+([A-Z]+[+-]?)', query, re.IGNORECASE)
        if rating_match:
            rating = rating_match.group(3).upper()
            return self._get_bonds_by_rating(rating)
        
        # If no specific pattern matches, provide general help
        return {
            'response_type': 'general_help',
            'message': (
                "I can help you find and compare bonds across different platforms. "
                "You can ask about:\n\n"
                "- Bonds available in the bond finder\n"
                "- Where to buy bonds from a specific issuer\n"
                "- Bonds with yields above a certain percentage\n"
                "- Which platform offers the best yield for a specific term\n"
                "- Bonds with specific credit ratings"
            )
        }
    
    def _get_general_info(self) -> Dict[str, Any]:
        """Get general information about available bonds"""
        # Get a sample of bonds from different issuers
        sample_bonds = self.finder_db.drop_duplicates(subset=['issuer']).head(5)
        
        # Format as a table
        bonds_table = ""
        for _, bond in sample_bonds.iterrows():
            platforms = self._get_platforms_for_issuer(bond['issuer'])
            yield_range = f"{bond['yield_min']}%-{bond['yield_max']}%"
            bonds_table += f"{bond['issuer']} | {
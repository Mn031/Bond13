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
            # Format as a table
        bonds_table = ""
        for _, bond in sample_bonds.iterrows():
            platforms = self._get_platforms_for_issuer(bond['issuer'])
            yield_range = f"{bond['yield_min']}%-{bond['yield_max']}%"
            bonds_table += f"{bond['issuer']} | {bond['rating']} | {yield_range} | {', '.join(platforms)}\n"
        
        return {
            'response_type': 'general_info',
            'message': self.response_templates['general_info'].format(bonds_table=bonds_table),
            'data': sample_bonds.to_dict('records')
        }
    
    def _get_platform_availability(self, issuer: str) -> Dict[str, Any]:
        """Get platforms where bonds from a specific issuer are available"""
        issuer_bonds = self.finder_db[self.finder_db['issuer'].str.contains(issuer, case=False, na=False)]
        
        if issuer_bonds.empty:
            return {
                'response_type': 'error',
                'message': self.response_templates['error_issuer_not_found'].format(issuer=issuer)
            }
        
        platforms = self._get_platforms_for_issuer(issuer)
        
        # Calculate yield range
        min_yield = issuer_bonds['yield_min'].min()
        max_yield = issuer_bonds['yield_max'].max()
        yield_range = f"{min_yield}%-{max_yield}%"
        
        return {
            'response_type': 'platform_availability',
            'issuer': issuer,
            'message': self.response_templates['platform_availability'].format(
                issuer=issuer,
                platforms=', '.join(platforms),
                yield_range=yield_range
            ),
            'data': {
                'issuer': issuer,
                'platforms': platforms,
                'yield_range': yield_range
            }
        }
    
    def _get_bonds_by_yield(self, min_yield: float) -> Dict[str, Any]:
        """Get bonds with yield above a specific threshold"""
        # Filter bonds with yield_max greater than min_yield
        high_yield_bonds = self.finder_db[self.finder_db['yield_max'] > min_yield]
        
        if high_yield_bonds.empty:
            return {
                'response_type': 'no_results',
                'message': f"No bonds found with yield above {min_yield}%."
            }
        
        # Format as a table
        bonds_table = ""
        for _, bond in high_yield_bonds.head(10).iterrows():
            platforms = self._get_platforms_for_issuer(bond['issuer'])
            yield_range = f"{bond['yield_min']}%-{bond['yield_max']}%"
            bonds_table += f"{bond['issuer']} | {bond['rating']} | {yield_range} | {', '.join(platforms)}\n"
        
        if len(high_yield_bonds) > 10:
            bonds_table += f"\n... and {len(high_yield_bonds) - 10} more bonds."
        
        return {
            'response_type': 'yield_based_search',
            'min_yield': min_yield,
            'message': self.response_templates['yield_based_search'].format(
                min_yield=min_yield,
                bonds_table=bonds_table
            ),
            'data': high_yield_bonds.to_dict('records')
        }
    
    def _get_best_yield_comparison(self, term: int = None) -> Dict[str, Any]:
        """Get platform offering the best yield for a specific term"""
        filtered_bonds = self.finder_db.copy()
        
        # Filter by term if specified
        if term is not None:
            # This would require a term/duration column in the database
            # For now, we'll simulate this filtering
            filtered_bonds = filtered_bonds[filtered_bonds['term_years'] == term]
        
        if filtered_bonds.empty:
            return {
                'response_type': 'no_results',
                'message': f"No bonds found{' for ' + str(term) + '-year term' if term else ''}."
            }
        
        # Find the bond with the highest yield
        best_bond = filtered_bonds.loc[filtered_bonds['yield_max'].idxmax()]
        platforms = self._get_platforms_for_issuer(best_bond['issuer'])
        
        # Determine which platform has this bond with the highest yield
        # In a real implementation, this would check yield by platform
        # For this demo, we'll just use the first platform
        best_platform = platforms[0] if platforms else "N/A"
        
        return {
            'response_type': 'best_yield_comparison',
            'term': term,
            'message': self.response_templates['best_yield_comparison'].format(
                platform=best_platform,
                yield_value=best_bond['yield_max'],
                term=term if term else "all"
            ),
            'data': {
                'platform': best_platform,
                'issuer': best_bond['issuer'],
                'yield': best_bond['yield_max'],
                'term': term
            }
        }
    
    def _get_bonds_by_rating(self, rating: str) -> Dict[str, Any]:
        """Get bonds with a specific credit rating"""
        # Filter bonds by rating
        # This would handle ratings like "AA+" or "A-"
        rating_bonds = self.finder_db[self.finder_db['rating'].str.contains(rating, regex=False)]
        
        if rating_bonds.empty:
            return {
                'response_type': 'no_results',
                'message': f"No bonds found with rating {rating}."
            }
        
        # Format as a table
        bonds_table = ""
        for _, bond in rating_bonds.head(10).iterrows():
            platforms = self._get_platforms_for_issuer(bond['issuer'])
            yield_range = f"{bond['yield_min']}%-{bond['yield_max']}%"
            maturity = bond.get('maturity_date', 'N/A')
            bonds_table += f"{bond['issuer']} | {bond['rating']} | {yield_range} | {maturity} | {', '.join(platforms)}\n"
        
        if len(rating_bonds) > 10:
            bonds_table += f"\n... and {len(rating_bonds) - 10} more bonds."
        
        return {
            'response_type': 'rating_based_search',
            'rating': rating,
            'message': f"Bonds with rating {rating}:\n\nIssuer | Rating | Yield | Maturity | Available at\n-------|--------|-------|----------|------------\n{bonds_table}",
            'data': rating_bonds.to_dict('records')
        }
    
    def _get_platforms_for_issuer(self, issuer: str) -> List[str]:
        """Get platforms where bonds from a specific issuer are available"""
        issuer_bonds = self.finder_db[self.finder_db['issuer'] == issuer]
        platforms = []
        
        # In a real implementation, this would check the platform availability
        # For this demo, we'll just simulate the availability
        for platform in self.platforms:
            if any(issuer_bonds[f'available_on_{platform.lower()}']):
                platforms.append(platform)
        
        return platforms

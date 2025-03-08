import re
from typing import Dict, List, Any

class OrchestratorAgent:
    def __init__(self, specialized_agents: Dict):
        """
        Initialize the Orchestrator Agent with specialized agents
        
        Args:
            specialized_agents: Dictionary of specialized agents keyed by their type
        """
        self.specialized_agents = specialized_agents
        
        # Define keywords and patterns for each agent type
        self.agent_patterns = {
            'bond_directory': [
                r'ISIN\s+([A-Z0-9]+)',
                r'(show|find|get|details|information).+(ISIN|bond)',
                r'(issuer|coupon|maturity|face value|rating).*bond',
                r'(debenture|trustee)',
                r'(issuances|issued|bonds).+(by|from)\s+([A-Za-z\s]+)'
            ],
            'bond_finder': [
                r'(available|find|where.+buy).+(bonds|yield)',
                r'(compare|best|highest).+(yield|platform)',
                r'(bonds|yield).+(platform|SMEST|FixedIncome)',
                r'bond\s+finder'
            ],
            'cash_flow': [
                r'(cash\s+flow|payment|schedule).+(ISIN|bond)',
                r'(maturity|maturing|redemption).+(date|in|on)',
                r'(interest|coupon).+(payment|date)'
            ],
            'bond_screener': [
                r'(company|financial|analysis|metrics|ratio)',
                r'(EPS|debt|equity|EBITDA|interest\s+coverage|ratio)',
                r'(compare|pros|cons|lenders|news|rating|sector|industry)',
                r'(current\s+ratio|growth\s+rate)'
            ],
            'yield_calculator': [
                r'(calculate|computation|calculation).+(yield|price|consideration)',
                r'(clean\s+price|consideration).+(bond|ISIN)',
                r'price\s+to\s+yield',
                r'yield\s+to\s+price'
            ]
        }
    
    def determine_agent(self, query: str) -> str:
        """
        Determine which specialized agent should handle the query
        
        Args:
            query: User's input query
            
        Returns:
            Agent type ('bond_directory', 'bond_finder', etc.)
        """
        scores = {agent_type: 0 for agent_type in self.specialized_agents.keys()}
        
        # Score each agent type based on pattern matches
        for agent_type, patterns in self.agent_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    scores[agent_type] += len(matches)
        
        # Get the agent with the highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            # Default to directory for general questions
            return 'bond_directory'
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a user query by routing to the appropriate specialized agent
        
        Args:
            query: User's input query
            
        Returns:
            Dictionary containing the response and metadata
        """
        agent_type = self.determine_agent(query)
        agent = self.specialized_agents[agent_type]
        
        response = agent.process_query(query)
        
        # Enhance response with metadata
        result = {
            'agent_type': agent_type,
            'response': response,
            'query': query,
            'confidence': self._calculate_confidence(query, agent_type)
        }
        
        return result
    
    def _calculate_confidence(self, query: str, agent_type: str) -> float:
        """
        Calculate confidence score for agent selection
        
        Args:
            query: User's input query
            agent_type: Selected agent type
            
        Returns:
            Confidence score between 0 and 1
        """
        total_patterns = sum(len(patterns) for patterns in self.agent_patterns.values())
        agent_patterns = self.agent_patterns[agent_type]
        
        matches = 0
        for pattern in agent_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                matches += 1
        
        # Calculate confidence based on pattern matches
        if matches == 0:
            return 0.5  # Default confidence
        else:
            return min(0.5 + (matches / len(agent_patterns)) * 0.5, 1.0)

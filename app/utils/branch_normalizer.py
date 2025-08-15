"""
Branch normalization utilities to convert full branch names to standardized abbreviations.
Examples: 
- Computer Science and Engineering -> CSE
- Computer Engineering -> CE  
- Mechanical Engineering -> ME
"""

import re
from typing import Dict, List, Tuple

class BranchNormalizer:
    def __init__(self):
        # Dictionary mapping normalized names to their variations
        self.branch_mappings = {
            # Computer Science related
            "CSE": [
                "Computer Science and Engineering",
                "Computer Science & Engineering", 
                "Computer Engineering",
                "Computer Science",
                "Computer Science and Engineering (Artificial Intelligence)",
                "Computer Science and Engineering (Artificial Intelligence and Data Science)",
                "Computer Science and Engineering(Artificial Intelligence and Machine Learning)",
                "Computer Science and Engineering (Cyber Security)",
                "Computer Science and Engineering(Cyber Security)",
                "Computer Science and Engineering(Data Science)",
                "Computer Science and Engineering (Internet of Things and Cyber Security Including Block Chain",
                "Computer Engineering (Software Engineering)",
                "Computer Science and Business Systems",
                "Computer Science and Design"
            ],
            
            # Information Technology
            "IT": [
                "Information Technology",
                "Information Technology Engineering",
                "Information Technology and Engineering"
            ],
            
            # Electronics and related
            "ECE": [
                "Electronics and Communication Engineering",
                "Electronics & Communication Engineering",
                "Electronics and Communications Engineering",
                "Electronics and Telecommunication Engineering",
                "Electronics & Telecommunication Engineering",
                "Electronics Engineering"
            ],
            
            "EEE": [
                "Electrical and Electronics Engineering",
                "Electrical & Electronics Engineering",
                "Electrical Engineering"
            ],
            
            "ETC": [
                "Electronics and Telecommunication",
                "Electronics & Telecommunication"
            ],
            
            # Mechanical Engineering
            "ME": [
                "Mechanical Engineering",
                "Mechanical and Automation Engineering",
                "Mechanical & Automation Engineering"
            ],
            
            # Civil Engineering
            "CE": [
                "Civil Engineering",
                "Civil and Environmental Engineering", 
                "Civil & Environmental Engineering",
                "Civil and infrastructure Engineering",
                "Civil Engineering and Planning"
            ],
            
            # Chemical Engineering
            "CHE": [
                "Chemical Engineering",
                "Chemical Technology"
            ],
            
            # Biotechnology
            "BT": [
                "Bio Technology",
                "Biotechnology",
                "Bio-Technology"
            ],
            
            # Biomedical Engineering
            "BME": [
                "Bio Medical Engineering",
                "Biomedical Engineering",
                "Bio-Medical Engineering"
            ],
            
            # Automobile Engineering
            "AE": [
                "Automobile Engineering",
                "Automotive Engineering"
            ],
            
            # Aeronautical Engineering
            "AERO": [
                "Aeronautical Engineering",
                "Aerospace Engineering"
            ],
            
            # Agricultural Engineering
            "AGE": [
                "Agricultural Engineering",
                "Agriculture Engineering"
            ],
            
            # Artificial Intelligence and Data Science
            "AIDS": [
                "Artificial Intelligence and Data Science",
                "Artificial Intelligence & Data Science",
                "AI and Data Science"
            ],
            
            # Artificial Intelligence and Machine Learning
            "AIML": [
                "Artificial Intelligence and Machine Learning",
                "Artificial Intelligence & Machine Learning",
                "AI and Machine Learning"
            ],
            
            # Data Science
            "DS": [
                "Data Science",
                "Data Science and Engineering"
            ],
            
            # Artificial Intelligence
            "AI": [
                "Artificial Intelligence"
            ],
            
            # Automation and Robotics
            "AR": [
                "Automation and Robotics",
                "Automation & Robotics",
                "Robotics and Automation"
            ],
            
            # Architecture
            "ARCH": [
                "Architecture",
                "Architectural Assistantship"
            ],
            
            # Other specialized branches
            "5G": [
                "5G",
                "5G Technology"
            ]
        }
        
        # Create reverse mapping for quick lookup
        self.full_name_to_normalized = {}
        for normalized, variations in self.branch_mappings.items():
            for variation in variations:
                self.full_name_to_normalized[variation.lower()] = normalized
    
    def normalize_branch(self, branch_name: str) -> str:
        """
        Normalize a branch name to its standard abbreviation.
        
        Args:
            branch_name: Full branch name
            
        Returns:
            Normalized abbreviation or original name if no mapping found
        """
        if not branch_name:
            return branch_name
            
        branch_lower = branch_name.strip().lower()
        
        # Direct lookup
        if branch_lower in self.full_name_to_normalized:
            return self.full_name_to_normalized[branch_lower]
        
        # Fuzzy matching for partial matches
        for normalized, variations in self.branch_mappings.items():
            for variation in variations:
                if self._fuzzy_match(branch_lower, variation.lower()):
                    return normalized
        
        # If no match found, return original (cleaned)
        return branch_name.strip()
    
    def _fuzzy_match(self, branch_lower: str, variation_lower: str) -> bool:
        """
        Check if branch name fuzzy matches a variation.
        This handles minor differences in punctuation, spacing, etc.
        """
        # Remove common punctuation and extra spaces
        branch_clean = re.sub(r'[&(),.-]', ' ', branch_lower)
        branch_clean = re.sub(r'\s+', ' ', branch_clean).strip()
        
        variation_clean = re.sub(r'[&(),.-]', ' ', variation_lower)  
        variation_clean = re.sub(r'\s+', ' ', variation_clean).strip()
        
        return branch_clean == variation_clean
    
    def get_all_branches_with_normalized(self, branches: List[str]) -> List[Tuple[str, str]]:
        """
        Get list of (original, normalized) tuples for all branches.
        
        Args:
            branches: List of original branch names
            
        Returns:
            List of (original_name, normalized_name) tuples
        """
        result = []
        seen_normalized = set()
        
        for branch in branches:
            if not branch or not branch.strip():
                continue
                
            normalized = self.normalize_branch(branch)
            
            # Avoid duplicates based on normalized name
            if normalized not in seen_normalized:
                result.append((branch, normalized))
                seen_normalized.add(normalized)
        
        return sorted(result, key=lambda x: x[1])  # Sort by normalized name
    
    def get_normalized_branches(self, branches: List[str]) -> List[str]:
        """
        Get list of unique normalized branch names.
        
        Args:
            branches: List of original branch names
            
        Returns:
            List of unique normalized branch names, sorted
        """
        normalized_set = set()
        
        for branch in branches:
            if not branch or not branch.strip():
                continue
                
            normalized = self.normalize_branch(branch)
            normalized_set.add(normalized)
        
        return sorted(list(normalized_set))

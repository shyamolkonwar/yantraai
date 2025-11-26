"""
K-Lingua v2.0 - Consistency Checker
Cross-field validation across document
"""

from typing import Dict, List, Optional
import re


class ConsistencyChecker:
    """
    Cross-field consistency validation
    """
    
    def __init__(self):
        """Initialize consistency checker"""
        pass
    
    def check_consistency(
        self,
        fields: List[Dict],
        field_types: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Check consistency across document fields
        
        Args:
            fields: List of extracted fields with text and metadata
            field_types: Optional mapping of field names to types
        
        Returns:
            Dict with consistency check results
        """
        if not fields or len(fields) < 2:
            return {
                'is_consistent': True,
                'consistency_flags': [],
                'consistency_score': 1.0
            }
        
        flags = []
        
        # Check name consistency
        name_flags = self._check_name_consistency(fields)
        flags.extend(name_flags)
        
        # Check date format consistency
        date_flags = self._check_date_consistency(fields)
        flags.extend(date_flags)
        
        # Check amount format consistency
        amount_flags = self._check_amount_consistency(fields)
        flags.extend(amount_flags)
        
        # Calculate overall consistency score
        consistency_score = 1.0 - (len(flags) * 0.1)
        consistency_score = max(0.0, min(1.0, consistency_score))
        
        return {
            'is_consistent': len(flags) == 0,
            'consistency_flags': flags,
            'consistency_score': consistency_score
        }
    
    def _check_name_consistency(self, fields: List[Dict]) -> List[Dict]:
        """
        Check patient/person name consistency
        
        Args:
            fields: List of fields
        
        Returns:
            List of consistency flags
        """
        flags = []
        
        # Extract name fields
        names = []
        for field in fields:
            if 'name' in field.get('field_type', '').lower():
                names.append(field.get('text', ''))
        
        if len(names) < 2:
            return flags
        
        # Check if names are consistent
        # Allow for abbreviations and middle name variations
        base_names = [self._normalize_name(name) for name in names]
        
        if len(set(base_names)) > 1:
            flags.append({
                'type': 'name_inconsistency',
                'severity': 'medium',
                'message': f'Name variations found: {", ".join(names)}'
            })
        
        return flags
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize name for comparison
        
        Args:
            name: Input name
        
        Returns:
            Normalized name
        """
        # Remove middle names, keep first and last
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1]}".lower()
        return name.lower()
    
    def _check_date_consistency(self, fields: List[Dict]) -> List[Dict]:
        """
        Check date format consistency
        
        Args:
            fields: List of fields
        
        Returns:
            List of consistency flags
        """
        flags = []
        
        # Extract date fields
        dates = []
        for field in fields:
            text = field.get('text', '')
            if self._looks_like_date(text):
                dates.append(text)
        
        if len(dates) < 2:
            return flags
        
        # Check if date formats are consistent
        formats = [self._detect_date_format(date) for date in dates]
        
        if len(set(formats)) > 1:
            flags.append({
                'type': 'date_format_inconsistency',
                'severity': 'low',
                'message': f'Multiple date formats found: {", ".join(set(formats))}'
            })
        
        return flags
    
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date"""
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{2,4}[/-]\d{1,2}[/-]\d{1,2}',
            r'\d{1,2}\s+[A-Za-z]+\s+\d{2,4}'
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _detect_date_format(self, date: str) -> str:
        """Detect date format"""
        if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', date):
            return 'DD/MM/YYYY'
        elif re.search(r'\d{1,2}-\d{1,2}-\d{2,4}', date):
            return 'DD-MM-YYYY'
        elif re.search(r'\d{2,4}/\d{1,2}/\d{1,2}', date):
            return 'YYYY/MM/DD'
        elif re.search(r'\d{1,2}\s+[A-Za-z]+\s+\d{2,4}', date):
            return 'DD Month YYYY'
        else:
            return 'unknown'
    
    def _check_amount_consistency(self, fields: List[Dict]) -> List[Dict]:
        """
        Check amount format consistency
        
        Args:
            fields: List of fields
        
        Returns:
            List of consistency flags
        """
        flags = []
        
        # Extract amount fields
        amounts = []
        for field in fields:
            text = field.get('text', '')
            if self._looks_like_amount(text):
                amounts.append(text)
        
        if len(amounts) < 2:
            return flags
        
        # Check decimal consistency
        has_decimal = [bool(re.search(r'\.\d+', amt)) for amt in amounts]
        
        if any(has_decimal) and not all(has_decimal):
            flags.append({
                'type': 'amount_format_inconsistency',
                'severity': 'low',
                'message': 'Inconsistent decimal usage in amounts'
            })
        
        return flags
    
    def _looks_like_amount(self, text: str) -> bool:
        """Check if text looks like an amount"""
        amount_patterns = [
            r'[₹$€£]\s*\d+',
            r'\d+\s*(?:rupees?|dollars?|euros?)',
            r'^\d+(?:\.\d+)?$'
        ]
        
        for pattern in amount_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

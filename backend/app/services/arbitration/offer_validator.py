"""
Offer Validator
Checks discount limits against policies
"""

from typing import Dict, Any, Optional, List


class OfferValidationError:
    """Offer validation error"""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
    
    def to_dict(self) -> Dict[str, str]:
        return {"field": self.field, "message": self.message}


class OfferValidator:
    """Validator for offer details against policy limits"""
    
    def validate_offer(
        self,
        offer: Optional[Dict[str, Any]],
        policy_rules: Dict[str, Any],
        estimated_value: int
    ) -> tuple[bool, List[OfferValidationError]]:
        """
        Validate offer against policy rules
        
        Args:
            offer: Offer dictionary (discount_type, discount_value, etc.)
            policy_rules: Policy rules dictionary
            estimated_value: Estimated transaction value in paise
        
        Returns:
            Tuple of (is_valid, errors_list)
        """
        errors = []
        
        # If no offer, nothing to validate
        if not offer:
            return (True, [])
        
        # Extract offer details
        discount_type = offer.get("discount_type")
        discount_value = offer.get("discount_value", 0)
        max_discount = offer.get("max_discount")
        min_purchase = offer.get("min_purchase")
        
        # Validate discount type
        if discount_type not in ["PERCENTAGE", "FLAT"]:
            errors.append(OfferValidationError(
                "discount_type",
                f"Invalid discount type: {discount_type}. Must be PERCENTAGE or FLAT"
            ))
            return (False, errors)
        
        # Validate discount value is positive
        if discount_value <= 0:
            errors.append(OfferValidationError(
                "discount_value",
                "Discount value must be positive"
            ))
        
        # Validate against policy limits
        max_discount_pct = policy_rules.get("max_discount_pct", 30)
        max_discount_value = policy_rules.get("max_discount_value", 500000)  # paise
        
        if discount_type == "PERCENTAGE":
            # Check percentage limit
            if discount_value > max_discount_pct:
                errors.append(OfferValidationError(
                    "discount_value",
                    f"Discount percentage {discount_value}% exceeds policy limit {max_discount_pct}%"
                ))
            
            # Calculate actual discount amount and check value limit
            if estimated_value > 0:
                actual_discount = (discount_value / 100) * estimated_value
                if max_discount:
                    actual_discount = min(actual_discount, max_discount)
                
                if actual_discount > max_discount_value:
                    errors.append(OfferValidationError(
                        "discount_value",
                        f"Discount amount ₹{actual_discount/100:.2f} exceeds policy limit ₹{max_discount_value/100:.2f}"
                    ))
        
        elif discount_type == "FLAT":
            # Check flat discount against value limit
            if discount_value > max_discount_value:
                errors.append(OfferValidationError(
                    "discount_value",
                    f"Flat discount ₹{discount_value/100:.2f} exceeds policy limit ₹{max_discount_value/100:.2f}"
                ))
            
            # Check discount doesn't exceed estimated value
            if estimated_value > 0 and discount_value > estimated_value:
                errors.append(OfferValidationError(
                    "discount_value",
                    f"Discount ₹{discount_value/100:.2f} exceeds estimated value ₹{estimated_value/100:.2f}"
                ))
        
        # Validate max_discount if present
        if max_discount is not None:
            if max_discount <= 0:
                errors.append(OfferValidationError(
                    "max_discount",
                    "Max discount must be positive"
                ))
            
            if max_discount > max_discount_value:
                errors.append(OfferValidationError(
                    "max_discount",
                    f"Max discount ₹{max_discount/100:.2f} exceeds policy limit ₹{max_discount_value/100:.2f}"
                ))
        
        # Validate min_purchase if present
        if min_purchase is not None:
            if min_purchase < 0:
                errors.append(OfferValidationError(
                    "min_purchase",
                    "Min purchase cannot be negative"
                ))
            
            # Warn if min_purchase is higher than estimated_value
            if estimated_value > 0 and min_purchase > estimated_value:
                errors.append(OfferValidationError(
                    "min_purchase",
                    f"Min purchase ₹{min_purchase/100:.2f} exceeds estimated value ₹{estimated_value/100:.2f}"
                ))
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def calculate_effective_discount(
        self,
        offer: Dict[str, Any],
        transaction_value: int
    ) -> int:
        """
        Calculate effective discount amount in paise
        
        Args:
            offer: Offer dictionary
            transaction_value: Transaction value in paise
        
        Returns:
            Effective discount in paise
        """
        discount_type = offer.get("discount_type")
        discount_value = offer.get("discount_value", 0)
        max_discount = offer.get("max_discount")
        min_purchase = offer.get("min_purchase", 0)
        
        # Check minimum purchase requirement
        if transaction_value < min_purchase:
            return 0
        
        if discount_type == "PERCENTAGE":
            discount = int((discount_value / 100) * transaction_value)
            if max_discount:
                discount = min(discount, max_discount)
            return discount
        
        elif discount_type == "FLAT":
            return min(discount_value, transaction_value)
        
        return 0
    
    def to_dict(
        self,
        is_valid: bool,
        errors: List[OfferValidationError]
    ) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            "is_valid": is_valid,
            "errors": [error.to_dict() for error in errors],
            "error_count": len(errors)
        }

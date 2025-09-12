"""
Cost tracking and token usage calculation for LLM API calls.
"""
from litellm import completion_cost, cost_per_token
from config import PRICING_FALLBACK


def calculate_cost_and_tokens(response, model_param):
    """
    Calculate cost and extract token usage from LLM response.
    
    Args:
        response: LLM API response object
        model_param: Model parameter string (e.g., "groq/llama-4-scout")
        
    Returns:
        dict: Cost and token data or None if no usage data available
    """
    if not (hasattr(response, 'usage') and response.usage):
        print("[DEBUG] No usage data in response")
        return None
        
    input_tokens = getattr(response.usage, 'prompt_tokens', 0)
    output_tokens = getattr(response.usage, 'completion_tokens', 0)
    
    print(f"[DEBUG] Token usage - Input: {input_tokens}, Output: {output_tokens}")
    
    # Try LiteLLM's built-in cost calculation first
    try:
        total_cost = completion_cost(completion_response=response)
        print(f"[DEBUG] Total cost from completion_cost(): {total_cost}")
        
        # Get cost breakdown per token type
        try:
            prompt_cost_per_token, completion_cost_per_token = cost_per_token(
                model=model_param, 
                prompt_tokens=input_tokens, 
                completion_tokens=output_tokens
            )
            input_cost = prompt_cost_per_token
            output_cost = completion_cost_per_token
            print(f"[DEBUG] Cost per token - Input: {input_cost}, Output: {output_cost}")
        except Exception as e:
            print(f"[DEBUG] Error getting cost_per_token: {e}")
            # Fallback: estimate breakdown
            input_cost = total_cost * 0.4 if total_cost else 0
            output_cost = total_cost * 0.6 if total_cost else 0
        
        if total_cost is None:
            total_cost = 0
            
    except Exception as e:
        print(f"[DEBUG] Error calculating cost: {e}")
        # Use fallback pricing
        total_cost, input_cost, output_cost = _calculate_fallback_cost(
            model_param, input_tokens, output_tokens
        )
    
    cost_data = {
        "total_cost": total_cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
    }
    
    print(f"[DEBUG] Final cost data: {cost_data}")
    return cost_data


def _calculate_fallback_cost(model_param, input_tokens, output_tokens):
    """
    Calculate cost using fallback pricing when LiteLLM cost functions fail.
    
    Args:
        model_param: Model parameter string
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        tuple: (total_cost, input_cost, output_cost)
    """
    if model_param in PRICING_FALLBACK:
        pricing = PRICING_FALLBACK[model_param]
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        print(f"[DEBUG] Using fallback pricing: {total_cost}")
        return total_cost, input_cost, output_cost
    else:
        print(f"[DEBUG] No fallback pricing for model: {model_param}")
        return 0, 0, 0


def format_cost_display(cost_data):
    """
    Format cost data for UI display.
    
    Args:
        cost_data: Dictionary containing cost and token information
        
    Returns:
        dict: Formatted display strings
    """
    if not cost_data:
        return None
        
    total_cost = cost_data.get('total_cost', 0)
    input_tokens = cost_data.get('input_tokens', 0)
    output_tokens = cost_data.get('output_tokens', 0)
    input_cost = cost_data.get('input_cost', 0)
    output_cost = cost_data.get('output_cost', 0)
    
    total_tokens = input_tokens + output_tokens
    
    return {
        'cost_str': f"${total_cost:.4f}",
        'token_str': f"{total_tokens:,}",
        'delta_str': f"{total_tokens:,} tokens",
        'help_text': (
            f"Input: {input_tokens:,} tokens (${input_cost:.4f})\n"
            f"Output: {output_tokens:,} tokens (${output_cost:.4f})\n"
            f"Total: {total_tokens:,} tokens (${total_cost:.4f})"
        ),
        'breakdown_str': f"In: {input_tokens:,} | Out: {output_tokens:,}"
    }


def should_show_cost(cost_data):
    """
    Determine if cost information should be displayed.
    
    Args:
        cost_data: Dictionary containing cost information
        
    Returns:
        bool: True if cost should be shown, False otherwise
    """
    return cost_data and cost_data.get('total_cost', 0) > 0
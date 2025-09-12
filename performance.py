"""
Performance tracking and statistics for API calls.
"""
import time
import streamlit as st


def update_performance_history(provider, model, processing_time, token_usage=None):
    """
    Update performance history for provider comparison.
    
    Args:
        provider: Provider name (e.g., "Mistral")
        model: Model name (e.g., "mistral-small-2506")  
        processing_time: Dictionary with timing data
        token_usage: Optional dictionary with cost and token data
    """
    if 'performance_history' not in st.session_state:
        st.session_state['performance_history'] = []
    
    # Add current performance data
    performance_data = {
        'provider': provider,
        'model': model,
        'timestamp': time.time(),
        'total_time': processing_time.get('total', 0),
        'api_time': processing_time.get('api_call', 0)
    }
    
    # Add token usage and cost if available
    if token_usage:
        performance_data.update(token_usage)
    
    # Keep only last 10 entries to avoid memory issues
    st.session_state['performance_history'].append(performance_data)
    if len(st.session_state['performance_history']) > 10:
        st.session_state['performance_history'] = st.session_state['performance_history'][-10:]


def get_provider_stats():
    """
    Get average performance stats by provider and model including costs.
    
    Returns:
        dict: Performance statistics organized by provider-model key
    """
    if 'performance_history' not in st.session_state:
        return {}
    
    history = st.session_state['performance_history']
    provider_stats = {}
    
    for entry in history:
        provider = entry['provider']
        model = entry.get('model', 'Unknown')
        key = f"{provider} - {model}"
        
        if key not in provider_stats:
            provider_stats[key] = {
                'times': [], 
                'costs': [],
                'input_tokens': [],
                'output_tokens': [],
                'count': 0,
                'provider': provider,
                'model': model
            }
        
        provider_stats[key]['times'].append(entry['total_time'])
        provider_stats[key]['count'] += 1
        
        # Add cost and token data if available
        if 'total_cost' in entry:
            provider_stats[key]['costs'].append(entry['total_cost'])
        if 'input_tokens' in entry:
            provider_stats[key]['input_tokens'].append(entry['input_tokens'])
        if 'output_tokens' in entry:
            provider_stats[key]['output_tokens'].append(entry['output_tokens'])
    
    # Calculate averages
    for key in provider_stats:
        stats = provider_stats[key]
        times = stats['times']
        costs = stats['costs']
        
        stats['avg_time'] = sum(times) / len(times) if times else 0
        stats['min_time'] = min(times) if times else 0
        stats['max_time'] = max(times) if times else 0
        
        # Cost averages
        if costs:
            stats['avg_cost'] = sum(costs) / len(costs)
            stats['total_cost'] = sum(costs)
        else:
            stats['avg_cost'] = 0
            stats['total_cost'] = 0
        
        # Token averages
        if stats['input_tokens']:
            stats['avg_input_tokens'] = sum(stats['input_tokens']) / len(stats['input_tokens'])
            stats['total_input_tokens'] = sum(stats['input_tokens'])
        else:
            stats['avg_input_tokens'] = 0
            stats['total_input_tokens'] = 0
            
        if stats['output_tokens']:
            stats['avg_output_tokens'] = sum(stats['output_tokens']) / len(stats['output_tokens'])
            stats['total_output_tokens'] = sum(stats['output_tokens'])
        else:
            stats['avg_output_tokens'] = 0
            stats['total_output_tokens'] = 0
    
    return provider_stats


def format_performance_stats_display(stats):
    """
    Format performance statistics for UI display.
    
    Args:
        stats: Dictionary with performance statistics
        
    Returns:
        dict: Formatted display data
    """
    avg_time = stats['avg_time']
    count = stats['count']
    provider = stats['provider']
    model = stats['model']
    avg_cost = stats.get('avg_cost', 0)
    total_cost = stats.get('total_cost', 0)
    avg_input_tokens = stats.get('avg_input_tokens', 0)
    avg_output_tokens = stats.get('avg_output_tokens', 0)
    
    # Format time display
    if avg_time < 1:
        time_display = f"{avg_time*1000:.0f}ms"
    else:
        time_display = f"{avg_time:.2f}s"
    
    # Format cost display
    cost_display = f"${avg_cost:.4f}" if avg_cost > 0 else "N/A"
    
    # Truncate long model names for display
    display_model = model
    if len(model) > 20:
        display_model = model[:17] + "..."
    
    # Create help text with comprehensive info
    help_text = (
        f"Model: {model}\n"
        f"Tests: {count}\n"
        f"Time - Min: {stats['min_time']:.3f}s | "
        f"Max: {stats['max_time']:.3f}s | "
        f"Avg: {stats['avg_time']:.3f}s"
    )
    
    if avg_cost > 0:
        help_text += (
            f"\nCost - Avg: ${avg_cost:.4f} | Total: ${total_cost:.4f}"
            f"\nTokens - Input: {avg_input_tokens:.0f} | Output: {avg_output_tokens:.0f}"
        )
    
    # Show both time and cost if available
    if avg_cost > 0:
        delta_text = f"{cost_display} • {display_model} ({count})"
    else:
        delta_text = f"{display_model} ({count})"
    
    return {
        'provider': provider,
        'time_display': time_display,
        'delta_text': delta_text,
        'help_text': help_text
    }


def create_timing_data(start_time, api_start_time, api_end_time, end_time):
    """
    Create timing data dictionary from timestamps.
    
    Args:
        start_time: Process start timestamp
        api_start_time: API call start timestamp  
        api_end_time: API call end timestamp
        end_time: Process end timestamp
        
    Returns:
        dict: Timing data
    """
    return {
        'total': end_time - start_time,
        'api_call': api_end_time - api_start_time,
        'preprocessing': api_start_time - start_time,
        'postprocessing': end_time - api_end_time
    }
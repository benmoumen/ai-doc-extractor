/**
 * Debug configuration for the frontend application
 * Controls visibility of debug features and sensitive information
 */

export const DEBUG_CONFIG = {
  // Enable debug mode in development or when explicitly enabled
  enabled: process.env.NODE_ENV === 'development' ||
           process.env.NEXT_PUBLIC_DEBUG_MODE === 'true',

  // Control specific debug features
  features: {
    // Show AI debug dialog with prompts and responses
    aiDebugDialog: process.env.NODE_ENV === 'development' ||
                   process.env.NEXT_PUBLIC_AI_DEBUG === 'true',

    // Show console logs for AI debug info
    aiDebugConsole: process.env.NODE_ENV === 'development',

    // Show detailed error information
    detailedErrors: process.env.NODE_ENV === 'development',

    // Show performance metrics
    performanceMetrics: process.env.NODE_ENV === 'development' ||
                        process.env.NEXT_PUBLIC_PERFORMANCE_DEBUG === 'true'
  }
};

/**
 * Check if debug mode is enabled
 */
export const isDebugEnabled = (): boolean => {
  return DEBUG_CONFIG.enabled;
};

/**
 * Check if a specific debug feature is enabled
 */
export const isDebugFeatureEnabled = (feature: keyof typeof DEBUG_CONFIG.features): boolean => {
  return DEBUG_CONFIG.features[feature] ?? false;
};

/**
 * Conditionally log debug information
 */
export const debugLog = (message: string, data?: any): void => {
  if (DEBUG_CONFIG.features.aiDebugConsole) {
    console.log(`[DEBUG] ${message}`, data);
  }
};

/**
 * Conditionally log AI debug information
 */
export const aiDebugLog = (message: string, data?: any): void => {
  if (DEBUG_CONFIG.features.aiDebugConsole) {
    console.log(`[AI DEBUG] ${message}`, data);
  }
};
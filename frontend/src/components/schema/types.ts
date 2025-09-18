export interface FieldConfig {
  type?: string;
  description?: string;
  required?: boolean;
  confidence_score?: number;
  legibility?: "high" | "medium" | "low";
  extraction_hints?: string[];
  positioning_hints?: string[];
  validation_pattern?: string;
  potential_issues?: string[];
}

export interface GeneratedSchema {
  id: string;
  name: string;
  description?: string;
  category?: string;
  fields: Record<string, FieldConfig>;
  total_fields: number;
  generation_confidence: number;
  production_ready: boolean;
  validation_status: string;
  user_review_status: string;
  overall_confidence: number;
  document_quality: string;
  extraction_difficulty: string;
  document_specific_notes: string[];
  quality_recommendations: string[];
}
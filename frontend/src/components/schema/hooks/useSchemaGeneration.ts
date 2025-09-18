import { useState, useEffect, useCallback } from "react";
import { GeneratedSchema } from "../types";
import { AIDebugInfo } from "@/types";
import { apiClient } from "@/lib/api";
import { aiDebugLog } from "@/lib/debug";

interface MinimalModel {
  id: string;
  name: string;
}

export function useSchemaGeneration() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [documentPreview, setDocumentPreview] = useState<string | null>(null);
  const [availableModels, setAvailableModels] = useState<MinimalModel[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedSchema, setGeneratedSchema] =
    useState<GeneratedSchema | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aiDebugInfo, setAiDebugInfo] = useState<AIDebugInfo | null>(null);

  // Handle file selection and preview
  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setDocumentPreview(url);
      return () => {
        URL.revokeObjectURL(url);
        setDocumentPreview(null);
      };
    } else {
      setDocumentPreview(null);
    }
  }, [selectedFile]);

  const resetGeneration = useCallback(() => {
    setGeneratedSchema(null);
    setError(null);
    setIsGenerating(false);
  }, []);

  const startGeneration = useCallback(async () => {
    if (!selectedFile || !selectedModel) return;

    try {
      setError(null);
      resetGeneration();
      setIsGenerating(true);

      const response = await apiClient.generateSchema({
        file: selectedFile,
        model: selectedModel || undefined,
      });

      if (
        response.success &&
        response.generated_schema?.is_valid &&
        response.generated_schema?.schema_data
      ) {
        const schemaData = response.generated_schema.schema_data;

        // Normalize field confidence scores from percentages to decimals
        const normalizedFields = Object.entries(schemaData.fields || {}).reduce(
          (acc, [key, field]) => {
            acc[key] = {
              ...field,
              confidence_score:
                field.confidence_score !== undefined
                  ? field.confidence_score / 100
                  : field.confidence_score,
            };
            return acc;
          },
          {} as Record<string, any>
        );

        setGeneratedSchema({
          id: schemaData.id,
          name: schemaData.name,
          description: schemaData.description,
          category: schemaData.category,
          fields: normalizedFields,
          total_fields: Object.keys(schemaData.fields || {}).length,
          generation_confidence: (schemaData.overall_confidence || 75) / 100,
          production_ready: response.generated_schema.ready_for_extraction,
          validation_status: "valid",
          user_review_status: "pending",
          overall_confidence: (schemaData.overall_confidence || 75) / 100,
          document_quality: schemaData.document_quality || "medium",
          extraction_difficulty: schemaData.extraction_difficulty || "medium",
          document_specific_notes: schemaData.document_specific_notes || [],
          quality_recommendations: [],
        });
        setAiDebugInfo(response.ai_debug || null);

        // Debug: Log the AI debug info to console for debugging (only in debug mode)
        if (response.ai_debug) {
          aiDebugLog("AI Debug Info received:", response.ai_debug);
          aiDebugLog("AI Debug Steps:", response.ai_debug.steps);
        }
      } else {
        throw new Error("Failed to generate schema");
      }
    } catch (error) {
      console.error("Generation error:", error);
      setError(
        error instanceof Error
          ? error.message
          : "An error occurred during generation"
      );
    } finally {
      setIsGenerating(false);
    }
  }, [selectedFile, selectedModel, resetGeneration]);

  return {
    // State
    selectedFile,
    selectedModel,
    documentPreview,
    availableModels,
    isGenerating,
    generatedSchema,
    error,
    aiDebugInfo,

    // Actions
    setSelectedFile,
    setSelectedModel,
    setAvailableModels,
    setGeneratedSchema,
    startGeneration,
    resetGeneration,
  };
}

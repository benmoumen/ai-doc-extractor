"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import {
  FileText,
  // Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  // ArrowRight,
  RefreshCw,
  Sparkles,
  Zap,
  Eye,
  Code,
  Settings,
  // X,
  ExternalLink,
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";

import { DocumentUpload } from "@/components/document-upload/document-upload";
import { SchemaSelector } from "./schema-selector";
import { ExtractionResults, type ExtractionResult } from "./extraction-results";
import { apiClient } from "@/lib/api";

// Minimal interfaces to avoid `any` while reflecting the structure we access
interface AIMessageContent {
  type: "text" | "image_url" | string;
  text?: string;
  image_url?: string | { url: string };
}

interface AIMessage {
  role: string;
  content?: AIMessageContent[];
}

interface DebugInfo {
  completion_params?: {
    model?: string;
    temperature?: number;
    messages?: AIMessage[];
  };
  raw_response?: {
    id?: string;
    model?: string;
    choices?: Array<{
      finish_reason?: string;
      message?: { content?: string };
    }>;
    usage?: Record<string, unknown>;
  };
}

interface SelectedSchemaDetails {
  fields?: Record<string, { display_name?: string; required?: boolean }>;
}

interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  status: "pending" | "active" | "completed" | "error";
  progress?: number;
}

// Schema Details Dialog Component
function SchemaDetailsDialog({
  schemaId,
  basicSchema,
  fetchSchemaDetails,
}: {
  schemaId: string;
  basicSchema: {
    id: string;
    name?: string;
    display_name?: string;
    description?: string;
    category?: string;
  };
  fetchSchemaDetails: (id: string) => Promise<{
    id: string;
    name: string;
    description: string;
    category?: string;
    fields: Record<
      string,
      {
        type: string;
        required: boolean;
        description: string;
        validation_pattern?: string;
        extraction_hints?: string[];
        display_name?: string;
      }
    >;
  } | null>;
}) {
  const [detailedSchema, setDetailedSchema] = useState<{
    id: string;
    name: string;
    description: string;
    category?: string;
    fields: Record<
      string,
      {
        type: string;
        required: boolean;
        description: string;
        validation_pattern?: string;
        extraction_hints?: string[];
        display_name?: string;
      }
    >;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const loadSchemaDetails = async () => {
    if (detailedSchema) return; // Already loaded

    setIsLoading(true);
    try {
      const details = await fetchSchemaDetails(schemaId);
      setDetailedSchema(details);
    } catch (error) {
      console.error("Failed to load schema details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
    if (open && !detailedSchema && !isLoading) {
      loadSchemaDetails();
    }
  };

  const schema = detailedSchema || basicSchema;
  const schemaName =
    schema?.name ||
    (schema as { display_name?: string })?.display_name ||
    "Schema";
  const schemaDescription = schema?.description || "";
  const schemaCategory = schema?.category || "";

  // Type guards for accessing optional properties
  const hasFieldCount = schema && "field_count" in schema;
  const fieldCount = hasFieldCount
    ? (schema as unknown as { field_count: number }).field_count
    : null;

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full">
          <Database className="h-4 w-4 mr-2" />
          View Schema
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Schema Details</DialogTitle>
          <DialogDescription>
            {schemaName} - Structure and field definitions
          </DialogDescription>
        </DialogHeader>
        <div className="max-h-[60vh] overflow-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Loading schema details...</span>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Schema Overview */}
              <div>
                <h4 className="text-sm font-medium mb-2">Schema Overview</h4>
                <div className="bg-muted p-3 rounded-md text-xs space-y-1">
                  <p>
                    <strong>ID:</strong> {schema?.id}
                  </p>
                  <p>
                    <strong>Name:</strong> {schemaName}
                  </p>
                  {schemaDescription && (
                    <p>
                      <strong>Description:</strong> {schemaDescription}
                    </p>
                  )}
                  {schemaCategory && (
                    <p>
                      <strong>Category:</strong> {schemaCategory}
                    </p>
                  )}
                  {fieldCount && (
                    <p>
                      <strong>Field Count:</strong> {fieldCount}
                    </p>
                  )}
                </div>
              </div>

              {/* Schema Fields */}
              {(() => {
                // Safely access fields from either detailed or basic schema
                const hasFields = schema && "fields" in schema;
                const hasFieldDefinitions =
                  schema && "field_definitions" in schema;
                const fields = hasFields
                  ? (schema as unknown as { fields: Record<string, unknown> })
                      .fields
                  : hasFieldDefinitions
                  ? (
                      schema as unknown as {
                        field_definitions: Record<string, unknown>;
                      }
                    ).field_definitions
                  : {};
                const hasFieldData = fields && Object.keys(fields).length > 0;

                return hasFieldData ? (
                  <div>
                    <h4 className="text-sm font-medium mb-2">
                      Field Definitions ({Object.keys(fields).length} fields)
                    </h4>
                    <div className="space-y-2">
                      {Object.entries(fields).map(([fieldName, fieldDef]) => {
                        // Type assertion for field definition
                        const typedFieldDef = fieldDef as {
                          type?: string;
                          required?: boolean;
                          description?: string;
                          validation_pattern?: string;
                          extraction_hints?: string[];
                          display_name?: string;
                        };
                        return (
                          <div
                            key={fieldName}
                            className="border rounded-lg p-3 space-y-2"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-sm">
                                {typedFieldDef?.display_name ||
                                  (typedFieldDef as { displayName?: string })
                                    ?.displayName ||
                                  fieldName}
                              </span>
                              <div className="flex gap-1">
                                <Badge variant="outline" className="text-xs">
                                  {typedFieldDef?.type || "text"}
                                </Badge>
                                <Badge
                                  variant={
                                    typedFieldDef?.required
                                      ? "destructive"
                                      : "secondary"
                                  }
                                  className="text-xs"
                                >
                                  {typedFieldDef?.required
                                    ? "Required"
                                    : "Optional"}
                                </Badge>
                              </div>
                            </div>
                            {typedFieldDef?.description && (
                              <p className="text-xs text-muted-foreground">
                                {typedFieldDef.description}
                              </p>
                            )}
                            {typedFieldDef?.validation_pattern && (
                              <div className="text-xs">
                                <span className="font-medium text-purple-600">
                                  Pattern:
                                </span>
                                <code className="ml-1 bg-purple-50 px-1 py-0.5 rounded">
                                  {typedFieldDef.validation_pattern}
                                </code>
                              </div>
                            )}
                            {typedFieldDef?.extraction_hints &&
                              typedFieldDef.extraction_hints.length > 0 && (
                                <div className="text-xs">
                                  <span className="font-medium text-blue-600">
                                    Hints:
                                  </span>
                                  <ul className="ml-2 mt-1 space-y-0.5">
                                    {typedFieldDef.extraction_hints!.map(
                                      (hint: string, index: number) => (
                                        <li
                                          key={index}
                                          className="text-blue-600"
                                        >
                                          • {hint}
                                        </li>
                                      )
                                    )}
                                  </ul>
                                </div>
                              )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div>
                    <h4 className="text-sm font-medium mb-2">
                      Field Definitions
                    </h4>
                    <div className="bg-muted p-3 rounded-md text-xs text-muted-foreground">
                      <p>No field definitions found in this schema.</p>
                      <p className="mt-1">
                        {isLoading
                          ? "Loading detailed schema information..."
                          : "This may be a simple schema or the field definitions might be stored in a different format."}
                      </p>
                    </div>
                  </div>
                );
              })()}

              {/* Raw JSON View */}
              <div>
                <h4 className="text-sm font-medium mb-2">Raw Schema JSON</h4>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-[300px]">
                  <code>{JSON.stringify(schema, null, 2)}</code>
                </pre>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function ExtractionWorkflow() {
  const [currentStep, setCurrentStep] = useState<
    "upload" | "configure" | "extract" | "results"
  >("upload");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  type MinimalModel = {
    id: string;
    name: string;
    provider?: string;
    model?: string;
  };
  const [availableModels, setAvailableModels] = useState<MinimalModel[]>([]);
  const [useAI, setUseAI] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [extractionResult, setExtractionResult] =
    useState<ExtractionResult | null>(null);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [availableSchemas, setAvailableSchemas] = useState<
    Record<
      string,
      {
        id: string;
        name?: string;
        display_name?: string;
        description?: string;
        category?: string;
        fields?: Record<string, unknown>;
        field_definitions?: Record<string, unknown>;
      }
    >
  >({});
  const [detailedSchemas, setDetailedSchemas] = useState<
    Record<
      string,
      {
        id: string;
        name: string;
        description: string;
        category?: string;
        fields: Record<
          string,
          {
            type: string;
            required: boolean;
            description: string;
            validation_pattern?: string;
            extraction_hints?: string[];
            display_name?: string;
          }
        >;
      }
    >
  >({});
  const [selectedSchemaDetails, setSelectedSchemaDetails] =
    useState<SelectedSchemaDetails | null>(null);
  const [documentPreview, setDocumentPreview] = useState<string | null>(null);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);

  // Load available models on component mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await apiClient.getSupportedModels();
        if (response.success && response.models) {
          setAvailableModels(response.models as MinimalModel[]);
          // Set default model to first available
          if (response.models.length > 0) {
            setSelectedModel(response.models[0].id);
          }
        }
      } catch (error) {
        console.error("Failed to load models:", error);
      }
    };
    loadModels();
  }, []);

  // Load available schemas
  useEffect(() => {
    const loadSchemas = async () => {
      try {
        const response = await apiClient.getAvailableSchemas();
        if (response.success && response.schemas) {
          setAvailableSchemas(
            response.schemas as Record<
              string,
              {
                id: string;
                name?: string;
                display_name?: string;
                description?: string;
                category?: string;
              }
            >
          );
        }
      } catch (error) {
        console.error("Failed to load schemas:", error);
      }
    };
    loadSchemas();
  }, []);

  // Function to fetch detailed schema information
  const fetchSchemaDetails = async (schemaId: string) => {
    if (detailedSchemas[schemaId]) {
      return detailedSchemas[schemaId]; // Return cached version
    }

    try {
      const response = await apiClient.getSchemaDetails(schemaId);
      if (response.success && response.schema) {
        // The backend returns the complete schema with fields property
        const schemaDetails = response.schema;
        setDetailedSchemas((prev) => ({
          ...prev,
          [schemaId]: schemaDetails,
        }));
        return schemaDetails;
      }
    } catch (error) {
      console.error("Failed to load schema details:", error);
    }
    return null;
  };

  // Create document preview when file is uploaded
  useEffect(() => {
    if (uploadedFile) {
      if (
        uploadedFile.type.startsWith("image/") ||
        uploadedFile.type === "application/pdf"
      ) {
        const url = URL.createObjectURL(uploadedFile);
        setDocumentPreview(url);
        return () => URL.revokeObjectURL(url);
      }
    }
  }, [uploadedFile]);

  // Fetch detailed schema information when schema is selected
  useEffect(() => {
    if (selectedSchema && selectedSchema !== "ai") {
      const loadSchemaDetails = async () => {
        try {
          const details = await apiClient.getSchemaDetails(selectedSchema);
          if (details.success && details.schema) {
            setSelectedSchemaDetails(details.schema as SelectedSchemaDetails);
          }
        } catch (error) {
          console.error("Failed to load schema details:", error);
          setSelectedSchemaDetails(null);
        }
      };
      loadSchemaDetails();
    } else {
      setSelectedSchemaDetails(null);
    }
  }, [selectedSchema]);

  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    {
      id: "upload",
      name: "Upload Document",
      description: "Select and upload your document",
      status: "pending",
    },
    {
      id: "configure",
      name: "Configure Extraction",
      description: "Choose extraction method",
      status: "pending",
    },
    {
      id: "extract",
      name: "Extract Data",
      description: "AI processing your document",
      status: "pending",
    },
    {
      id: "results",
      name: "Review & Export",
      description: "Review and export results",
      status: "pending",
    },
  ]);

  const updateStepStatus = (
    stepId: string,
    status: WorkflowStep["status"],
    progress?: number
  ) => {
    setWorkflowSteps((prev) =>
      prev.map((step) =>
        step.id === stepId ? { ...step, status, progress } : step
      )
    );
  };

  const handleUploadStart = (file: File) => {
    setUploadedFile(file);
    setIsUploading(true);
    updateStepStatus("upload", "active");
  };

  const handleUploadComplete = (result: { success: boolean }) => {
    setIsUploading(false);
    if (result.success) {
      updateStepStatus("upload", "completed");
      updateStepStatus("configure", "active");
      setCurrentStep("configure");
      toast.success("Document uploaded successfully");
    } else {
      updateStepStatus("upload", "error");
      toast.error("Upload failed. Please try again.");
    }
  };

  const handleSchemaSelect = (schemaId: string | null, aiMode: boolean) => {
    setSelectedSchema(schemaId);
    setUseAI(aiMode);
  };

  const handleStartExtraction = async () => {
    if (!uploadedFile) return;

    setIsExtracting(true);
    updateStepStatus("configure", "completed");
    updateStepStatus("extract", "active");
    setCurrentStep("extract");
    setExtractionProgress(0);

    // Progress simulation for UI feedback
    const progressInterval = setInterval(() => {
      setExtractionProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      // Call real API for data extraction
      const startTime = Date.now();
      const result = await apiClient.extractData(
        uploadedFile,
        selectedSchema || undefined,
        useAI,
        selectedModel || undefined
      );
      const endTime = Date.now();
      const clientSideProcessingTime = (endTime - startTime) / 1000;

      clearInterval(progressInterval);
      setExtractionProgress(100);

      if (result.success) {
        // Store the debug information from this extraction
        if (result.debug) {
          setDebugInfo(result.debug as DebugInfo);
        }

        // Transform API response to match our component interface
        // Our backend returns: { success, extracted_data, validation, metadata }
        // Normalize extraction mode values from backend -> UI
        const modeRaw = result.metadata?.extraction_mode;
        const normalizedMode: "schema" | "ai" =
          modeRaw === "schema_guided"
            ? "schema"
            : modeRaw === "freeform"
            ? "ai"
            : selectedSchema
            ? "schema"
            : "ai";

        // Get confidence scores from the response (optional fields from backend)
        type ExtendedExtractedData = typeof result.extracted_data & {
          field_confidence?: Record<string, number>;
          overall_confidence?: number;
        };
        const ed = (result.extracted_data || {}) as ExtendedExtractedData;
        const fieldConfidence: Record<string, number> =
          ed.field_confidence ?? {};
        const overallConfidence =
          ed.overall_confidence ?? result.metadata?.overall_confidence ?? 75;

        // Get document verification data
        const documentVerification = result.document_verification || {};

        const extractionResult: ExtractionResult = {
          id: `extraction_${Date.now()}`,
          documentType: result.metadata?.file_type || "document",
          extractionMode: normalizedMode,
          schemaUsed: result.metadata?.schema_id ?? selectedSchema ?? undefined,
          processingTime:
            result.metadata?.processing_time || clientSideProcessingTime,
          confidence: overallConfidence, // Keep original scale (0-100)
          extractedFields: result.extracted_data?.structured_data
            ? Object.entries(result.extracted_data.structured_data).map(
                ([key, value]) => ({
                  id: key,
                  name: key,
                  displayName: key
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (l) => l.toUpperCase()),
                  // Preserve structured values for arrays/objects; stringify primitives safely
                  value:
                    Array.isArray(value) ||
                    (value !== null && typeof value === "object")
                      ? value
                      : value != null
                      ? String(value)
                      : "",
                  // Infer accurate type including objects
                  type: Array.isArray(value)
                    ? "array"
                    : value !== null && typeof value === "object"
                    ? "object"
                    : typeof value === "number"
                    ? "number"
                    : typeof value === "boolean"
                    ? "boolean"
                    : "string",
                  // Use actual field confidence if available, otherwise use overall confidence
                  confidence:
                    fieldConfidence[key] !== undefined
                      ? fieldConfidence[key] // Keep original scale (0-100), including 0
                      : overallConfidence,
                  validation: {
                    isValid: result.validation?.passed ?? true,
                    errors: result.validation?.errors || [],
                  },
                })
              )
            : [
                {
                  id: "raw_content",
                  name: "raw_content",
                  displayName: "Extracted Content",
                  value:
                    result.extracted_data?.formatted_text ||
                    result.extracted_data?.raw_content ||
                    "No content extracted",
                  type: "string",
                  confidence: overallConfidence, // Use overall confidence for raw content
                  validation: {
                    isValid: result.validation?.passed ?? true,
                    errors: result.validation?.errors || [],
                  },
                },
              ],
          warnings:
            result.validation?.errors?.map(
              (error: string) => `Validation warning: ${error}`
            ) || [],
          verification: documentVerification,
          suggestions: (() => {
            const suggestions = [];
            const docQuality =
              result.extracted_data?.document_quality ||
              result.metadata?.document_quality;

            // Add verification-based suggestions
            const riskLevel = documentVerification.risk_level;
            const authenticityScore = documentVerification.authenticity_score;

            if (riskLevel === "high") {
              suggestions.push(
                "⚠️ HIGH RISK: Significant authenticity concerns detected. Manual verification required before processing."
              );
            } else if (riskLevel === "medium") {
              suggestions.push(
                "⚠️ MEDIUM RISK: Some authenticity concerns detected. Recommend manual review."
              );
            }

            if (authenticityScore && authenticityScore < 60) {
              suggestions.push(
                `Document authenticity score is ${authenticityScore}%. Consider additional verification steps.`
              );
            }

            // Check for tampering indicators
            const tampering = documentVerification.tampering_indicators;
            if (tampering) {
              const issues = [];
              if (tampering.photo_manipulation)
                issues.push("photo manipulation");
              if (tampering.text_alterations) issues.push("text alterations");
              if (tampering.structural_anomalies)
                issues.push("structural anomalies");
              if (tampering.digital_artifacts) issues.push("digital artifacts");
              if (tampering.font_inconsistencies)
                issues.push("font inconsistencies");

              if (issues.length > 0) {
                suggestions.push(
                  `Potential tampering detected: ${issues.join(
                    ", "
                  )}. Document requires careful review.`
                );
              }
            }

            // Document type mismatch
            if (
              documentVerification.expected_document_type &&
              documentVerification.detected_document_type &&
              documentVerification.expected_document_type !==
                documentVerification.detected_document_type
            ) {
              suggestions.push(
                `Document type mismatch: Expected ${documentVerification.expected_document_type}, but detected ${documentVerification.detected_document_type}.`
              );
            }

            // Add suggestions based on document quality
            if (docQuality === "low") {
              suggestions.push(
                "Document quality is low. Consider uploading a higher resolution image for better extraction accuracy."
              );
            }

            // Add suggestions based on confidence levels
            if (overallConfidence < 50) {
              suggestions.push(
                "Overall extraction confidence is low. Manual review of all fields is strongly recommended."
              );
            } else if (overallConfidence < 70) {
              suggestions.push(
                "Some fields have low confidence scores. Please review highlighted fields carefully."
              );
            }

            // Check for fields with very low confidence
            const lowConfidenceFields = Object.entries(fieldConfidence)
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              .filter(([_, conf]) => conf < 50)
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              .map(([field, _]) => field);

            if (lowConfidenceFields.length > 0) {
              suggestions.push(
                `Fields with low confidence: ${lowConfidenceFields.join(
                  ", "
                )}. These may require manual correction.`
              );
            }

            return suggestions;
          })(),
        };

        setExtractionResult(extractionResult);
        updateStepStatus("extract", "completed");
        updateStepStatus("results", "active");
        setCurrentStep("results");
        toast.success("Extraction completed successfully!");
      } else {
        throw new Error(result.error || "Extraction failed");
      }
    } catch (error) {
      console.error("Extraction error:", error);
      clearInterval(progressInterval);
      updateStepStatus("extract", "error");

      const errorMessage =
        error instanceof Error
          ? error.message
          : "Extraction failed. Please try again.";
      toast.error(errorMessage);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleFieldUpdate = (fieldId: string, newValue: unknown) => {
    if (!extractionResult) return;

    setExtractionResult({
      ...extractionResult,
      extractedFields: extractionResult.extractedFields.map((field) =>
        field.id === fieldId ? { ...field, value: newValue } : field
      ),
    });
  };

  const handleExport = () => {
    if (!extractionResult) return;

    // Export the complete extraction result object as JSON
    const blob = new Blob([JSON.stringify(extractionResult, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extraction-${extractionResult.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Extraction data exported as JSON");
  };

  const handleReset = () => {
    setCurrentStep("upload");
    setUploadedFile(null);
    setSelectedSchema(null);
    setUseAI(false);
    setExtractionResult(null);
    setExtractionProgress(0);
    setDocumentPreview(null);
    setDebugInfo(null);
    setIsUploading(false);
    setWorkflowSteps((prev) =>
      prev.map((step) => ({
        ...step,
        status: step.id === "upload" ? "pending" : "pending",
        progress: undefined,
      }))
    );
  };

  return (
    <div className="space-y-6">
      {/* Workflow Progress */}
      <Card>
        <CardContent className="pt-6">
          {/* Circles + Dividers Row using 7-column grid: C | D | C | D | C | D | C */}
          <div className="grid grid-cols-7 items-center">
            {workflowSteps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="col-span-1 flex justify-center">
                  <div
                    className={`
                    w-10 h-10 rounded-full flex items-center justify-center
                    ${
                      step.status === "completed"
                        ? "bg-green-500 text-white"
                        : step.status === "active"
                        ? "bg-blue-200 text-white"
                        : step.status === "error"
                        ? "bg-red-500 text-white"
                        : "bg-gray-200 text-gray-400"
                    }
                  `}
                  >
                    {step.status === "completed" ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : step.status === "error" ? (
                      <AlertCircle className="h-5 w-5" />
                    ) : step.status === "active" &&
                      ((step.id === "upload" && isUploading) ||
                        (step.id === "extract" && isExtracting)) ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : step.status === "active" ? (
                      <div className="w-3 h-3 rounded-full bg-blue-400" />
                    ) : (
                      <div className="w-3 h-3 rounded-full bg-gray-400" />
                    )}
                  </div>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div
                    className={`col-span-1 h-0.5 mx-2 ${
                      workflowSteps[index].status === "completed"
                        ? "bg-green-500"
                        : workflowSteps[index + 1].status !== "pending"
                        ? "bg-blue-500"
                        : "bg-gray-200"
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Labels Row aligned under the exact same grid columns as circles */}
          <div className="mt-3 grid grid-cols-7 items-start">
            {workflowSteps.map((step, index) => (
              <React.Fragment key={`${step.id}-labels`}>
                <div className="col-span-1 text-center">
                  <p className="text-xs font-medium">{step.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {step.description}
                  </p>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className="col-span-1" />
                )}
              </React.Fragment>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Content Area */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Step */}
          {currentStep === "upload" && (
            <DocumentUpload
              onUploadComplete={handleUploadComplete}
              onUploadStart={handleUploadStart}
            />
          )}

          {/* Configure Step */}
          {currentStep === "configure" && uploadedFile && (
            <Card>
              <CardHeader>
                <CardTitle>Configure Extraction</CardTitle>
                <CardDescription>
                  Choose how you want to extract data from {uploadedFile.name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <SchemaSelector
                  schemas={Object.values(availableSchemas).map((schema) => ({
                    id: schema.id,
                    name: schema.name ?? schema.display_name ?? "Untitled",
                    description: schema.description ?? "",
                    category: schema.category ?? "Other",
                  }))}
                  onSchemaSelect={handleSchemaSelect}
                />

                <Separator />

                {/* Model Selection */}
                <div className="space-y-3">
                  <label className="text-sm font-medium">AI Model</label>
                  <div className="grid grid-cols-1 gap-2">
                    {availableModels.map((model) => (
                      <div
                        key={model.id}
                        className={`
                          p-3 rounded-lg border cursor-pointer transition-colors
                          ${
                            selectedModel === model.id
                              ? "border-blue-200 bg-blue-50"
                              : "border-gray-200 hover:border-gray-300"
                          }
                        `}
                        onClick={() => setSelectedModel(model.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">{model.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {model.provider} • {model.model}
                            </p>
                          </div>
                          <div
                            className={`
                            w-4 h-4 rounded-full border-2
                            ${
                              selectedModel === model.id
                                ? "bg-blue-500 border-blue-500"
                                : "border-gray-300"
                            }
                          `}
                          >
                            {selectedModel === model.id && (
                              <div className="w-full h-full bg-white rounded-full scale-50" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Ready to extract</p>
                    <p className="text-xs text-muted-foreground">
                      {selectedSchema
                        ? `Schema-guided extraction: ${selectedSchema}`
                        : useAI
                        ? "AI Free-form Discovery: automatic field detection without schema constraints"
                        : "Please select a schema or enable AI Free-form Discovery mode"}
                    </p>
                  </div>
                  <Button
                    onClick={handleStartExtraction}
                    disabled={!useAI && !selectedSchema}
                  >
                    <Zap className="h-4 w-4 mr-2" />
                    Start Extraction
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Extract Step */}
          {currentStep === "extract" && (
            <Card>
              <CardHeader>
                <CardTitle>Extracting Data</CardTitle>
                <CardDescription>
                  AI is processing your document...
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Processing document...</span>
                    <span>{extractionProgress}%</span>
                  </div>
                  <Progress value={extractionProgress} className="h-2" />
                </div>

                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                    <Sparkles className="h-5 w-5 text-blue-500 animate-pulse" />
                    <div>
                      <p className="text-sm font-medium">
                        AI Analysis in Progress
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Detecting document type and extracting fields...
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Results Step */}
          {currentStep === "results" && extractionResult && (
            <ExtractionResults
              result={extractionResult}
              onFieldUpdate={handleFieldUpdate}
              onExport={handleExport}
            />
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Document Info */}
          {uploadedFile && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Document Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start gap-3">
                  <FileText className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium break-all">
                      {uploadedFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {/* Document Preview Button */}
                {uploadedFile && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="h-4 w-4 mr-2" />
                        View Document
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>Document Preview</DialogTitle>
                        <DialogDescription>
                          {uploadedFile.name}
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        {uploadedFile.type === "application/pdf" ? (
                          <div className="space-y-4">
                            <embed
                              src={documentPreview || ""}
                              type="application/pdf"
                              className="w-full h-[50vh]"
                            />
                            <div className="text-center">
                              <p className="text-sm text-muted-foreground mb-2">
                                PDF not displaying? Open in new tab:
                              </p>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  window.open(documentPreview || "", "_blank")
                                }
                              >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                Open PDF in New Tab
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Image
                            src={documentPreview || ""}
                            alt="Document preview"
                            width={1200}
                            height={800}
                            className="w-full h-auto"
                            unoptimized
                          />
                        )}
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {/* AI Debug Info Viewer Button */}
                {extractionResult && debugInfo && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Code className="h-4 w-4 mr-2" />
                        View AI Debug Info
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-6xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>AI Debug Information</DialogTitle>
                        <DialogDescription>
                          Completion parameters and raw response from AI model
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        <Tabs defaultValue="params" className="w-full">
                          <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="params">
                              Completion Parameters
                            </TabsTrigger>
                            <TabsTrigger value="response">
                              Raw AI Response
                            </TabsTrigger>
                          </TabsList>
                          <TabsContent value="params" className="space-y-4">
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                Model & Settings
                              </h4>
                              <div className="bg-muted p-3 rounded-md text-xs space-y-2">
                                <div>
                                  <strong>Model:</strong>{" "}
                                  {debugInfo.completion_params?.model ||
                                    "Unknown"}
                                </div>
                                <div>
                                  <strong>Temperature:</strong>{" "}
                                  {debugInfo.completion_params?.temperature ??
                                    "Not set"}
                                </div>
                              </div>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                Messages Sent to AI
                              </h4>
                              <div className="space-y-2">
                                {debugInfo.completion_params?.messages?.map(
                                  (message: AIMessage, index: number) => (
                                    <div
                                      key={index}
                                      className="bg-muted p-3 rounded-md"
                                    >
                                      <div className="text-xs font-medium mb-2">
                                        Message {index + 1} (Role:{" "}
                                        {message.role})
                                      </div>
                                      {message.content?.map(
                                        (
                                          content: AIMessageContent,
                                          contentIndex: number
                                        ) => (
                                          <div
                                            key={contentIndex}
                                            className="text-xs space-y-1"
                                          >
                                            {content.type === "text" && (
                                              <div>
                                                <strong>Text Prompt:</strong>
                                                <pre className="mt-1 whitespace-pre-wrap bg-background p-2 rounded border max-h-40 overflow-auto">
                                                  {content.text}
                                                </pre>
                                              </div>
                                            )}
                                            {content.type === "image_url" && (
                                              <div>
                                                <strong>Image:</strong> Document
                                                image (base64 encoded)
                                              </div>
                                            )}
                                          </div>
                                        )
                                      )}
                                    </div>
                                  )
                                )}
                              </div>
                            </div>
                          </TabsContent>
                          <TabsContent value="response" className="space-y-4">
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                Response Metadata
                              </h4>
                              <div className="bg-muted p-3 rounded-md text-xs space-y-2">
                                <div>
                                  <strong>Response ID:</strong>{" "}
                                  {debugInfo.raw_response?.id || "Not provided"}
                                </div>
                                <div>
                                  <strong>Model Used:</strong>{" "}
                                  {debugInfo.raw_response?.model || "Unknown"}
                                </div>
                                <div>
                                  <strong>Finish Reason:</strong>{" "}
                                  {debugInfo.raw_response?.choices?.[0]
                                    ?.finish_reason || "Not provided"}
                                </div>
                                {debugInfo.raw_response?.usage &&
                                  Object.keys(debugInfo.raw_response.usage)
                                    .length > 0 && (
                                    <div>
                                      <strong>Token Usage:</strong>
                                      <pre className="mt-1 text-xs bg-background p-2 rounded border">
                                        {JSON.stringify(
                                          debugInfo.raw_response.usage,
                                          null,
                                          2
                                        )}
                                      </pre>
                                    </div>
                                  )}
                              </div>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                Raw AI Response Content
                              </h4>
                              <pre className="text-xs bg-muted p-4 rounded-md whitespace-pre-wrap max-h-96 overflow-auto">
                                {debugInfo.raw_response?.choices?.[0]?.message
                                  ?.content || "No response content available"}
                              </pre>
                            </div>
                          </TabsContent>
                        </Tabs>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {/* Schema View Button */}
                {selectedSchema &&
                  selectedSchema !== "ai" &&
                  availableSchemas[selectedSchema] && (
                    <SchemaDetailsDialog
                      schemaId={selectedSchema}
                      basicSchema={availableSchemas[selectedSchema]}
                      fetchSchemaDetails={fetchSchemaDetails}
                    />
                  )}

                {/* Extraction Details Button */}
                {extractionResult && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Settings className="h-4 w-4 mr-2" />
                        View Extraction Details
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>Extraction Details</DialogTitle>
                        <DialogDescription>
                          Configuration and details for this extraction
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        <div className="space-y-6">
                          {/* Extraction Summary */}
                          <div>
                            <h4 className="text-sm font-medium mb-2">
                              Extraction Summary
                            </h4>
                            <div className="text-xs space-y-1 bg-muted p-3 rounded-md">
                              <p>
                                <strong>Mode:</strong>{" "}
                                {extractionResult.extractionMode === "ai"
                                  ? "AI Free-form Discovery"
                                  : "Schema-guided"}
                              </p>
                              <p>
                                <strong>Processing Time:</strong>{" "}
                                {extractionResult.processingTime?.toFixed(2)}s
                              </p>
                              <p>
                                <strong>Overall Confidence:</strong>{" "}
                                {Math.round(extractionResult.confidence || 0)}%
                              </p>
                              <p>
                                <strong>Fields Extracted:</strong>{" "}
                                {extractionResult.extractedFields.length}
                              </p>
                            </div>
                          </div>

                          {/* Schema Information */}
                          {selectedSchema && selectedSchema !== "ai" ? (
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                Schema Information
                              </h4>
                              <div className="bg-muted p-3 rounded-md text-xs">
                                <p>
                                  <strong>Schema Used:</strong> {selectedSchema}
                                </p>
                                <p className="mt-1 text-muted-foreground">
                                  This extraction used a predefined schema to
                                  guide field extraction and validation.
                                </p>
                                {selectedSchemaDetails &&
                                  selectedSchemaDetails.fields && (
                                    <div className="mt-3">
                                      <p className="text-muted-foreground mb-2">
                                        Schema Fields (
                                        {
                                          Object.keys(
                                            selectedSchemaDetails.fields
                                          ).length
                                        }
                                        ):
                                      </p>
                                      <div className="space-y-1 max-h-32 overflow-y-auto">
                                        {Object.entries(
                                          selectedSchemaDetails.fields
                                        ).map(
                                          ([fieldName, fieldDef]: [
                                            string,
                                            {
                                              display_name?: string;
                                              required?: boolean;
                                            }
                                          ]) => (
                                            <div
                                              key={fieldName}
                                              className="flex items-center gap-2"
                                            >
                                              <span className="text-xs">
                                                {fieldDef.display_name ||
                                                  fieldName}
                                              </span>
                                              <Badge
                                                variant={
                                                  fieldDef.required
                                                    ? "destructive"
                                                    : "outline"
                                                }
                                                className="text-xs px-1 py-0 h-4"
                                              >
                                                {fieldDef.required
                                                  ? "Required"
                                                  : "Optional"}
                                              </Badge>
                                            </div>
                                          )
                                        )}
                                      </div>
                                    </div>
                                  )}
                              </div>
                            </div>
                          ) : (
                            <div>
                              <h4 className="text-sm font-medium mb-2">
                                AI Free-form Discovery
                              </h4>
                              <div className="bg-muted p-3 rounded-md text-xs">
                                <p>
                                  This extraction used AI Free-form Discovery
                                  without a predefined schema.
                                </p>
                                <p className="mt-1 text-muted-foreground">
                                  The AI automatically identified and extracted
                                  fields based on document structure and
                                  content.
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {extractionResult && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Document Type
                        </span>
                        <Badge variant="outline">
                          {extractionResult.documentType}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Extraction Mode
                        </span>
                        <Badge
                          variant={
                            extractionResult.extractionMode === "schema"
                              ? "default"
                              : "secondary"
                          }
                        >
                          {extractionResult.extractionMode === "schema"
                            ? "Schema-guided"
                            : "AI Free-form Discovery"}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Fields Extracted
                        </span>
                        <span className="font-medium">
                          {extractionResult.extractedFields.length}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Confidence
                        </span>
                        <Badge variant="default">
                          {Math.round(extractionResult.confidence || 0)}%
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          Processing Time
                        </span>
                        <span className="font-medium">
                          {extractionResult.processingTime?.toFixed(2)}s
                        </span>
                      </div>
                    </div>
                  </>
                )}

                {/* Process Another Document Button */}
                {currentStep === "results" && (
                  <>
                    <Separator className="my-3" />
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={handleReset}
                    >
                      <RefreshCw className="h-4 w-4 mr-2" />
                      Process Another Document
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Extraction Guide */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Quick Start Guide</CardTitle>
              <CardDescription className="text-xs">
                Follow these steps to extract data from your documents
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Step 1 */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-950 flex items-center justify-center">
                    <span className="text-sm font-semibold text-blue-600 dark:text-blue-400">
                      1
                    </span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Upload Document</p>
                    <p className="text-xs text-muted-foreground">
                      Drag & drop or browse for PDF, JPEG, or PNG files
                    </p>
                  </div>
                </div>

                {/* Step 2 */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-950 flex items-center justify-center">
                    <span className="text-sm font-semibold text-purple-600 dark:text-purple-400">
                      2
                    </span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Extraction Mode</p>
                    <div className="space-y-1">
                      <p className="text-xs text-muted-foreground">
                        <span className="font-medium">• Schema Mode:</span>{" "}
                        Structured extraction with predefined fields &
                        validation rules (Recommended)
                      </p>
                      <p className="text-xs text-muted-foreground">
                        <span className="font-medium">
                          • AI Free-form Discovery:
                        </span>{" "}
                        AI explores and extracts all discoverable data without
                        constraints
                      </p>
                    </div>
                  </div>
                </div>

                {/* Step 3 */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-950 flex items-center justify-center">
                    <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                      3
                    </span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Process & Review</p>
                    <p className="text-xs text-muted-foreground">
                      AI extracts data, then review and edit as needed
                    </p>
                  </div>
                </div>

                {/* Step 4 */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-orange-100 dark:bg-orange-950 flex items-center justify-center">
                    <span className="text-sm font-semibold text-orange-600 dark:text-orange-400">
                      4
                    </span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium">Review & Export</p>
                    <p className="text-xs text-muted-foreground">
                      Review extracted data and export from the results table
                    </p>
                  </div>
                </div>

                <Separator className="my-3" />

                {/* Tips Section */}
                <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <Sparkles className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div className="space-y-1">
                      <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
                        Best Practices
                      </p>
                      <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-0.5">
                        <li>• Use high-quality scans for better accuracy</li>
                        <li>• Schema mode works best for structured forms</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Upload,
  FileText,
  Brain,
  Wand2,
  CheckCircle,
  AlertCircle,
  Loader2,
  Eye,
  Download,
  Edit2,
  Check,
  X,
  Plus,
  Trash2,
  Save,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api";

interface GenerationStep {
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  duration?: number;
  details?: any;
}

interface SchemaGenerationProps {
  onSchemaGenerated?: (schemaId: string) => void;
  className?: string;
}

export function SchemaGenerator({
  onSchemaGenerated,
  className,
}: SchemaGenerationProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [generationSteps, setGenerationSteps] = useState<GenerationStep[]>([
    { name: "Document Processing", status: "pending" },
    { name: "AI Schema Generation", status: "pending" },
    { name: "Schema Validation", status: "pending" },
  ]);
  const [generatedSchema, setGeneratedSchema] = useState<any>(null);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [documentPreview, setDocumentPreview] = useState<string | null>(null);

  // Edit mode states
  const [isEditMode, setIsEditMode] = useState(false);
  const [editingSchema, setEditingSchema] = useState<any>(null);

  // Save schema states
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Ref to scroll to results section
  const resultsRef = useRef<HTMLDivElement | null>(null);

  // Load available models on component mount
  useEffect(() => {
    loadModels();
  }, []);

  // Update document preview when file changes
  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setDocumentPreview(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setDocumentPreview(null);
    }
  }, [selectedFile]);

  // Scroll to results when a schema has been generated
  useEffect(() => {
    if (generatedSchema && !isGenerating) {
      // Wait for the UI to paint before scrolling
      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    }
  }, [generatedSchema, isGenerating]);

  const loadModels = async () => {
    try {
      const response = await apiClient.getSupportedModels();
      if (response.success && response.models) {
        setAvailableModels(response.models);
        // Set first model as default
        if (response.models.length > 0) {
          setSelectedModel(response.models[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to load models:", err);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      resetGeneration();
    }
  };

  const resetGeneration = () => {
    setIsGenerating(false);
    setGenerationProgress(0);
    setCurrentStep("");
    setGeneratedSchema(null);
    setAnalysisId(null);
    setGenerationSteps((steps) =>
      steps.map((step) => ({ ...step, status: "pending" }))
    );
  };

  const updateStepStatus = (
    stepName: string,
    status: GenerationStep["status"],
    details?: any,
    duration?: number
  ) => {
    setGenerationSteps((steps) =>
      steps.map((step) =>
        step.name === stepName ? { ...step, status, details, duration } : step
      )
    );
  };

  const startGeneration = async () => {
    if (!selectedFile) {
      setError("Please select a document to analyze");
      return;
    }

    setError(null);
    resetGeneration();
    setIsGenerating(true);
    setCurrentStep("Uploading document...");

    try {
      // Step 1: Process document
      updateStepStatus("Document Processing", "in_progress");
      setGenerationProgress(10);

      // Step 2: Generate schema with AI
      setCurrentStep("Analyzing document with AI...");
      updateStepStatus("Document Processing", "completed");
      updateStepStatus("AI Schema Generation", "in_progress");
      setGenerationProgress(30);

      const schemaResponse = await apiClient.generateSchema({
        file: selectedFile,
        model: selectedModel || undefined,
      });

      if (!schemaResponse.success) {
        throw new Error("Schema generation failed");
      }

      setGenerationProgress(70);
      updateStepStatus("AI Schema Generation", "completed");
      updateStepStatus("Schema Validation", "in_progress");
      setCurrentStep("Validating generated schema...");

      // Process the generated schema
      const generatedSchema = schemaResponse.generated_schema;

      if (generatedSchema.is_valid && generatedSchema.schema_data) {
        setGeneratedSchema({
          id: generatedSchema.schema_data.id,
          name: generatedSchema.schema_data.name,
          description: generatedSchema.schema_data.description,
          category: generatedSchema.schema_data.category,
          fields: generatedSchema.schema_data.fields, // Store the complete fields data
          total_fields: Object.keys(generatedSchema.schema_data.fields).length,
          generation_confidence: 0.85, // Default confidence since backend doesn't provide it yet
          production_ready: generatedSchema.ready_for_extraction,
          validation_status: "valid",
          user_review_status: "pending",
        });

        updateStepStatus("Schema Validation", "completed");
        setCurrentStep("Schema generation completed!");
        setGenerationProgress(100);

        if (onSchemaGenerated && generatedSchema.schema_id) {
          onSchemaGenerated(generatedSchema.schema_id);
        }
      } else {
        // Show more detailed error information
        console.error("Schema validation failed:", {
          is_valid: generatedSchema.is_valid,
          has_schema_data: !!generatedSchema.schema_data,
          raw_response_length: generatedSchema.raw_response?.length || 0,
          raw_response_preview:
            generatedSchema.raw_response?.substring(0, 200) + "...",
        });

        const errorMessage = !generatedSchema.is_valid
          ? "AI response could not be parsed as valid JSON schema"
          : "Generated schema missing required data fields";

        throw new Error(`${errorMessage}. Check console for raw AI response.`);
      }
    } catch (err: any) {
      console.error("Generation failed:", err);
      setError(err.message || "Schema generation failed");
      setCurrentStep("Generation failed");

      // Mark current step as failed
      const currentStepName = generationSteps.find(
        (step) => step.status === "in_progress"
      )?.name;
      if (currentStepName) {
        updateStepStatus(currentStepName, "failed");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const getStepIcon = (status: GenerationStep["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case "in_progress":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return (
          <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
        );
    }
  };

  // Edit mode functions
  const startEditMode = () => {
    setIsEditMode(true);
    setEditingSchema(JSON.parse(JSON.stringify(generatedSchema))); // Deep copy
  };

  const saveChanges = () => {
    setGeneratedSchema(editingSchema);
    setIsEditMode(false);
    // Here you could also send the updated schema to the backend
  };

  const cancelEdit = () => {
    setEditingSchema(null);
    setIsEditMode(false);
  };

  const updateSchemaField = (field: string, value: any) => {
    setEditingSchema({
      ...editingSchema,
      [field]: value,
    });
  };

  const updateFieldProperty = (
    fieldName: string,
    property: string,
    value: any
  ) => {
    setEditingSchema({
      ...editingSchema,
      fields: {
        ...editingSchema.fields,
        [fieldName]: {
          ...editingSchema.fields[fieldName],
          [property]: value,
        },
      },
    });
  };

  const deleteField = (fieldName: string) => {
    const updatedFields = { ...editingSchema.fields };
    delete updatedFields[fieldName];
    setEditingSchema({
      ...editingSchema,
      fields: updatedFields,
      total_fields: Object.keys(updatedFields).length,
    });
  };

  const addNewField = () => {
    const newFieldName = `new_field_${Date.now()}`;
    setEditingSchema({
      ...editingSchema,
      fields: {
        ...editingSchema.fields,
        [newFieldName]: {
          type: "text",
          required: false,
          description: "New field description",
        },
      },
      total_fields: Object.keys(editingSchema.fields).length + 1,
    });
  };

  const renameField = (oldName: string, newName: string) => {
    if (oldName === newName || !newName) return;

    // Preserve field order by recreating object in same order
    const updatedFields: Record<string, any> = {};
    Object.entries(editingSchema.fields).forEach(([key, value]) => {
      if (key === oldName) {
        updatedFields[newName] = value;
      } else {
        updatedFields[key] = value;
      }
    });

    setEditingSchema({
      ...editingSchema,
      fields: updatedFields,
    });
  };

  const downloadSchema = () => {
    const schemaToDownload = isEditMode ? editingSchema : generatedSchema;
    if (!schemaToDownload) return;

    const schemaData = {
      id: schemaToDownload.id,
      name: schemaToDownload.name,
      description: schemaToDownload.description,
      category: schemaToDownload.category,
      fields: schemaToDownload.fields,
      total_fields: schemaToDownload.total_fields,
      generated_at: new Date().toISOString(),
      confidence: schemaToDownload.generation_confidence,
      production_ready: schemaToDownload.production_ready,
    };

    const blob = new Blob([JSON.stringify(schemaData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `schema-${generatedSchema.name
      .toLowerCase()
      .replace(/\s+/g, "-")}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const saveSchemaForExtraction = async () => {
    const schemaToSave = isEditMode ? editingSchema : generatedSchema;
    if (!schemaToSave) return;

    setIsSaving(true);
    setSaveError(null);
    setSaveMessage(null);

    try {
      const schemaData = {
        id: schemaToSave.id,
        name: schemaToSave.name,
        description: schemaToSave.description || "",
        category: schemaToSave.category || "Government",
        fields: schemaToSave.fields,
      };

      const response = await apiClient.saveSchema(schemaData);

      if (response.success) {
        setSaveMessage(
          `Schema "${schemaToSave.name}" saved successfully! It's now available for data extraction.`
        );

        // Notify parent component that schema was saved
        if (onSchemaGenerated) {
          onSchemaGenerated(response.schema_id);
        }
      } else {
        throw new Error("Failed to save schema");
      }
    } catch (err: any) {
      console.error("Save schema error:", err);
      setSaveError(err.message || "Failed to save schema");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="h-6 w-6 text-purple-500" />
          AI Schema Generator
        </h2>
        <p className="text-muted-foreground">
          Upload a sample document to automatically generate a custom extraction
          schema using AI
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5" />
            Configuration
          </CardTitle>
          <CardDescription>
            Select your document and configure generation settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Upload */}
          <div className="space-y-2">
            <Label>Sample Document</Label>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <Label
                htmlFor="file-upload"
                className="flex items-center gap-2 px-4 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <Upload className="h-4 w-4" />
                Choose Document
              </Label>
              {selectedFile && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    <FileText className="h-3 w-3 mr-1" />
                    {selectedFile.name}
                  </Badge>
                  {documentPreview && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3 mr-1" />
                          Preview
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl max-h-[80vh]">
                        <DialogHeader>
                          <DialogTitle>Document Preview</DialogTitle>
                          <DialogDescription>
                            {selectedFile.name}
                          </DialogDescription>
                        </DialogHeader>
                        <div className="overflow-auto max-h-[60vh]">
                          {selectedFile.type === "application/pdf" ? (
                            <embed
                              src={documentPreview}
                              width="100%"
                              height="500px"
                              type="application/pdf"
                            />
                          ) : (
                            <img
                              src={documentPreview}
                              alt="Document preview"
                              className="max-w-full h-auto"
                            />
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Model Selection */}
          <div className="space-y-2">
            <Label>AI Model</Label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger>
                <SelectValue placeholder="Select AI model..." />
              </SelectTrigger>
              <SelectContent>
                {availableModels.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    {model.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Generate Button */}
          <Button
            onClick={startGeneration}
            disabled={!selectedFile || isGenerating}
            className="w-full"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating Schema...
              </>
            ) : (
              <>
                <Brain className="h-4 w-4 mr-2" />
                Generate Schema
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Progress Display */}
      {isGenerating && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Generation Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{currentStep}</span>
                <span>{generationProgress}%</span>
              </div>
              <Progress value={generationProgress} />
            </div>

            {/* Step Details */}
            <div className="space-y-2">
              {generationSteps.map((step, index) => (
                <div
                  key={step.name}
                  className="flex items-center gap-3 text-sm"
                >
                  {getStepIcon(step.status)}
                  <span
                    className={
                      step.status === "completed"
                        ? "text-green-600"
                        : step.status === "failed"
                        ? "text-red-600"
                        : ""
                    }
                  >
                    {step.name}
                  </span>
                  {step.duration && (
                    <span className="text-muted-foreground ml-auto">
                      {step.duration.toFixed(2)}s
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {generatedSchema && (
        <>
          {/* Anchor for smooth scrolling to results */}
          <div ref={resultsRef} />
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Generated Schema
              </CardTitle>
              <CardDescription>
                Your AI-generated schema is ready for use
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Header with Edit Controls */}
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium">Schema Details</h3>
                  {!isEditMode ? (
                    <Button onClick={startEditMode} variant="outline" size="sm">
                      <Edit2 className="h-4 w-4 mr-2" />
                      Edit Schema
                    </Button>
                  ) : (
                    <div className="flex gap-2">
                      <Button onClick={saveChanges} variant="default" size="sm">
                        <Check className="h-4 w-4 mr-2" />
                        Save Changes
                      </Button>
                      <Button onClick={cancelEdit} variant="outline" size="sm">
                        <X className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    </div>
                  )}
                </div>

                {/* Schema Basic Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Schema Name</Label>
                    {!isEditMode ? (
                      <p className="text-sm">{generatedSchema.name}</p>
                    ) : (
                      <Input
                        value={editingSchema.name}
                        onChange={(e) =>
                          updateSchemaField("name", e.target.value)
                        }
                        className="text-sm"
                      />
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Schema ID</Label>
                    {!isEditMode ? (
                      <p className="text-sm font-mono">{generatedSchema.id}</p>
                    ) : (
                      <Input
                        value={editingSchema.id}
                        onChange={(e) =>
                          updateSchemaField(
                            "id",
                            e.target.value
                              .toLowerCase()
                              .replace(/[^a-z0-9_]/g, "_")
                          )
                        }
                        className="text-sm font-mono"
                        placeholder="snake_case_id"
                      />
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Category</Label>
                    {!isEditMode ? (
                      <Badge variant="outline">
                        {generatedSchema.category || "Unknown"}
                      </Badge>
                    ) : (
                      <Select
                        value={editingSchema.category || "Government"}
                        onValueChange={(value) =>
                          updateSchemaField("category", value)
                        }
                      >
                        <SelectTrigger className="text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Government">Government</SelectItem>
                          <SelectItem value="Business">Business</SelectItem>
                          <SelectItem value="Personal">Personal</SelectItem>
                          <SelectItem value="Healthcare">Healthcare</SelectItem>
                          <SelectItem value="Education">Education</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Total Fields</Label>
                    <p className="text-sm">
                      {isEditMode
                        ? editingSchema.total_fields
                        : generatedSchema.total_fields}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Description</Label>
                  {!isEditMode ? (
                    <p className="text-sm text-muted-foreground">
                      {generatedSchema.description || "No description"}
                    </p>
                  ) : (
                    <Input
                      value={editingSchema.description || ""}
                      onChange={(e) =>
                        updateSchemaField("description", e.target.value)
                      }
                      className="text-sm"
                      placeholder="Enter schema description"
                    />
                  )}
                </div>

                <Separator />

                {/* Generation Confidence */}
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Generation Confidence
                  </Label>
                  <div className="flex items-center gap-2">
                    <Progress
                      value={generatedSchema.generation_confidence * 100}
                      className="flex-1"
                    />
                    <span className="text-sm">
                      {Math.round(generatedSchema.generation_confidence * 100)}%
                    </span>
                  </div>
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-xs">
                      {generatedSchema.generation_confidence >= 0.8
                        ? "High confidence - This schema is ready for production use."
                        : generatedSchema.generation_confidence >= 0.6
                        ? "Medium confidence - Review recommended before production use."
                        : "Low confidence - Manual review and adjustment required."}
                    </AlertDescription>
                  </Alert>
                </div>

                <Separator />

                {/* Schema Fields */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">
                      Generated Fields (
                      {isEditMode
                        ? editingSchema?.total_fields
                        : generatedSchema.total_fields}
                      )
                    </Label>
                    {isEditMode && (
                      <Button onClick={addNewField} variant="outline" size="sm">
                        <Plus className="h-4 w-4 mr-1" />
                        Add Field
                      </Button>
                    )}
                  </div>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {(isEditMode
                      ? editingSchema?.fields
                      : generatedSchema.fields) &&
                      Object.entries(
                        isEditMode ? editingSchema.fields : generatedSchema.fields
                      ).map(([fieldName, fieldConfig]: [string, any], index) => (
                        <div
                          key={`field-${index}`}
                          className="border rounded-lg p-3 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            {!isEditMode ? (
                              <span className="text-sm font-medium">
                                {fieldName}
                              </span>
                            ) : (
                              <Input
                                value={fieldName}
                                onChange={(e) =>
                                  renameField(fieldName, e.target.value)
                                }
                                className="text-sm font-medium w-48"
                                placeholder="field_name"
                              />
                            )}
                            <div className="flex gap-1">
                              {!isEditMode ? (
                                <>
                                  <Badge variant="outline" className="text-xs">
                                    {fieldConfig.type || "text"}
                                  </Badge>
                                  <Badge
                                    variant={
                                      fieldConfig.required
                                        ? "destructive"
                                        : "secondary"
                                    }
                                    className="text-xs"
                                  >
                                    {fieldConfig.required
                                      ? "Required"
                                      : "Optional"}
                                  </Badge>
                                </>
                              ) : (
                                <>
                                  <Select
                                    value={fieldConfig.type || "text"}
                                    onValueChange={(value) =>
                                      updateFieldProperty(
                                        fieldName,
                                        "type",
                                        value
                                      )
                                    }
                                  >
                                    <SelectTrigger className="w-24 h-7 text-xs">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="text">text</SelectItem>
                                      <SelectItem value="number">
                                        number
                                      </SelectItem>
                                      <SelectItem value="date">date</SelectItem>
                                      <SelectItem value="email">email</SelectItem>
                                      <SelectItem value="phone">phone</SelectItem>
                                      <SelectItem value="url">url</SelectItem>
                                      <SelectItem value="boolean">
                                        boolean
                                      </SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <Select
                                    value={
                                      fieldConfig.required
                                        ? "required"
                                        : "optional"
                                    }
                                    onValueChange={(value) =>
                                      updateFieldProperty(
                                        fieldName,
                                        "required",
                                        value === "required"
                                      )
                                    }
                                  >
                                    <SelectTrigger className="w-24 h-7 text-xs">
                                      <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="required">
                                        Required
                                      </SelectItem>
                                      <SelectItem value="optional">
                                        Optional
                                      </SelectItem>
                                    </SelectContent>
                                  </Select>
                                  <Button
                                    onClick={() => deleteField(fieldName)}
                                    variant="ghost"
                                    size="sm"
                                    className="h-7 px-2 text-destructive hover:text-destructive"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </>
                              )}
                            </div>
                          </div>
                          {!isEditMode ? (
                            fieldConfig.description && (
                              <p className="text-xs text-muted-foreground">
                                {fieldConfig.description}
                              </p>
                            )
                          ) : (
                            <Input
                              value={fieldConfig.description || ""}
                              onChange={(e) =>
                                updateFieldProperty(
                                  fieldName,
                                  "description",
                                  e.target.value
                                )
                              }
                              className="text-xs"
                              placeholder="Field description"
                            />
                          )}
                        </div>
                      ))}
                  </div>
                </div>

                <Separator />

                {/* Save/Success/Error Messages */}
                {saveMessage && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>{saveMessage}</AlertDescription>
                  </Alert>
                )}

                {saveError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{saveError}</AlertDescription>
                  </Alert>
                )}

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    onClick={saveSchemaForExtraction}
                    disabled={isSaving}
                    variant="default"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save for Extraction
                      </>
                    )}
                  </Button>
                  <Button onClick={downloadSchema} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

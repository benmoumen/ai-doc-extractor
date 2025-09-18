"use client";

import React, { useState, useEffect, useRef } from "react";
import { Brain, Plus, AlertCircle, X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { SchemaList } from "./SchemaList";
import { SchemaEditor } from "./SchemaEditor";
import { useSchemaManager } from "./hooks/useSchemaManager";
import { useSchemaGeneration } from "./hooks/useSchemaGeneration";
import { FieldConfig } from "./types";
import { SchemaGenerationForm } from "./components/SchemaGenerationForm";
import { toast } from "sonner";

interface SchemaManagerProps {
  onSchemaGenerated?: (schemaId: string) => void;
  className?: string;
}

type ViewMode = "list" | "edit" | "create" | "generate";

export function SchemaManager({
  onSchemaGenerated,
  className,
}: SchemaManagerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [showGeneration, setShowGeneration] = useState(false);

  const resultsRef = useRef<HTMLDivElement>(null);

  // Schema management
  const {
    schemas,
    activeSchema,
    isLoading,
    error,
    loadSchemas,
    loadSchema,
    createSchema,
    updateSchema,
    deleteSchema,
    setActiveSchema,
    clearError,
    isOperationInProgress,
  } = useSchemaManager();

  // Schema generation
  const {
    selectedFile,
    selectedModel,
    documentPreview,
    availableModels,
    isGenerating,
    generatedSchema,
    error: generationError,
    aiDebugInfo,
    setSelectedFile,
    setSelectedModel,
    setAvailableModels,
    startGeneration,
    resetGeneration,
  } = useSchemaGeneration();

  // Load schemas on mount
  useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  // Handle schema generation completion
  useEffect(() => {
    if (generatedSchema && !isGenerating) {
      setActiveSchema(generatedSchema);
      setViewMode("edit");

      // Scroll to results
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);

      if (onSchemaGenerated) {
        onSchemaGenerated(generatedSchema.id);
      }
    }
  }, [generatedSchema, isGenerating, setActiveSchema, onSchemaGenerated]);

  const handleEditSchema = async (schemaId: string) => {
    try {
      const schema = await loadSchema(schemaId);
      if (schema) {
        setViewMode("edit");
        // Scroll to editor
        setTimeout(() => {
          resultsRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }, 100);
      }
    } catch {
      toast.error("Failed to load schema");
    }
  };

  const handleSaveSchema = async (data: {
    name: string;
    description: string;
    category: string;
    fields: Record<string, FieldConfig>;
  }) => {
    try {
      // Check if this is a generated schema (came from AI generation)
      // Generated schemas have IDs but haven't been saved to database yet
      const isGeneratedSchema = activeSchema?.id && generatedSchema?.id === activeSchema.id;

      if (activeSchema?.id && !isGeneratedSchema) {
        // Update existing schema (exists in database)
        await updateSchema(activeSchema.id, data);
        toast.success("Schema updated successfully");
      } else {
        // Create new schema (either no ID or generated schema being saved for first time)
        await createSchema(data);
        toast.success("Schema saved successfully");
      }

      setViewMode("list");
      setActiveSchema(null);
      await loadSchemas(); // Refresh the list
    } catch (error) {
      toast.error("Failed to save schema");
      throw error; // Re-throw to keep loading state in editor
    }
  };

  const handleCancelEdit = () => {
    setViewMode("list");
    setActiveSchema(null);
  };

  const handleDeleteSchema = async (schemaId: string): Promise<void> => {
    await deleteSchema(schemaId);
  };

  const handleGeneration = async () => {
    setShowGeneration(true);
    await startGeneration();
  };

  const handleFileSelect = (file: File | null) => {
    setSelectedFile(file);
    if (file) {
      resetGeneration();
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header and Actions */}
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          {!showGeneration ? (
            <Button
              onClick={() => setShowGeneration(true)}
              disabled={isLoading}
              className="flex items-center gap-2 h-10 px-4"
            >
              <Sparkles className="h-4 w-4" />
              Generate with AI
            </Button>
          ) : (
            <Button
              variant="outline"
              onClick={() => setShowGeneration(false)}
              disabled={isLoading}
              className="flex items-center gap-2 h-10 px-4"
            >
              <X className="h-4 w-4" />
              Close Generator
            </Button>
          )}
          {!showGeneration && (
            <Button
              variant="outline"
              onClick={() => setViewMode("create")}
              disabled={isLoading || isOperationInProgress()}
              className="flex items-center gap-2 h-10 px-4"
            >
              <Plus className="h-4 w-4" />
              Create Manually
            </Button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            {error}
            <Button variant="ghost" size="sm" onClick={clearError}>
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {generationError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{generationError}</AlertDescription>
        </Alert>
      )}

      {/* AI Generation Section */}
      {showGeneration && (
        <div className="space-y-8">
          {/* Primary Generation Area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
              <SchemaGenerationForm
                selectedFile={selectedFile}
                selectedModel={selectedModel}
                documentPreview={documentPreview}
                availableModels={availableModels}
                isGenerating={isGenerating}
                onFileSelect={handleFileSelect}
                onModelSelect={setSelectedModel}
                onGenerate={handleGeneration}
                onModelsLoad={setAvailableModels}
              />
            </div>

            {/* Secondary Schema Reference */}
            <div className="lg:col-span-1">
              <div className="bg-gray-50/50 rounded-2xl p-6 border border-gray-100">
                <SchemaList
                  schemas={schemas}
                  isLoading={isLoading}
                  onEditSchema={handleEditSchema}
                  onDeleteSchema={handleDeleteSchema}
                  isOperationInProgress={isOperationInProgress}
                  className="max-h-[500px]"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Schema List (when not in generation mode) */}
      {!showGeneration && viewMode === "list" && (
        <SchemaList
          schemas={schemas}
          isLoading={isLoading}
          onEditSchema={handleEditSchema}
          onDeleteSchema={handleDeleteSchema}
          isOperationInProgress={isOperationInProgress}
        />
      )}

      {/* Schema Editor */}
      {(viewMode === "edit" || viewMode === "create") && (
        <div ref={resultsRef} className="mt-8">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
            <SchemaEditor
              schema={viewMode === "edit" ? activeSchema : null}
              aiDebugInfo={aiDebugInfo}
              onSave={handleSaveSchema}
              onCancel={handleCancelEdit}
              isLoading={
                isOperationInProgress("create") ||
                isOperationInProgress(activeSchema?.id || "")
              }
            />
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useCallback, useEffect } from "react";
import Image from "next/image";
import {
  Upload,
  FileText,
  Brain,
  Wand2,
  Loader2,
  Eye,
} from "lucide-react";
import { Button } from "@/components/ui/button";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { apiClient } from "@/lib/api";

interface MinimalModel {
  id: string;
  name: string;
}

interface SchemaGenerationFormProps {
  selectedFile: File | null;
  selectedModel: string;
  documentPreview: string | null;
  availableModels: MinimalModel[];
  isGenerating: boolean;
  onFileSelect: (file: File | null) => void;
  onModelSelect: (modelId: string) => void;
  onGenerate: () => void;
  onModelsLoad: (models: MinimalModel[]) => void;
}

export function SchemaGenerationForm({
  selectedFile,
  selectedModel,
  documentPreview,
  availableModels,
  isGenerating,
  onFileSelect,
  onModelSelect,
  onGenerate,
  onModelsLoad,
}: SchemaGenerationFormProps) {
  const loadModels = useCallback(async () => {
    try {
      const response = await apiClient.getSupportedModels();
      if (response.success && response.models) {
        onModelsLoad(response.models);
        // Auto-select the first model if none is selected
        if (!selectedModel && response.models.length > 0) {
          onModelSelect(response.models[0].id);
        }
      } else {
        console.error("Failed to load models");
      }
    } catch (error) {
      console.error("Error loading models:", error);
    }
  }, [onModelsLoad, selectedModel, onModelSelect]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    onFileSelect(file);
  };

  const truncateFileName = (name: string, maxLength: number = 25) => {
    if (name.length <= maxLength) return name;
    const ext = name.split('.').pop();
    const nameWithoutExt = name.substring(0, name.lastIndexOf('.'));
    const truncated = nameWithoutExt.substring(0, maxLength - 5 - (ext?.length || 0));
    return `${truncated}...${ext}`;
  };

  return (
    <Card className="h-fit">
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Wand2 className="h-4 w-4" />
          Configuration
        </CardTitle>
        <CardDescription className="text-xs">
          Select your document and configure generation settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* File Upload */}
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">Sample Document</Label>
          <div className="space-y-2">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            {!selectedFile ? (
              <Label
                htmlFor="file-upload"
                className="flex items-center justify-center gap-2 px-3 py-2 text-sm border rounded-md cursor-pointer hover:bg-accent transition-colors"
              >
                <Upload className="h-3.5 w-3.5" />
                Choose Document
              </Label>
            ) : (
              <div className="flex items-center gap-2">
                <Label
                  htmlFor="file-upload"
                  className="flex-1 flex items-center gap-2 px-3 py-2 text-sm bg-muted/50 rounded-md cursor-pointer hover:bg-muted transition-colors"
                >
                  <FileText className="h-3.5 w-3.5 flex-shrink-0" />
                  <span className="truncate text-xs">
                    {truncateFileName(selectedFile.name)}
                  </span>
                </Label>
                {documentPreview && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 px-2">
                        <Eye className="h-3.5 w-3.5" />
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
                          <Image
                            src={documentPreview}
                            alt="Document preview"
                            width={1200}
                            height={800}
                            className="max-w-full h-auto"
                            unoptimized
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
        <div className="space-y-1.5">
          <Label className="text-xs font-medium">AI Model</Label>
          <Select value={selectedModel} onValueChange={onModelSelect}>
            <SelectTrigger className="h-8 text-sm">
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
          onClick={onGenerate}
          disabled={!selectedFile || isGenerating}
          className={`w-full h-9 transition-all duration-200 ${
            isGenerating
              ? 'bg-blue-600 hover:bg-blue-600 cursor-not-allowed'
              : 'hover:bg-primary/90 hover:scale-[1.02]'
          }`}
          size="sm"
        >
          {isGenerating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              <span className="font-medium">Analyzing Document...</span>
            </>
          ) : (
            <>
              <Brain className="h-4 w-4 mr-2" />
              <span className="font-medium">Analyze Document</span>
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
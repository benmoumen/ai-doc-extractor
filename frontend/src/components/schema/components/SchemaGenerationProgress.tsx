"use client";

import React from "react";
import { Loader2, CheckCircle, Clock, XCircle, Brain, FileText, Search, Target, Zap } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface GenerationStep {
  name: string;
  status: "pending" | "in_progress" | "completed" | "failed";
  duration?: number;
}

interface SchemaGenerationProgressProps {
  isGenerating: boolean;
  generationProgress: number;
  currentStep: string;
  generationSteps: GenerationStep[];
}

export function SchemaGenerationProgress({
  isGenerating,
  generationProgress,
  currentStep,
  generationSteps,
}: SchemaGenerationProgressProps) {
  const getStepIcon = (status: GenerationStep["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "in_progress":
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  if (!isGenerating) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Loader2 className="h-5 w-5 animate-spin" />
          Analysis Progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>{currentStep}</span>
            {generationProgress === 100 ? (
              <span className="text-green-600 font-medium">✓ Complete</span>
            ) : (
              <span className="text-blue-600 flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processing...
              </span>
            )}
          </div>
          {generationProgress === 100 ? (
            <Progress value={100} className="bg-green-100" />
          ) : (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse w-full opacity-70"></div>
            </div>
          )}
        </div>

        {/* Processing State */}
        {generationProgress === 100 ? (
          // Show actual steps after completion
          <div className="space-y-2">
            {generationSteps.map((step) => (
              <div
                key={step.name}
                className="flex items-center gap-3 text-sm"
              >
                {getStepIcon(step.status)}
                <span
                  className={
                    step.status === "completed"
                      ? "text-green-600 dark:text-green-400"
                      : step.status === "in_progress"
                      ? "text-blue-600 dark:text-blue-400"
                      : step.status === "failed"
                      ? "text-red-600 dark:text-red-400"
                      : "text-gray-500"
                  }
                >
                  {step.name}
                </span>
                {step.duration && (
                  <span className="text-xs text-gray-400 ml-auto">
                    {step.duration.toFixed(1)}s
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (
          // Show simple processing message during API call
          <div className="text-center py-4 text-gray-500">
            <div className="flex items-center justify-center gap-2 text-sm">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span>AI is analyzing your document...</span>
            </div>
            <p className="text-xs mt-2 text-gray-400">
              This may take a few moments depending on document complexity
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Predefined step configurations
// Icons are created inside component to avoid runtime errors
export const getAIGenerationSteps = () => ({
  DOCUMENT_UPLOAD: {
    name: "Document Upload",
    description: "Processing uploaded document",
    iconType: "FileText",
    iconColor: "text-blue-500"
  },
  CONTENT_EXTRACTION: {
    name: "Content Extraction",
    description: "Extracting text and structure from document",
    iconType: "Search",
    iconColor: "text-purple-500"
  },
  AI_ANALYSIS: {
    name: "AI Analysis",
    description: "Analyzing document structure and content",
    iconType: "Brain",
    iconColor: "text-orange-500"
  },
  FIELD_DETECTION: {
    name: "Field Detection",
    description: "Identifying potential extraction fields",
    iconType: "Target",
    iconColor: "text-green-500"
  },
  SCHEMA_GENERATION: {
    name: "Schema Generation",
    description: "Generating extraction schema",
    iconType: "Zap",
    iconColor: "text-yellow-500"
  },
  QUALITY_ASSESSMENT: {
    name: "Quality Assessment",
    description: "Evaluating schema quality and confidence",
    iconType: "CheckCircle",
    iconColor: "text-indigo-500"
  }
});

// Helper function to get icon component
export const getStepIcon = (iconType: string, iconColor: string) => {
  const className = `h-3 w-3 ${iconColor}`;
  switch (iconType) {
    case "FileText":
      return <FileText className={className} />;
    case "Search":
      return <Search className={className} />;
    case "Brain":
      return <Brain className={className} />;
    case "Target":
      return <Target className={className} />;
    case "Zap":
      return <Zap className={className} />;
    case "CheckCircle":
      return <CheckCircle className={className} />;
    default:
      return <Clock className={className} />;
  }
};
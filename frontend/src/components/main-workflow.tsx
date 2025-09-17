"use client";

import React, { useState } from "react";
import { FileText, Brain, Wand2, Zap } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import { ExtractionWorkflow } from "./extraction/extraction-workflow";
import { SchemaGenerator } from "./schema/schema-generator";

export function MainWorkflow() {
  const [generatedSchemaId, setGeneratedSchemaId] = useState<string | null>(
    null
  );

  const handleSchemaGenerated = (schemaId: string) => {
    setGeneratedSchemaId(schemaId);
    // Optionally switch to extraction tab to use the new schema
    // You could trigger a tab switch here if desired
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="space-y-2 mb-6">
        <h1 className="text-3xl font-bold">AI Data Extractor</h1>
        <p className="text-muted-foreground">
          Extract structured data from documents or generate custom schemas
          using AI
        </p>
      </div>

      <Tabs defaultValue="extraction" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="extraction" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Data Extraction
          </TabsTrigger>
          <TabsTrigger
            value="schema-generation"
            className="flex items-center gap-2"
          >
            <Brain className="h-4 w-4" />
            Document Analysis
          </TabsTrigger>
        </TabsList>

        <TabsContent value="extraction" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-blue-500" />
                Document Data Extraction
              </CardTitle>
              <CardDescription>
                Extract structured data from your documents using AI or
                predefined schemas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ExtractionWorkflow />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="schema-generation" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-purple-500" />
                AI Document Analysis
              </CardTitle>
              <CardDescription>
                Analyze sample documents to understand structure and create
                extraction templates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SchemaGenerator
                onSchemaGenerated={handleSchemaGenerated}
                className="mt-0"
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Optional: Show notification when schema is generated */}
      {generatedSchemaId && (
        <div className="fixed bottom-4 right-4 bg-green-100 dark:bg-green-900 border border-green-300 dark:border-green-700 rounded-lg p-4 shadow-lg max-w-sm">
          <div className="flex items-start gap-3">
            <Brain className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-green-800 dark:text-green-200">
                Schema Generated Successfully!
              </h4>
              <p className="text-xs text-green-600 dark:text-green-300 mt-1">
                Your new schema is ready to use in the Data Extraction tab.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

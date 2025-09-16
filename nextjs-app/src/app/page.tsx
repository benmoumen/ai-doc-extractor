"use client";

import { useState } from "react";
import { FileText, Sparkles, Zap, Shield, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "sonner";
import { ExtractionWorkflow } from "@/components/extraction/extraction-workflow";
import { SchemaGenerator } from "@/components/schema/schema-generator";

export default function Home() {
  const [activeTab, setActiveTab] = useState("extract");

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Toaster position="top-right" richColors />

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-lg bg-white/70 dark:bg-gray-950/70 border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">AI Document Extractor</h1>
                <p className="text-xs text-muted-foreground">
                  Intelligent data extraction platform
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="gap-1">
                <Sparkles className="h-3 w-3" />
                AI Powered
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="max-w-4xl mx-auto text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 text-sm mb-4">
            <Zap className="h-4 w-4" />
            <span>Advanced extraction with AI & schemas</span>
          </div>
          <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Extract Data from Any Document
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload your documents and let our AI automatically extract
            structured data. Use predefined schemas for consistency or let AI
            discover fields automatically.
          </p>
        </div>

        {/* Main Workflow Tabs */}
        <div className="max-w-7xl mx-auto">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="space-y-6"
          >
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-2">
              <TabsTrigger value="extract" className="gap-2">
                <Sparkles className="h-4 w-4" />
                Data Extraction
              </TabsTrigger>
              <TabsTrigger value="schemas" className="gap-2">
                <FileText className="h-4 w-4" />
                Schema Generation
              </TabsTrigger>
            </TabsList>

            <TabsContent value="extract" className="space-y-6">
              <ExtractionWorkflow />
            </TabsContent>

            <TabsContent value="schemas" className="space-y-6">
              <SchemaGenerator />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}

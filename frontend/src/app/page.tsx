"use client";

import { useState } from "react";
import { FileText, Sparkles, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Toaster } from "sonner";
import { ExtractionWorkflow } from "@/components/extraction/extraction-workflow";
import { SchemaManager } from "@/components/schema/SchemaManager";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [heroCollapsed, setHeroCollapsed] = useState(false);

  const handleTabChange = (value: string) => {
    if (!activeTab) {
      // First tab selection - collapse hero
      setHeroCollapsed(true);
      // Small delay to allow hero collapse animation to start
      setTimeout(() => setActiveTab(value), 100);
    } else {
      // Switching between tabs - no hero animation
      setActiveTab(value);
    }
  };

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
                <h1 className="text-xl font-bold">AI Data Extractor</h1>
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
      <main className="container mx-auto px-4">
        {/* Hero Section - Collapsible */}
        <div
          className={`transition-all duration-700 ease-in-out overflow-hidden ${
            heroCollapsed
              ? 'max-h-0 opacity-0 py-0'
              : 'max-h-96 opacity-100 py-8'
          }`}
        >
          <div className="max-w-4xl mx-auto text-center">
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
        </div>

        {/* Main Workflow Tabs */}
        <div className={`max-w-7xl mx-auto transition-all duration-500 ${
          heroCollapsed ? 'pt-8' : 'pt-0'
        }`}>
          <Tabs
            value={activeTab || ""}
            onValueChange={handleTabChange}
            className="space-y-6"
          >
            <TabsList className={`grid w-full max-w-md mx-auto grid-cols-2 gap-4 transition-all duration-500 ${
              !activeTab ? 'opacity-90 scale-98' : 'opacity-100 scale-100'
            }`}>
              <TabsTrigger
                value="extract"
                className={`gap-2 transition-all duration-300 hover:scale-105 hover:shadow-sm ${
                  !activeTab
                    ? 'bg-white/80 text-gray-700 border border-gray-200 hover:bg-white hover:text-gray-900 hover:border-blue-300'
                    : ''
                }`}
              >
                <Sparkles className="h-4 w-4" />
                Data Extraction
                <Badge
                  variant="secondary"
                  className={`ml-auto text-xs border ${
                    !activeTab ? 'bg-blue-100 text-blue-700 border-blue-200' : 'border-gray-300'
                  }`}
                >
                  DS
                </Badge>
              </TabsTrigger>
              <TabsTrigger
                value="schemas"
                className={`gap-2 transition-all duration-300 hover:scale-105 hover:shadow-sm ${
                  !activeTab
                    ? 'bg-white/80 text-gray-700 border border-gray-200 hover:bg-white hover:text-gray-900 hover:border-purple-300'
                    : ''
                }`}
              >
                <FileText className="h-4 w-4" />
                Document Analysis
                <Badge
                  variant="secondary"
                  className={`ml-auto text-xs border ${
                    !activeTab ? 'bg-purple-100 text-purple-700 border-purple-200' : 'border-gray-300'
                  }`}
                >
                  BPA
                </Badge>
              </TabsTrigger>
            </TabsList>

            {/* Tab Content with fade-in animation */}
            <div className={`transition-all duration-500 ${
              activeTab ? 'opacity-100 transform translate-y-0' : 'opacity-0 transform translate-y-4'
            }`}>
              {activeTab === "extract" && (
                <TabsContent value="extract" className="space-y-6 mt-0">
                  <ExtractionWorkflow />
                </TabsContent>
              )}

              {activeTab === "schemas" && (
                <TabsContent value="schemas" className="space-y-6 mt-0">
                  <SchemaManager />
                </TabsContent>
              )}
            </div>
          </Tabs>
        </div>

        {/* Call to Action when no tab is selected */}
        {!activeTab && (
          <div className="max-w-md mx-auto text-center mt-8 pb-16">
            <p className="text-muted-foreground mb-4">
              Choose your workflow to get started
            </p>
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span>Click a tab above to begin</span>
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-300" />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
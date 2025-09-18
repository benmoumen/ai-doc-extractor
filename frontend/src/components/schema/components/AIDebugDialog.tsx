"use client";

import React from "react";
import { Brain } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { GeneratedSchema } from "../types";
import { AIDebugInfo, AIDebugStep } from "@/types";
import { isDebugFeatureEnabled } from "@/lib/debug";

interface AIDebugDialogProps {
  schema: GeneratedSchema | null;
  aiDebugInfo?: AIDebugInfo | null;
  trigger?: React.ReactNode;
}

export function AIDebugDialog({ schema, aiDebugInfo, trigger }: AIDebugDialogProps) {
  // Don't render debug dialog if debug mode is disabled
  if (!isDebugFeatureEnabled('aiDebugDialog')) {
    return null;
  }

  if (!schema) {
    return null;
  }

  // Show debug info only if available, otherwise show a message
  const hasDebugInfo = aiDebugInfo && aiDebugInfo.steps && aiDebugInfo.steps.length > 0;

  const defaultTrigger = (
    <Button variant="outline" size="sm" className="gap-2">
      <Brain className="h-3 w-3" />
      AI Debug Info
    </Button>
  );

  return (
    <Dialog>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-500" />
            Multi-Step AI Document Analysis Debug
          </DialogTitle>
          <DialogDescription>
            Detailed information about the AI document analysis process for &ldquo;{schema.name}&rdquo;
          </DialogDescription>
        </DialogHeader>

        {!hasDebugInfo ? (
          <div className="text-center py-8">
            <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="font-medium text-gray-900 mb-2">No Debug Information Available</h3>
            <p className="text-sm text-gray-500">
              Debug information is only available for schemas generated with AI analysis.
            </p>
          </div>
        ) : (
          <div className="overflow-y-auto max-h-[70vh] space-y-4">
            {/* Summary Statistics */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h3 className="font-medium text-blue-900 mb-3 flex items-center gap-2">
                <Brain className="h-4 w-4" />
                Overall Analysis Summary
              </h3>
              {(() => {
                // Calculate totals across all steps
                const totalStats = aiDebugInfo.steps?.reduce((acc, step) => {
                  const tokens = step.tokens_used;
                  if (tokens) {
                    acc.promptTokens += tokens.prompt_tokens || 0;
                    acc.completionTokens += tokens.completion_tokens || 0;
                    acc.totalTokens += tokens.total_tokens || 0;
                    acc.totalTime += tokens.total_time || 0;
                    acc.queueTime += tokens.queue_time || 0;
                    acc.promptTime += tokens.prompt_time || 0;
                    acc.completionTime += tokens.completion_time || 0;
                  }
                  acc.duration += step.duration || 0;
                  acc.successfulSteps += step.success ? 1 : 0;
                  return acc;
                }, {
                  promptTokens: 0,
                  completionTokens: 0,
                  totalTokens: 0,
                  totalTime: 0,
                  queueTime: 0,
                  promptTime: 0,
                  completionTime: 0,
                  duration: 0,
                  successfulSteps: 0
                }) || {
                  promptTokens: 0,
                  completionTokens: 0,
                  totalTokens: 0,
                  totalTime: 0,
                  queueTime: 0,
                  promptTime: 0,
                  completionTime: 0,
                  duration: 0,
                  successfulSteps: 0
                };

                const totalSteps = aiDebugInfo.steps?.length || 0;
                const successRate = totalSteps > 0 ? (totalStats.successfulSteps / totalSteps) * 100 : 0;

                return (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-white rounded-lg p-3 border border-blue-100">
                      <h4 className="font-medium text-blue-800 mb-2 text-sm">Token Usage</h4>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Input Tokens:</span>
                          <span className="font-mono">{totalStats.promptTokens.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Output Tokens:</span>
                          <span className="font-mono">{totalStats.completionTokens.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between border-t pt-1">
                          <span className="font-medium">Total Tokens:</span>
                          <span className="font-mono font-medium">{totalStats.totalTokens.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-3 border border-blue-100">
                      <h4 className="font-medium text-blue-800 mb-2 text-sm">Timing Analysis</h4>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Queue Time:</span>
                          <span className="font-mono">{totalStats.queueTime.toFixed(2)}s</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Processing:</span>
                          <span className="font-mono">{totalStats.completionTime.toFixed(2)}s</span>
                        </div>
                        <div className="flex justify-between border-t pt-1">
                          <span className="font-medium">Total Duration:</span>
                          <span className="font-mono font-medium">{totalStats.duration.toFixed(2)}s</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-white rounded-lg p-3 border border-blue-100">
                      <h4 className="font-medium text-blue-800 mb-2 text-sm">Success Metrics</h4>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span>Steps Completed:</span>
                          <span className="font-mono">{totalStats.successfulSteps}/{totalSteps}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Success Rate:</span>
                          <span className="font-mono">{successRate.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between border-t pt-1">
                          <span className="font-medium">Tokens/Second:</span>
                          <span className="font-mono font-medium">
                            {totalStats.duration > 0 ? (totalStats.totalTokens / totalStats.duration).toFixed(0) : '0'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Individual Step Details */}
            {aiDebugInfo.steps?.map((step: AIDebugStep, index: number) => (
              <Card key={index} className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                      Step {step.step}
                    </span>
                    {step.name}
                    <Badge
                      variant={step.success ? "default" : "destructive"}
                      className="ml-auto"
                    >
                      {step.success ? "Success" : "Failed"}
                    </Badge>
                  </CardTitle>
                  <p className="text-xs text-muted-foreground">
                    Duration: {(step.duration || 0).toFixed(2)}s
                  </p>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="space-y-2">
                    <Label className="text-xs font-medium">AI Prompt:</Label>
                    <div className="bg-slate-50 p-3 rounded-lg text-xs font-mono max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap">
                        {step.prompt || "No prompt data available"}
                      </pre>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">Raw AI Response:</Label>
                    <div className="bg-slate-50 p-3 rounded-lg text-xs font-mono max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap">
                        {step.raw_response || "No response data available"}
                      </pre>
                    </div>
                  </div>

                  {step.parsed_data && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium">Parsed Data:</Label>
                      <div className="bg-green-50 p-3 rounded-lg text-xs font-mono max-h-32 overflow-y-auto">
                        <pre className="whitespace-pre-wrap">
                          {typeof step.parsed_data === 'string'
                            ? step.parsed_data
                            : JSON.stringify(step.parsed_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {step.tokens_used && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium">Performance Metrics:</Label>
                      <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg text-xs">
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="font-medium text-blue-800 mb-1">Tokens</p>
                            <p>Prompt: {step.tokens_used.prompt_tokens.toLocaleString()}</p>
                            <p>Completion: {step.tokens_used.completion_tokens.toLocaleString()}</p>
                            <p>Total: {step.tokens_used.total_tokens.toLocaleString()}</p>
                          </div>
                          {step.tokens_used.total_time && (
                            <div>
                              <p className="font-medium text-blue-800 mb-1">Timing (seconds)</p>
                              {step.tokens_used.queue_time && <p>Queue: {step.tokens_used.queue_time.toFixed(3)}s</p>}
                              {step.tokens_used.prompt_time && <p>Prompt: {step.tokens_used.prompt_time.toFixed(3)}s</p>}
                              {step.tokens_used.completion_time && <p>Completion: {step.tokens_used.completion_time.toFixed(3)}s</p>}
                              <p className="font-medium">Total: {step.tokens_used.total_time.toFixed(3)}s</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Debug: Show all available fields */}
                  <details className="mt-4">
                    <summary className="text-xs font-medium text-gray-600 cursor-pointer hover:text-gray-800">
                      🔍 Show raw step data
                    </summary>
                    <div className="mt-2 bg-gray-50 p-3 rounded-lg text-xs font-mono max-h-32 overflow-y-auto">
                      <pre className="whitespace-pre-wrap">
                        {JSON.stringify(step, null, 2)}
                      </pre>
                    </div>
                  </details>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
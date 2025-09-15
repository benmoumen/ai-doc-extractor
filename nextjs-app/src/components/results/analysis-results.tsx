'use client'

import React, { useState } from 'react'
import {
  FileText,
  Brain,
  Target,
  Database,
  Download,
  Edit3,
  AlertCircle,
  CheckCircle2,
  TrendingUp
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table'

import { DocumentAnalysisResponse } from '@/types'

interface AnalysisResultsProps {
  result: DocumentAnalysisResponse
  onExport?: (format: string) => void
  onEditField?: (fieldId: string, newValue: any) => void
  onRetryAnalysis?: () => void
  className?: string
}

export function AnalysisResults({
  result,
  onExport,
  onEditField,
  onRetryAnalysis,
  className
}: AnalysisResultsProps) {
  const [activeTab, setActiveTab] = useState('overview')

  if (!result.success) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="flex items-center space-x-3 text-red-600">
            <AlertCircle className="h-5 w-5" />
            <span>Analysis failed: {result.errors?.[0] || 'Unknown error'}</span>
          </div>
          {onRetryAnalysis && (
            <Button onClick={onRetryAnalysis} variant="outline" className="mt-4">
              Retry Analysis
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.8) return 'default'
    if (confidence >= 0.6) return 'secondary'
    return 'destructive'
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Brain className="h-5 w-5" />
              <span>Analysis Results</span>
            </CardTitle>
            <CardDescription>
              AI-extracted data from {result.document.filename}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={getConfidenceBadge(result.confidence.overall_confidence)}>
              {Math.round(result.confidence.overall_confidence * 100)}% Confidence
            </Badge>
            <Badge variant="outline">
              {result.confidence.confidence_level}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="fields">Fields</TabsTrigger>
            <TabsTrigger value="schema">Schema</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6 mt-6">
            {/* Document Info */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Document Type</span>
                </div>
                <div className="text-lg font-semibold">
                  {result.analysis.detected_document_type}
                </div>
                <div className="text-xs text-gray-500">
                  {Math.round(result.analysis.document_type_confidence * 100)}% confidence
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Target className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Fields Detected</span>
                </div>
                <div className="text-lg font-semibold">
                  {result.analysis.total_fields_detected}
                </div>
                <div className="text-xs text-gray-500">
                  {result.analysis.high_confidence_fields} high confidence
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Database className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Schema Generated</span>
                </div>
                <div className="text-lg font-semibold">
                  {result.schema.total_fields} fields
                </div>
                <div className="text-xs text-gray-500">
                  {result.schema.production_ready ? 'Production Ready' : 'Needs Review'}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Quality Score</span>
                </div>
                <div className="text-lg font-semibold">
                  {Math.round(result.analysis.overall_quality_score * 100)}%
                </div>
                <div className="text-xs text-gray-500">
                  Overall quality
                </div>
              </div>
            </div>

            {/* Processing Summary */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Processing Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Processing Time</span>
                    <span className="font-medium">{result.total_processing_time.toFixed(1)}s</span>
                  </div>
                  <Progress value={100} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Overall Confidence</span>
                    <span className={`font-medium ${getConfidenceColor(result.confidence.overall_confidence)}`}>
                      {Math.round(result.confidence.overall_confidence * 100)}%
                    </span>
                  </div>
                  <Progress
                    value={result.confidence.overall_confidence * 100}
                    className="h-2"
                  />
                </div>
              </div>
            </div>

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium">Recommendations</h3>
                <ul className="space-y-1">
                  {result.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-gray-600 flex items-start space-x-2">
                      <CheckCircle2 className="h-3 w-3 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </TabsContent>

          <TabsContent value="fields" className="space-y-4 mt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Extracted Fields</h3>
              <Button variant="outline" size="sm">
                <Edit3 className="h-4 w-4 mr-2" />
                Edit Fields
              </Button>
            </div>

            {/* This would be populated with actual field data from the analysis */}
            <div className="text-sm text-gray-500">
              Field data would be displayed here when available from the analysis results.
              The backend provides detailed field information in get_analysis_results().
            </div>
          </TabsContent>

          <TabsContent value="schema" className="space-y-4 mt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium">Generated Schema</h3>
              <div className="flex space-x-2">
                <Button variant="outline" size="sm">
                  View JSON Schema
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export Schema
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="pt-4">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Schema Name:</span>
                      <div className="text-gray-600">{result.schema.name}</div>
                    </div>
                    <div>
                      <span className="font-medium">Total Fields:</span>
                      <div className="text-gray-600">{result.schema.total_fields}</div>
                    </div>
                    <div>
                      <span className="font-medium">High Confidence Fields:</span>
                      <div className="text-gray-600">{result.schema.high_confidence_fields}</div>
                    </div>
                    <div>
                      <span className="font-medium">Generation Confidence:</span>
                      <div className={`${getConfidenceColor(result.schema.generation_confidence)}`}>
                        {Math.round(result.schema.generation_confidence * 100)}%
                      </div>
                    </div>
                  </div>

                  <div>
                    <span className="font-medium text-sm">Description:</span>
                    <div className="text-sm text-gray-600 mt-1">
                      {result.schema.description || 'No description available'}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Production Ready:</span>
                    {result.schema.production_ready ? (
                      <Badge variant="default">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Ready
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        <AlertCircle className="h-3 w-3 mr-1" />
                        Needs Review
                      </Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="performance" className="space-y-4 mt-6">
            <div className="space-y-4">
              <h3 className="text-sm font-medium">Performance Metrics</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Total Time</span>
                        <span className="text-lg font-bold">
                          {result.total_processing_time.toFixed(1)}s
                        </span>
                      </div>
                      <Progress value={100} className="h-2" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Model Used</span>
                        <Badge variant="outline">{result.analysis.model_used}</Badge>
                      </div>
                      <div className="text-xs text-gray-500">
                        AI processing model
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">File Size</span>
                        <span className="text-sm font-medium">
                          {(result.document.file_size / 1024 / 1024).toFixed(1)}MB
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {result.document.file_type.toUpperCase()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Stage breakdown would go here */}
              <div className="text-sm text-gray-500">
                Detailed stage performance metrics available in processing_stages data.
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-6 border-t">
          <div className="flex space-x-2">
            {onRetryAnalysis && (
              <Button variant="outline" onClick={onRetryAnalysis}>
                Retry Analysis
              </Button>
            )}
          </div>

          <div className="flex space-x-2">
            {onExport && (
              <>
                <Button variant="outline" size="sm" onClick={() => onExport('json')}>
                  <Download className="h-4 w-4 mr-2" />
                  JSON
                </Button>
                <Button variant="outline" size="sm" onClick={() => onExport('csv')}>
                  <Download className="h-4 w-4 mr-2" />
                  CSV
                </Button>
                <Button variant="outline" size="sm" onClick={() => onExport('pdf')}>
                  <Download className="h-4 w-4 mr-2" />
                  PDF
                </Button>
              </>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
'use client'

import React, { useState } from 'react'
import {
  FileText, Upload, Loader2, CheckCircle, AlertCircle,
  ArrowRight, RefreshCw, Download, Sparkles, Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { toast } from 'sonner'

import { DocumentUpload } from '@/components/document-upload/document-upload'
import { SchemaSelector, type Schema } from './schema-selector'
import { ExtractionResults, type ExtractionResult, type ExtractedField } from './extraction-results'
import { apiClient } from '@/lib/api'

interface WorkflowStep {
  id: string
  name: string
  description: string
  status: 'pending' | 'active' | 'completed' | 'error'
  progress?: number
}

export function ExtractionWorkflow() {
  const [currentStep, setCurrentStep] = useState<'upload' | 'configure' | 'extract' | 'results'>('upload')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null)
  const [useAI, setUseAI] = useState(true)
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null)
  const [extractionProgress, setExtractionProgress] = useState(0)

  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    {
      id: 'upload',
      name: 'Upload Document',
      description: 'Select and upload your document',
      status: 'active'
    },
    {
      id: 'configure',
      name: 'Configure Extraction',
      description: 'Choose extraction method',
      status: 'pending'
    },
    {
      id: 'extract',
      name: 'Extract Data',
      description: 'AI processing your document',
      status: 'pending'
    },
    {
      id: 'results',
      name: 'Review & Export',
      description: 'Review and export results',
      status: 'pending'
    }
  ])

  const updateStepStatus = (stepId: string, status: WorkflowStep['status'], progress?: number) => {
    setWorkflowSteps(prev => prev.map(step =>
      step.id === stepId ? { ...step, status, progress } : step
    ))
  }

  const handleUploadStart = (file: File) => {
    setUploadedFile(file)
    updateStepStatus('upload', 'active')
  }

  const handleUploadComplete = (result: any) => {
    if (result.success) {
      updateStepStatus('upload', 'completed')
      updateStepStatus('configure', 'active')
      setCurrentStep('configure')
      toast.success('Document uploaded successfully')
    } else {
      updateStepStatus('upload', 'error')
      toast.error('Upload failed. Please try again.')
    }
  }

  const handleSchemaSelect = (schemaId: string | null, aiMode: boolean) => {
    setSelectedSchema(schemaId)
    setUseAI(aiMode)
  }

  const handleStartExtraction = async () => {
    if (!uploadedFile) return

    setIsExtracting(true)
    updateStepStatus('configure', 'completed')
    updateStepStatus('extract', 'active')
    setCurrentStep('extract')
    setExtractionProgress(0)

    // Progress simulation for UI feedback
    const progressInterval = setInterval(() => {
      setExtractionProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return 90
        }
        return prev + 10
      })
    }, 500)

    try {
      // Call real API for data extraction
      const result = await apiClient.extractData(
        uploadedFile,
        selectedSchema || undefined,
        useAI,
        'llama-scout' // Default model - could be made configurable
      )

      clearInterval(progressInterval)
      setExtractionProgress(100)

      if (result.success) {
        // Transform API response to match our component interface
        const extractionResult: ExtractionResult = {
          id: result.extraction_id,
          documentType: result.document_type,
          extractionMode: result.extraction_mode,
          schemaUsed: result.schema_used,
          processingTime: result.processing_time,
          confidence: result.confidence,
          extractedFields: result.extracted_fields.map((field: any) => ({
            id: field.id,
            name: field.name,
            displayName: field.display_name,
            value: field.value,
            type: field.type,
            confidence: field.confidence,
            source: field.source,
            validation: {
              isValid: field.validation?.is_valid ?? true,
              errors: field.validation?.errors || []
            }
          })),
          warnings: result.warnings || [],
          suggestions: result.suggestions || []
        }

        setExtractionResult(extractionResult)
        updateStepStatus('extract', 'completed')
        updateStepStatus('results', 'active')
        setCurrentStep('results')
        toast.success('Extraction completed successfully!')
      } else {
        throw new Error(result.error || 'Extraction failed')
      }
    } catch (error) {
      console.error('Extraction error:', error)
      clearInterval(progressInterval)
      updateStepStatus('extract', 'error')

      const errorMessage = error instanceof Error ? error.message : 'Extraction failed. Please try again.'
      toast.error(errorMessage)
    } finally {
      setIsExtracting(false)
    }
  }

  const handleFieldUpdate = (fieldId: string, newValue: any) => {
    if (!extractionResult) return

    setExtractionResult({
      ...extractionResult,
      extractedFields: extractionResult.extractedFields.map(field =>
        field.id === fieldId ? { ...field, value: newValue } : field
      )
    })
  }

  const handleExport = (format: 'json' | 'csv' | 'excel') => {
    if (!extractionResult) return

    const data = extractionResult.extractedFields.reduce((acc, field) => {
      acc[field.name] = field.value
      return acc
    }, {} as Record<string, any>)

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `extraction-${extractionResult.id}.json`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Data exported as JSON')
    } else if (format === 'csv') {
      // Create CSV content
      const headers = ['Field Name', 'Value', 'Type', 'Confidence', 'Source', 'Valid']
      const rows = extractionResult.extractedFields.map(field => [
        field.displayName,
        field.value?.toString() || '',
        field.type,
        (field.confidence * 100).toFixed(1) + '%',
        field.source,
        field.validation.isValid ? 'Yes' : 'No'
      ])

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell.toString().replace(/"/g, '""')}"`).join(','))
      ].join('\n')

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `extraction-${extractionResult.id}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Data exported as CSV')
    } else if (format === 'excel') {
      // Create a basic Excel-compatible CSV with metadata
      const headers = ['Field Name', 'Value', 'Type', 'Confidence', 'Source', 'Valid', 'Display Name']
      const metadataRows = [
        ['Document Type', extractionResult.documentType, '', '', '', '', ''],
        ['Extraction Mode', extractionResult.extractionMode, '', '', '', '', ''],
        ['Processing Time', `${extractionResult.processingTime?.toFixed(2)}s`, '', '', '', '', ''],
        ['Overall Confidence', `${(extractionResult.confidence * 100).toFixed(1)}%`, '', '', '', '', ''],
        ['', '', '', '', '', '', ''], // Empty row
      ]
      const fieldRows = extractionResult.extractedFields.map(field => [
        field.name,
        field.value?.toString() || '',
        field.type,
        (field.confidence * 100).toFixed(1) + '%',
        field.source,
        field.validation.isValid ? 'Yes' : 'No',
        field.displayName
      ])

      const excelContent = [
        headers.join(','),
        ...metadataRows.map(row => row.map(cell => `"${cell.toString().replace(/"/g, '""')}"`).join(',')),
        ...fieldRows.map(row => row.map(cell => `"${cell.toString().replace(/"/g, '""')}"`).join(','))
      ].join('\n')

      const blob = new Blob([excelContent], { type: 'application/vnd.ms-excel' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `extraction-${extractionResult.id}.csv`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Data exported for Excel')
    }
  }

  const handleReset = () => {
    setCurrentStep('upload')
    setUploadedFile(null)
    setSelectedSchema(null)
    setUseAI(true)
    setExtractionResult(null)
    setExtractionProgress(0)
    setWorkflowSteps(prev => prev.map(step => ({
      ...step,
      status: step.id === 'upload' ? 'active' : 'pending',
      progress: undefined
    })))
  }

  return (
    <div className="space-y-6">
      {/* Workflow Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {workflowSteps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className="flex flex-col items-center gap-2">
                  <div className={`
                    w-10 h-10 rounded-full flex items-center justify-center
                    ${step.status === 'completed' ? 'bg-green-500 text-white' :
                      step.status === 'active' ? 'bg-blue-500 text-white' :
                      step.status === 'error' ? 'bg-red-500 text-white' :
                      'bg-gray-200 text-gray-400'}
                  `}>
                    {step.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : step.status === 'error' ? (
                      <AlertCircle className="h-5 w-5" />
                    ) : step.status === 'active' ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium">{step.name}</p>
                    <p className="text-xs text-muted-foreground">{step.description}</p>
                  </div>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div className={`
                    flex-1 h-0.5 mx-4
                    ${workflowSteps[index + 1].status !== 'pending' ? 'bg-blue-500' : 'bg-gray-200'}
                  `} />
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
          {currentStep === 'upload' && (
            <DocumentUpload
              onUploadComplete={handleUploadComplete}
              onUploadStart={handleUploadStart}
            />
          )}

          {/* Configure Step */}
          {currentStep === 'configure' && uploadedFile && (
            <Card>
              <CardHeader>
                <CardTitle>Configure Extraction</CardTitle>
                <CardDescription>
                  Choose how you want to extract data from {uploadedFile.name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <SchemaSelector onSchemaSelect={handleSchemaSelect} />

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Ready to extract</p>
                    <p className="text-xs text-muted-foreground">
                      {useAI ? 'AI will automatically detect and extract fields' :
                       selectedSchema ? `Using ${selectedSchema} schema` :
                       'Please select a schema or use AI mode'}
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
          {currentStep === 'extract' && (
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
                      <p className="text-sm font-medium">AI Analysis in Progress</p>
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
          {currentStep === 'results' && extractionResult && (
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
                    <p className="text-sm font-medium break-all">{uploadedFile.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {extractionResult && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Document Type</span>
                        <Badge variant="outline">{extractionResult.documentType}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Fields Extracted</span>
                        <span className="font-medium">{extractionResult.extractedFields.length}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Confidence</span>
                        <Badge variant="default">
                          {Math.round((extractionResult.confidence || 0) * 100)}%
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Processing Time</span>
                        <span className="font-medium">{extractionResult.processingTime?.toFixed(2)}s</span>
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Quick Actions */}
          {currentStep === 'results' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => handleExport('json')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export as JSON
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => handleExport('csv')}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Export as CSV
                </Button>
                <Separator className="my-2" />
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={handleReset}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Process Another Document
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Tips */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-500" />
                Pro Tips
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-purple-500">•</span>
                  <span>AI mode works best for common document types</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-500">•</span>
                  <span>Use schemas for consistent extraction across similar documents</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-500">•</span>
                  <span>Review medium confidence fields before exporting</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-500">•</span>
                  <span>Hybrid mode combines schema structure with AI discovery</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
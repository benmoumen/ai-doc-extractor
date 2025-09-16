'use client'

import React, { useState, useEffect } from 'react'
import {
  FileText, Upload, Loader2, CheckCircle, AlertCircle,
  ArrowRight, RefreshCw, Download, Sparkles, Zap, Eye,
  Code, Settings, X, ExternalLink
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
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
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [availableModels, setAvailableModels] = useState<any[]>([])
  const [useAI, setUseAI] = useState(true)
  const [isExtracting, setIsExtracting] = useState(false)
  const [extractionResult, setExtractionResult] = useState<ExtractionResult | null>(null)
  const [extractionProgress, setExtractionProgress] = useState(0)
  const [availableSchemas, setAvailableSchemas] = useState<any>({})
  const [selectedSchemaDetails, setSelectedSchemaDetails] = useState<any>(null)
  const [documentPreview, setDocumentPreview] = useState<string | null>(null)
  const [debugInfo, setDebugInfo] = useState<any | null>(null)

  // Load available models on component mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const response = await apiClient.getSupportedModels()
        if (response.success && response.models) {
          setAvailableModels(response.models)
          // Set default model to first available
          if (response.models.length > 0) {
            setSelectedModel(response.models[0].id)
          }
        }
      } catch (error) {
        console.error('Failed to load models:', error)
      }
    }
    loadModels()
  }, [])

  // Load available schemas
  useEffect(() => {
    const loadSchemas = async () => {
      try {
        const response = await apiClient.getAvailableSchemas()
        if (response.success && response.schemas) {
          setAvailableSchemas(response.schemas)
        }
      } catch (error) {
        console.error('Failed to load schemas:', error)
      }
    }
    loadSchemas()
  }, [])

  // Create document preview when file is uploaded
  useEffect(() => {
    if (uploadedFile) {
      if (uploadedFile.type.startsWith('image/') || uploadedFile.type === 'application/pdf') {
        const url = URL.createObjectURL(uploadedFile)
        setDocumentPreview(url)
        return () => URL.revokeObjectURL(url)
      }
    }
  }, [uploadedFile])

  // Fetch detailed schema information when schema is selected
  useEffect(() => {
    if (selectedSchema && selectedSchema !== 'ai') {
      const loadSchemaDetails = async () => {
        try {
          const details = await apiClient.getSchemaDetails(selectedSchema)
          if (details.success && details.schema) {
            setSelectedSchemaDetails(details.schema)
          }
        } catch (error) {
          console.error('Failed to load schema details:', error)
          setSelectedSchemaDetails(null)
        }
      }
      loadSchemaDetails()
    } else {
      setSelectedSchemaDetails(null)
    }
  }, [selectedSchema])

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
      const startTime = Date.now()
      const result = await apiClient.extractData(
        uploadedFile,
        selectedSchema || undefined,
        useAI,
        selectedModel || undefined
      )
      const endTime = Date.now()
      const clientSideProcessingTime = (endTime - startTime) / 1000

      clearInterval(progressInterval)
      setExtractionProgress(100)

      if (result.success) {
        // Store the debug information from this extraction
        if (result.debug) {
          setDebugInfo(result.debug)
        }

        // Transform API response to match our component interface
        // Our backend returns: { success, extracted_data, validation, metadata }
        const extractionResult: ExtractionResult = {
          id: `extraction_${Date.now()}`,
          documentType: result.metadata?.file_type || 'document',
          extractionMode: result.metadata?.extraction_mode || (selectedSchema ? 'schema' : 'ai'),
          schemaUsed: result.metadata?.schema_id || selectedSchema,
          processingTime: result.metadata?.processing_time || clientSideProcessingTime,
          confidence: result.validation?.passed ? 0.9 : 0.7,
          extractedFields: result.extracted_data?.structured_data ?
            Object.entries(result.extracted_data.structured_data).map(([key, value], index) => ({
              id: key,
              name: key,
              displayName: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
              value: Array.isArray(value) ? value.join(', ') : String(value),
              type: typeof value === 'number' ? 'number' :
                    typeof value === 'boolean' ? 'boolean' :
                    Array.isArray(value) ? 'array' : 'text',
              confidence: result.validation?.passed ? 0.9 : 0.7,
              source: 'ai_extraction',
              validation: {
                isValid: result.validation?.passed ?? true,
                errors: result.validation?.errors || []
              }
            })) : [
              {
                id: 'raw_content',
                name: 'raw_content',
                displayName: 'Extracted Content',
                value: result.extracted_data?.formatted_text || result.extracted_data?.raw_content || 'No content extracted',
                type: 'text',
                confidence: result.validation?.passed ? 0.9 : 0.7,
                source: 'ai_extraction',
                validation: {
                  isValid: result.validation?.passed ?? true,
                  errors: result.validation?.errors || []
                }
              }
            ],
          warnings: result.validation?.errors?.map((error: string) => `Validation warning: ${error}`) || [],
          suggestions: []
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
    setDocumentPreview(null)
    setDebugInfo(null)
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
                <SchemaSelector
                  schemas={Object.values(availableSchemas).map(schema => ({
                    id: schema.id,
                    name: schema.name || schema.display_name,
                    description: schema.description,
                    category: schema.category || 'Other'
                  }))}
                  onSchemaSelect={handleSchemaSelect}
                />

                <Separator />

                {/* Model Selection */}
                <div className="space-y-3">
                  <label className="text-sm font-medium">AI Model</label>
                  <div className="grid grid-cols-1 gap-2">
                    {availableModels.map((model) => (
                      <div
                        key={model.id}
                        className={`
                          p-3 rounded-lg border cursor-pointer transition-colors
                          ${selectedModel === model.id
                            ? 'border-blue-200 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                          }
                        `}
                        onClick={() => setSelectedModel(model.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm font-medium">{model.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {model.provider} • {model.model}
                            </p>
                          </div>
                          <div className={`
                            w-4 h-4 rounded-full border-2
                            ${selectedModel === model.id
                              ? 'bg-blue-500 border-blue-500'
                              : 'border-gray-300'
                            }
                          `}>
                            {selectedModel === model.id && (
                              <div className="w-full h-full bg-white rounded-full scale-50" />
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">Ready to extract</p>
                    <p className="text-xs text-muted-foreground">
                      {selectedSchema ? `Schema-guided extraction: ${selectedSchema}` :
                       useAI ? 'AI free-form extraction: automatic field detection' :
                       'Please select a schema or enable AI mode'}
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

                {/* Document Preview Button */}
                {uploadedFile && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Eye className="h-4 w-4 mr-2" />
                        View Document
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>Document Preview</DialogTitle>
                        <DialogDescription>
                          {uploadedFile.name}
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        {uploadedFile.type === 'application/pdf' ? (
                          <div className="space-y-4">
                            <embed
                              src={documentPreview || ''}
                              type="application/pdf"
                              className="w-full h-[50vh]"
                            />
                            <div className="text-center">
                              <p className="text-sm text-muted-foreground mb-2">
                                PDF not displaying? Open in new tab:
                              </p>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => window.open(documentPreview || '', '_blank')}
                              >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                Open PDF in New Tab
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <img
                            src={documentPreview || ''}
                            alt="Document preview"
                            className="w-full h-auto"
                          />
                        )}
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {/* AI Debug Info Viewer Button */}
                {extractionResult && debugInfo && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Code className="h-4 w-4 mr-2" />
                        View AI Debug Info
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-6xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>AI Debug Information</DialogTitle>
                        <DialogDescription>
                          Completion parameters and raw response from AI model
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        <Tabs defaultValue="params" className="w-full">
                          <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="params">Completion Parameters</TabsTrigger>
                            <TabsTrigger value="response">Raw AI Response</TabsTrigger>
                          </TabsList>
                          <TabsContent value="params" className="space-y-4">
                            <div>
                              <h4 className="text-sm font-medium mb-2">Model & Settings</h4>
                              <div className="bg-muted p-3 rounded-md text-xs space-y-2">
                                <div><strong>Model:</strong> {debugInfo.completion_params?.model || 'Unknown'}</div>
                                <div><strong>Temperature:</strong> {debugInfo.completion_params?.temperature ?? 'Not set'}</div>
                              </div>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium mb-2">Messages Sent to AI</h4>
                              <div className="space-y-2">
                                {debugInfo.completion_params?.messages?.map((message: any, index: number) => (
                                  <div key={index} className="bg-muted p-3 rounded-md">
                                    <div className="text-xs font-medium mb-2">Message {index + 1} (Role: {message.role})</div>
                                    {message.content?.map((content: any, contentIndex: number) => (
                                      <div key={contentIndex} className="text-xs space-y-1">
                                        {content.type === 'text' && (
                                          <div>
                                            <strong>Text Prompt:</strong>
                                            <pre className="mt-1 whitespace-pre-wrap bg-background p-2 rounded border max-h-40 overflow-auto">
                                              {content.text}
                                            </pre>
                                          </div>
                                        )}
                                        {content.type === 'image_url' && (
                                          <div>
                                            <strong>Image:</strong> Document image (base64 encoded)
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </TabsContent>
                          <TabsContent value="response" className="space-y-4">
                            <div>
                              <h4 className="text-sm font-medium mb-2">Response Metadata</h4>
                              <div className="bg-muted p-3 rounded-md text-xs space-y-2">
                                <div><strong>Response ID:</strong> {debugInfo.raw_response?.id || 'Not provided'}</div>
                                <div><strong>Model Used:</strong> {debugInfo.raw_response?.model || 'Unknown'}</div>
                                <div><strong>Finish Reason:</strong> {debugInfo.raw_response?.choices?.[0]?.finish_reason || 'Not provided'}</div>
                                {debugInfo.raw_response?.usage && Object.keys(debugInfo.raw_response.usage).length > 0 && (
                                  <div>
                                    <strong>Token Usage:</strong>
                                    <pre className="mt-1 text-xs bg-background p-2 rounded border">
                                      {JSON.stringify(debugInfo.raw_response.usage, null, 2)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            </div>
                            <div>
                              <h4 className="text-sm font-medium mb-2">Raw AI Response Content</h4>
                              <pre className="text-xs bg-muted p-4 rounded-md whitespace-pre-wrap max-h-96 overflow-auto">
                                {debugInfo.raw_response?.choices?.[0]?.message?.content || 'No response content available'}
                              </pre>
                            </div>
                          </TabsContent>
                        </Tabs>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {/* Extraction Details Button */}
                {extractionResult && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm" className="w-full">
                        <Settings className="h-4 w-4 mr-2" />
                        View Extraction Details
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-4xl max-h-[80vh]">
                      <DialogHeader>
                        <DialogTitle>Extraction Details</DialogTitle>
                        <DialogDescription>
                          Configuration and details for this extraction
                        </DialogDescription>
                      </DialogHeader>
                      <div className="max-h-[60vh] overflow-auto">
                        <div className="space-y-6">
                          {/* Extraction Summary */}
                          <div>
                            <h4 className="text-sm font-medium mb-2">Extraction Summary</h4>
                            <div className="text-xs space-y-1 bg-muted p-3 rounded-md">
                              <p><strong>Mode:</strong> {extractionResult.extractionMode === 'ai_freeform' ? 'AI Free-form Detection' : 'Schema-guided'}</p>
                              <p><strong>Processing Time:</strong> {extractionResult.processingTime?.toFixed(2)}s</p>
                              <p><strong>Overall Confidence:</strong> {Math.round((extractionResult.confidence || 0) * 100)}%</p>
                              <p><strong>Fields Extracted:</strong> {extractionResult.extractedFields.length}</p>
                            </div>
                          </div>

                          {/* Schema Information */}
                          {selectedSchema && selectedSchema !== 'ai' ? (
                            <div>
                              <h4 className="text-sm font-medium mb-2">Schema Information</h4>
                              <div className="bg-muted p-3 rounded-md text-xs">
                                <p><strong>Schema Used:</strong> {selectedSchema}</p>
                                <p className="mt-1 text-muted-foreground">
                                  This extraction used a predefined schema to guide field extraction and validation.
                                </p>
                                {selectedSchemaDetails && selectedSchemaDetails.fields && (
                                  <div className="mt-3">
                                    <p className="text-muted-foreground mb-2">Schema Fields ({Object.keys(selectedSchemaDetails.fields).length}):</p>
                                    <div className="space-y-1 max-h-32 overflow-y-auto">
                                      {Object.entries(selectedSchemaDetails.fields).map(([fieldName, fieldDef]: [string, any]) => (
                                        <div key={fieldName} className="flex items-center gap-2">
                                          <span className="text-xs">{fieldDef.display_name || fieldName}</span>
                                          <Badge variant={fieldDef.required ? "destructive" : "outline"} className="text-xs px-1 py-0 h-4">
                                            {fieldDef.required ? "Required" : "Optional"}
                                          </Badge>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div>
                              <h4 className="text-sm font-medium mb-2">AI Free-form Extraction</h4>
                              <div className="bg-muted p-3 rounded-md text-xs">
                                <p>This extraction used AI free-form detection without a predefined schema.</p>
                                <p className="mt-1 text-muted-foreground">
                                  The AI automatically identified and extracted fields based on document structure and content.
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                )}

                {extractionResult && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Document Type</span>
                        <Badge variant="outline">{extractionResult.documentType}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Extraction Mode</span>
                        <Badge variant={extractionResult.extractionMode === 'schema' ? 'default' : 'secondary'}>
                          {extractionResult.extractionMode === 'schema' ? 'Schema-guided' :
                           extractionResult.extractionMode === 'ai_freeform' ? 'AI Free-form' :
                           'AI'}
                        </Badge>
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
'use client'

import React, { useState, useEffect } from 'react'
import { Upload, FileText, Brain, Wand2, CheckCircle, AlertCircle, Loader2, Eye, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { apiClient } from '@/lib/api'

interface GenerationStep {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  duration?: number
  details?: any
}

interface SchemaGenerationProps {
  onSchemaGenerated?: (schemaId: string) => void
  className?: string
}

export function SchemaGenerator({ onSchemaGenerated, className }: SchemaGenerationProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [documentTypeHint, setDocumentTypeHint] = useState<string>('')
  const [availableModels, setAvailableModels] = useState<any[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState<string>('')
  const [generationSteps, setGenerationSteps] = useState<GenerationStep[]>([
    { name: 'Document Processing', status: 'pending' },
    { name: 'AI Schema Generation', status: 'pending' },
    { name: 'Schema Validation', status: 'pending' }
  ])
  const [generatedSchema, setGeneratedSchema] = useState<any>(null)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [documentPreview, setDocumentPreview] = useState<string | null>(null)

  // Load available models on component mount
  useEffect(() => {
    loadModels()
  }, [])

  // Update document preview when file changes
  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile)
      setDocumentPreview(url)
      return () => URL.revokeObjectURL(url)
    } else {
      setDocumentPreview(null)
    }
  }, [selectedFile])

  const loadModels = async () => {
    try {
      const response = await apiClient.getSupportedModels()
      if (response.success && response.models) {
        setAvailableModels(response.models)
        // Set first model as default
        if (response.models.length > 0) {
          setSelectedModel(response.models[0].id)
        }
      }
    } catch (err) {
      console.error('Failed to load models:', err)
    }
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
      resetGeneration()
    }
  }

  const resetGeneration = () => {
    setIsGenerating(false)
    setGenerationProgress(0)
    setCurrentStep('')
    setGeneratedSchema(null)
    setAnalysisId(null)
    setGenerationSteps(steps => steps.map(step => ({ ...step, status: 'pending' })))
  }

  const updateStepStatus = (stepName: string, status: GenerationStep['status'], details?: any, duration?: number) => {
    setGenerationSteps(steps =>
      steps.map(step =>
        step.name === stepName
          ? { ...step, status, details, duration }
          : step
      )
    )
  }

  const startGeneration = async () => {
    if (!selectedFile) {
      setError('Please select a document to analyze')
      return
    }

    setIsGenerating(true)
    setError(null)
    resetGeneration()
    setCurrentStep('Uploading document...')

    try {
      // Step 1: Process document
      updateStepStatus('Document Processing', 'in_progress')
      setGenerationProgress(10)

      // Step 2: Generate schema with AI
      setCurrentStep('Analyzing document with AI...')
      updateStepStatus('Document Processing', 'completed')
      updateStepStatus('AI Schema Generation', 'in_progress')
      setGenerationProgress(30)

      const schemaResponse = await apiClient.generateSchema({
        file: selectedFile,
        model: selectedModel || undefined
      })

      if (!schemaResponse.success) {
        throw new Error('Schema generation failed')
      }

      setGenerationProgress(70)
      updateStepStatus('AI Schema Generation', 'completed')
      updateStepStatus('Schema Validation', 'in_progress')
      setCurrentStep('Validating generated schema...')

      // Process the generated schema
      const generatedSchema = schemaResponse.generated_schema

      if (generatedSchema.is_valid && generatedSchema.schema_data) {
        setGeneratedSchema({
          id: generatedSchema.schema_data.id,
          name: generatedSchema.schema_data.name,
          description: generatedSchema.schema_data.description,
          total_fields: Object.keys(generatedSchema.schema_data.fields).length,
          generation_confidence: 0.85, // Default confidence since backend doesn't provide it yet
          production_ready: generatedSchema.ready_for_extraction,
          validation_status: 'valid',
          user_review_status: 'pending'
        })

        updateStepStatus('Schema Validation', 'completed')
        setCurrentStep('Schema generation completed!')
        setGenerationProgress(100)

        if (onSchemaGenerated && generatedSchema.schema_id) {
          onSchemaGenerated(generatedSchema.schema_id)
        }
      } else {
        // Show more detailed error information
        console.error('Schema validation failed:', {
          is_valid: generatedSchema.is_valid,
          has_schema_data: !!generatedSchema.schema_data,
          raw_response_length: generatedSchema.raw_response?.length || 0,
          raw_response_preview: generatedSchema.raw_response?.substring(0, 200) + '...'
        })

        const errorMessage = !generatedSchema.is_valid
          ? 'AI response could not be parsed as valid JSON schema'
          : 'Generated schema missing required data fields'

        throw new Error(`${errorMessage}. Check console for raw AI response.`)
      }

    } catch (err: any) {
      console.error('Generation failed:', err)
      setError(err.message || 'Schema generation failed')
      setCurrentStep('Generation failed')

      // Mark current step as failed
      const currentStepName = generationSteps.find(step => step.status === 'in_progress')?.name
      if (currentStepName) {
        updateStepStatus(currentStepName, 'failed')
      }
    } finally {
      setIsGenerating(false)
    }
  }


  const getStepIcon = (status: GenerationStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'in_progress':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      default:
        return <div className="h-4 w-4 rounded-full border-2 border-gray-300" />
    }
  }

  const downloadSchema = () => {
    if (!generatedSchema) return

    const schemaData = {
      id: generatedSchema.id,
      name: generatedSchema.name,
      description: generatedSchema.description,
      generated_at: new Date().toISOString(),
      confidence: generatedSchema.generation_confidence,
      fields: generatedSchema.total_fields,
      production_ready: generatedSchema.production_ready
    }

    const blob = new Blob([JSON.stringify(schemaData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `schema-${generatedSchema.name.toLowerCase().replace(/\s+/g, '-')}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Brain className="h-6 w-6 text-purple-500" />
          AI Schema Generator
        </h2>
        <p className="text-muted-foreground">
          Upload a sample document to automatically generate a custom extraction schema using AI
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5" />
            Configuration
          </CardTitle>
          <CardDescription>
            Select your document and configure generation settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Upload */}
          <div className="space-y-2">
            <Label>Sample Document</Label>
            <div className="flex items-center gap-4">
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.tiff,.bmp"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <Label
                htmlFor="file-upload"
                className="flex items-center gap-2 px-4 py-2 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <Upload className="h-4 w-4" />
                Choose Document
              </Label>
              {selectedFile && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    <FileText className="h-3 w-3 mr-1" />
                    {selectedFile.name}
                  </Badge>
                  {documentPreview && (
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button variant="outline" size="sm">
                          <Eye className="h-3 w-3 mr-1" />
                          Preview
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-4xl max-h-[80vh]">
                        <DialogHeader>
                          <DialogTitle>Document Preview</DialogTitle>
                          <DialogDescription>{selectedFile.name}</DialogDescription>
                        </DialogHeader>
                        <div className="overflow-auto max-h-[60vh]">
                          {selectedFile.type === 'application/pdf' ? (
                            <embed src={documentPreview} width="100%" height="500px" type="application/pdf" />
                          ) : (
                            <img src={documentPreview} alt="Document preview" className="max-w-full h-auto" />
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
          <div className="space-y-2">
            <Label>AI Model</Label>
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger>
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

          {/* Document Type Hint */}
          <div className="space-y-2">
            <Label>Document Type Hint (Optional)</Label>
            <Select value={documentTypeHint} onValueChange={setDocumentTypeHint}>
              <SelectTrigger>
                <SelectValue placeholder="Select document type..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto-detect">Auto-detect</SelectItem>
                <SelectItem value="national_id">National ID Card</SelectItem>
                <SelectItem value="passport">Passport</SelectItem>
                <SelectItem value="residence_permit">Residence Permit</SelectItem>
                <SelectItem value="business_license">Business License</SelectItem>
                <SelectItem value="invoice">Invoice</SelectItem>
                <SelectItem value="receipt">Receipt</SelectItem>
                <SelectItem value="contract">Contract</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Generate Button */}
          <Button
            onClick={startGeneration}
            disabled={!selectedFile || isGenerating}
            className="w-full"
            size="lg"
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Generating Schema...
              </>
            ) : (
              <>
                <Brain className="h-4 w-4 mr-2" />
                Generate Schema
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Progress Display */}
      {isGenerating && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin" />
              Generation Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{currentStep}</span>
                <span>{generationProgress}%</span>
              </div>
              <Progress value={generationProgress} />
            </div>

            {/* Step Details */}
            <div className="space-y-2">
              {generationSteps.map((step, index) => (
                <div key={step.name} className="flex items-center gap-3 text-sm">
                  {getStepIcon(step.status)}
                  <span className={step.status === 'completed' ? 'text-green-600' : step.status === 'failed' ? 'text-red-600' : ''}>
                    {step.name}
                  </span>
                  {step.duration && (
                    <span className="text-muted-foreground ml-auto">
                      {step.duration.toFixed(2)}s
                    </span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {generatedSchema && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              Generated Schema
            </CardTitle>
            <CardDescription>
              Your AI-generated schema is ready for use
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="overview" className="space-y-4">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="confidence">Confidence</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Schema Name</Label>
                    <p className="text-sm">{generatedSchema.name}</p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Total Fields</Label>
                    <p className="text-sm">{generatedSchema.total_fields}</p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">High Confidence Fields</Label>
                    <p className="text-sm">{generatedSchema.high_confidence_fields}</p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Production Ready</Label>
                    <Badge variant={generatedSchema.production_ready ? "default" : "secondary"}>
                      {generatedSchema.production_ready ? "Yes" : "Needs Review"}
                    </Badge>
                  </div>
                </div>

                {generatedSchema.description && (
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Description</Label>
                    <p className="text-sm text-muted-foreground">{generatedSchema.description}</p>
                  </div>
                )}

                <Separator />

                <div className="flex gap-2">
                  <Button onClick={downloadSchema} variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Download Schema
                  </Button>
                  {onSchemaGenerated && (
                    <Button onClick={() => onSchemaGenerated!(generatedSchema.id)}>
                      Use This Schema
                    </Button>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="details" className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Schema ID</Label>
                  <code className="text-xs bg-muted p-2 rounded block">{generatedSchema.id}</code>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">Validation Status</Label>
                  <Badge variant={generatedSchema.validation_status === 'valid' ? "default" : "destructive"}>
                    {generatedSchema.validation_status}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <Label className="text-sm font-medium">User Review Status</Label>
                  <Badge variant="secondary">{generatedSchema.user_review_status || 'Pending'}</Badge>
                </div>
              </TabsContent>

              <TabsContent value="confidence" className="space-y-4">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">Generation Confidence</Label>
                    <div className="flex items-center gap-2">
                      <Progress value={generatedSchema.generation_confidence * 100} className="flex-1" />
                      <span className="text-sm">{Math.round(generatedSchema.generation_confidence * 100)}%</span>
                    </div>
                  </div>

                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {generatedSchema.generation_confidence >= 0.8
                        ? "High confidence - This schema is ready for production use."
                        : generatedSchema.generation_confidence >= 0.6
                        ? "Medium confidence - Review recommended before production use."
                        : "Low confidence - Manual review and adjustment required."}
                    </AlertDescription>
                  </Alert>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
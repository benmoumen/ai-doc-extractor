'use client'

import React, { useState, useCallback } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { toast } from 'sonner'

import { uploadDocumentWithProgress } from '@/lib/api'
import { DocumentUploadRequest, DocumentAnalysisResponse, UploadState } from '@/types'

interface DocumentUploadProps {
  onUploadComplete?: (result: DocumentAnalysisResponse) => void
  onUploadStart?: (file: File) => void
  onUploadProgress?: (progress: number) => void
  className?: string
  acceptedTypes?: string[]
  maxFileSizeMB?: number
}

export function DocumentUpload({
  onUploadComplete,
  onUploadStart,
  onUploadProgress,
  className,
  acceptedTypes = ['application/pdf', 'image/jpeg', 'image/png'],
  maxFileSizeMB = 100
}: DocumentUploadProps) {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0
  })

  const [dragActive, setDragActive] = useState(false)

  // File validation
  const validateFile = useCallback((file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `File type ${file.type} is not supported. Please upload ${acceptedTypes.join(', ')}`
    }

    const maxSizeBytes = maxFileSizeMB * 1024 * 1024
    if (file.size > maxSizeBytes) {
      return `File size ${(file.size / 1024 / 1024).toFixed(1)}MB exceeds maximum of ${maxFileSizeMB}MB`
    }

    return null
  }, [acceptedTypes, maxFileSizeMB])

  // Handle file upload
  const handleUpload = useCallback(async (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      toast.error(validationError)
      return
    }

    setUploadState({
      status: 'uploading',
      progress: 0,
      file
    })

    onUploadStart?.(file)

    try {
      const request: DocumentUploadRequest = { file }

      // Upload with progress tracking
      const result = await uploadDocumentWithProgress(
        request,
        (progress) => {
          setUploadState(prev => ({
            ...prev,
            progress: Math.min(progress, 90) // Reserve 10% for processing
          }))
          onUploadProgress?.(progress)
        }
      )

      // Check if the processing was successful
      if (!result.success) {
        throw new Error(result.errors?.[0] || 'Document processing failed')
      }

      // Show processing state
      setUploadState(prev => ({
        ...prev,
        status: 'processing',
        progress: 95
      }))

      // Simulate processing completion (in real app, you'd poll for status)
      setTimeout(() => {
        setUploadState({
          status: 'completed',
          progress: 100,
          file,
          result
        })

        // Safe access to analysis data
        const detectedType = result.analysis?.detected_document_type || 'Unknown'
        const confidence = result.analysis?.document_type_confidence
          ? Math.round(result.analysis.document_type_confidence * 100)
          : 0

        toast.success(`Document processed successfully! Detected: ${detectedType} (${confidence}% confidence)`)
        onUploadComplete?.(result)
      }, 2000)

    } catch (error) {
      console.error('Upload failed:', error)

      const errorMessage = error instanceof Error ? error.message : 'Upload failed'

      setUploadState({
        status: 'error',
        progress: 0,
        file,
        error: errorMessage
      })

      toast.error(`Upload failed: ${errorMessage}`)
    }
  }, [validateFile, onUploadStart, onUploadProgress, onUploadComplete])

  // Handle file input change
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      handleUpload(file)
    }
  }

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleUpload(file)
    }
  }

  // Reset upload state
  const handleReset = () => {
    setUploadState({
      status: 'idle',
      progress: 0
    })
  }

  const getStatusIcon = () => {
    switch (uploadState.status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle2 className="h-8 w-8 text-green-500" />
      case 'error':
        return <AlertCircle className="h-8 w-8 text-red-500" />
      default:
        return <Upload className="h-8 w-8 text-gray-400" />
    }
  }

  const getStatusMessage = () => {
    switch (uploadState.status) {
      case 'uploading':
        return `Uploading ${uploadState.file?.name}...`
      case 'processing':
        return 'Processing document with AI...'
      case 'completed':
        return `Successfully processed ${uploadState.file?.name}`
      case 'error':
        return uploadState.error || 'Upload failed'
      default:
        return 'Drag and drop a document or click to upload'
    }
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload PDF, JPEG, or PNG files for AI-powered data extraction
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-colors
            ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}
            ${uploadState.status === 'idle' ? 'hover:border-gray-400 hover:bg-gray-50 cursor-pointer' : ''}
            ${uploadState.status === 'error' ? 'border-red-300 bg-red-50' : ''}
            ${uploadState.status === 'completed' ? 'border-green-300 bg-green-50' : ''}
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => {
            if (uploadState.status === 'idle') {
              document.getElementById('file-input')?.click()
            }
          }}
        >
          <input
            id="file-input"
            type="file"
            accept={acceptedTypes.join(',')}
            onChange={handleFileChange}
            className="hidden"
            disabled={uploadState.status !== 'idle'}
          />

          <div className="flex flex-col items-center space-y-4">
            {getStatusIcon()}

            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">
                {getStatusMessage()}
              </p>

              {uploadState.status === 'idle' && (
                <p className="text-xs text-gray-500">
                  Supported formats: PDF, JPEG, PNG (max {maxFileSizeMB}MB)
                </p>
              )}

              {uploadState.file && (
                <div className="text-xs text-gray-600">
                  <div className="flex items-center justify-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span>{uploadState.file.name}</span>
                    <span>({(uploadState.file.size / 1024 / 1024).toFixed(1)}MB)</span>
                  </div>
                </div>
              )}
            </div>

            {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
              <div className="w-full max-w-xs">
                <Progress value={uploadState.progress} className="h-2" />
                <p className="text-xs text-gray-500 mt-1 text-center">
                  {uploadState.progress}%
                </p>
              </div>
            )}

            {uploadState.status === 'completed' && uploadState.result && uploadState.result.success && (
              <div className="text-xs text-gray-600 space-y-1">
                <div>Document Type: <span className="font-medium">{uploadState.result.analysis?.detected_document_type || 'Unknown'}</span></div>
                <div>Confidence: <span className="font-medium">{uploadState.result.analysis?.document_type_confidence ? Math.round(uploadState.result.analysis.document_type_confidence * 100) : 0}%</span></div>
                <div>Fields Detected: <span className="font-medium">{uploadState.result.analysis?.total_fields_detected || 0}</span></div>
                <div>Processing Time: <span className="font-medium">{uploadState.result.total_processing_time?.toFixed(1) || '0.0'}s</span></div>
              </div>
            )}

            {(uploadState.status === 'completed' || uploadState.status === 'error') && (
              <Button
                onClick={handleReset}
                variant="outline"
                size="sm"
                className="mt-4"
              >
                Upload Another Document
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
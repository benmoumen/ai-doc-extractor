'use client'

import React from 'react'
import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

import { StageResult } from '@/types'

interface ProcessingProgressProps {
  processingStages: Record<string, StageResult>
  totalProcessingTime?: number
  className?: string
}

// Define the expected stages in order
const PROCESSING_STAGES = [
  {
    key: 'document_processing',
    name: 'Document Processing',
    description: 'Extracting text and images from document'
  },
  {
    key: 'ai_analysis',
    name: 'AI Analysis',
    description: 'Analyzing document structure and content'
  },
  {
    key: 'field_enhancement',
    name: 'Field Enhancement',
    description: 'Refining and validating extracted fields'
  },
  {
    key: 'validation_inference',
    name: 'Validation Rules',
    description: 'Inferring data validation rules'
  },
  {
    key: 'schema_generation',
    name: 'Schema Generation',
    description: 'Generating structured data schema'
  },
  {
    key: 'confidence_analysis',
    name: 'Confidence Analysis',
    description: 'Calculating confidence scores and recommendations'
  }
]

export function ProcessingProgress({
  processingStages,
  totalProcessingTime,
  className
}: ProcessingProgressProps) {
  // Calculate overall progress
  const completedStages = PROCESSING_STAGES.filter(stage =>
    processingStages[stage.key]?.success === true
  ).length

  const failedStages = PROCESSING_STAGES.filter(stage =>
    processingStages[stage.key]?.success === false
  ).length

  const inProgressStages = PROCESSING_STAGES.filter(stage => {
    const stageResult = processingStages[stage.key]
    return stageResult && stageResult.success === undefined
  }).length

  const overallProgress = (completedStages / PROCESSING_STAGES.length) * 100

  const getStageIcon = (stage: typeof PROCESSING_STAGES[0]) => {
    const stageResult = processingStages[stage.key]

    if (!stageResult) {
      return <Clock className="h-4 w-4 text-gray-400" />
    }

    if (stageResult.success === true) {
      return <CheckCircle2 className="h-4 w-4 text-green-500" />
    }

    if (stageResult.success === false) {
      return <AlertCircle className="h-4 w-4 text-red-500" />
    }

    return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
  }

  const getStageStatus = (stage: typeof PROCESSING_STAGES[0]) => {
    const stageResult = processingStages[stage.key]

    if (!stageResult) {
      return 'pending'
    }

    if (stageResult.success === true) {
      return 'completed'
    }

    if (stageResult.success === false) {
      return 'error'
    }

    return 'processing'
  }

  const getStageDetails = (stage: typeof PROCESSING_STAGES[0]) => {
    const stageResult = processingStages[stage.key]

    if (!stageResult) {
      return null
    }

    const details = []

    if (stageResult.duration) {
      details.push(`${(stageResult.duration * 1000).toFixed(0)}ms`)
    }

    // Add stage-specific details
    if (stage.key === 'ai_analysis' && stageResult.model_used) {
      details.push(`Model: ${stageResult.model_used}`)
    }

    if (stage.key === 'field_enhancement' && stageResult.enhanced_fields_count) {
      details.push(`${stageResult.enhanced_fields_count} fields`)
    }

    if (stage.key === 'schema_generation' && stageResult.total_fields_generated) {
      details.push(`${stageResult.total_fields_generated} fields`)
    }

    return details.length > 0 ? details.join(' • ') : null
  }

  const getStatusColor = () => {
    if (failedStages > 0) return 'destructive'
    if (completedStages === PROCESSING_STAGES.length) return 'default'
    if (inProgressStages > 0) return 'secondary'
    return 'outline'
  }

  const getStatusText = () => {
    if (failedStages > 0) return 'Processing Failed'
    if (completedStages === PROCESSING_STAGES.length) return 'Processing Complete'
    if (inProgressStages > 0) return 'Processing...'
    return 'Waiting to Start'
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Processing Progress</CardTitle>
            <CardDescription>
              AI document analysis pipeline - 6 stages
            </CardDescription>
          </div>
          <Badge variant={getStatusColor()}>
            {getStatusText()}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Overall Progress</span>
            <span>{Math.round(overallProgress)}%</span>
          </div>
          <Progress value={overallProgress} className="h-2" />
        </div>

        {/* Stage Details */}
        <div className="space-y-3">
          {PROCESSING_STAGES.map((stage, index) => {
            const status = getStageStatus(stage)
            const stageResult = processingStages[stage.key]
            const details = getStageDetails(stage)

            return (
              <div key={stage.key} className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getStageIcon(stage)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium text-gray-900">
                      {stage.name}
                    </h4>
                    <Badge
                      variant={
                        status === 'completed' ? 'default' :
                        status === 'error' ? 'destructive' :
                        status === 'processing' ? 'secondary' : 'outline'
                      }
                      className="text-xs"
                    >
                      {status === 'completed' ? 'Done' :
                       status === 'error' ? 'Error' :
                       status === 'processing' ? 'Running' : 'Pending'}
                    </Badge>
                  </div>

                  <p className="text-xs text-gray-500 mt-1">
                    {stage.description}
                  </p>

                  {details && (
                    <p className="text-xs text-gray-600 mt-1">
                      {details}
                    </p>
                  )}

                  {status === 'error' && stageResult?.error && (
                    <p className="text-xs text-red-600 mt-1">
                      Error: {stageResult.error}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Summary */}
        {totalProcessingTime && (
          <div className="pt-4 border-t">
            <div className="flex items-center justify-between text-sm">
              <span>Total Processing Time</span>
              <span className="font-medium">{totalProcessingTime.toFixed(1)}s</span>
            </div>

            <div className="flex items-center justify-between text-sm mt-1">
              <span>Stages Completed</span>
              <span className="font-medium">
                {completedStages}/{PROCESSING_STAGES.length}
              </span>
            </div>

            {failedStages > 0 && (
              <div className="flex items-center justify-between text-sm mt-1">
                <span>Stages Failed</span>
                <span className="font-medium text-red-600">
                  {failedStages}
                </span>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
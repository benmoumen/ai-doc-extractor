"use client";

import React, { useState, useCallback, useRef, useEffect } from "react";
import {
  Upload,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Shield,
  AlertTriangle,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

import { uploadDocumentWithProgress } from "@/lib/api";
import { DocumentUploadRequest, DocumentAnalysisResponse } from "@/types";

interface DocumentUploaderProps {
  onUploadComplete?: (result: DocumentAnalysisResponse) => void;
  onUploadStart?: (file: File) => void;
  onUploadProgress?: (progress: number) => void;
  className?: string;
  acceptedTypes?: string[];
  maxFileSizeMB?: number;
  enableSecurityCheck?: boolean;
  enableDragDrop?: boolean;
}

interface UploadState {
  status: "idle" | "uploading" | "processing" | "completed" | "error";
  progress: number;
  file?: File;
  result?: DocumentAnalysisResponse;
  error?: string;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export function DocumentUploader({
  onUploadComplete,
  onUploadStart,
  onUploadProgress,
  className,
  acceptedTypes = ["application/pdf", "image/jpeg", "image/png"],
  maxFileSizeMB = 10,
  enableSecurityCheck = true,
  enableDragDrop = true,
}: DocumentUploaderProps) {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: "idle",
    progress: 0,
  });

  const [dragActive, setDragActive] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // File validation with security checks
  const validateFile = useCallback(
    (file: File): ValidationResult => {
      const result: ValidationResult = {
        isValid: true,
        errors: [],
        warnings: [],
      };

      // Check file type
      if (!acceptedTypes.includes(file.type)) {
        result.errors.push(
          `File type "${file.type}" is not supported. Accepted types: ${acceptedTypes
            .map(t => t.split("/")[1].toUpperCase())
            .join(", ")}`
        );
        result.isValid = false;
      }

      // Check file size
      const maxSizeBytes = maxFileSizeMB * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        result.errors.push(
          `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds maximum of ${maxFileSizeMB}MB`
        );
        result.isValid = false;
      }

      // Check minimum size
      if (file.size < 100) {
        result.errors.push("File appears to be empty or corrupted");
        result.isValid = false;
      }

      // Security checks
      if (enableSecurityCheck) {
        // Check for suspicious file names
        const suspiciousPatterns = [
          /\.\./,  // Directory traversal
          /[<>:"\/\\|?*\x00-\x1f]/,  // Invalid characters
          /\.(exe|bat|cmd|com|pif|scr|vbs|js)$/i,  // Executable extensions
        ];

        for (const pattern of suspiciousPatterns) {
          if (pattern.test(file.name)) {
            result.warnings.push(
              "File name contains potentially unsafe characters"
            );
          }
        }

        // Check for excessively long file names
        if (file.name.length > 255) {
          result.errors.push("File name is too long (max 255 characters)");
          result.isValid = false;
        }

        // Validate file extension matches MIME type
        const extension = file.name.split('.').pop()?.toLowerCase();
        const expectedExtensions: Record<string, string[]> = {
          'application/pdf': ['pdf'],
          'image/jpeg': ['jpg', 'jpeg'],
          'image/png': ['png'],
        };

        const validExtensions = expectedExtensions[file.type];
        if (validExtensions && extension && !validExtensions.includes(extension)) {
          result.warnings.push(
            `File extension ".${extension}" doesn't match file type`
          );
        }
      }

      // Performance warning for large files
      if (file.size > 5 * 1024 * 1024) {
        result.warnings.push(
          "Large file detected. Upload may take longer."
        );
      }

      return result;
    },
    [acceptedTypes, maxFileSizeMB, enableSecurityCheck]
  );

  // Handle file upload
  const handleUpload = useCallback(
    async (file: File) => {
      // Reset previous validation
      setValidationResult(null);

      // Validate file
      const validation = validateFile(file);
      setValidationResult(validation);

      if (!validation.isValid) {
        validation.errors.forEach(error => {
          toast.error(error);
        });
        return;
      }

      // Show warnings if any
      validation.warnings.forEach(warning => {
        toast.warning(warning);
      });

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      setUploadState({
        status: "uploading",
        progress: 0,
        file,
      });

      onUploadStart?.(file);

      try {
        const request: DocumentUploadRequest = { file };

        // Upload with progress tracking
        const result = await uploadDocumentWithProgress(
          request,
          (progress) => {
            setUploadState((prev) => ({
              ...prev,
              progress: Math.min(progress, 90), // Reserve 10% for server processing
            }));
            onUploadProgress?.(progress);
          }
        );

        // Check if upload was successful
        if (!result.success) {
          throw new Error(
            result.errors?.[0] || "Document upload failed"
          );
        }

        // Show processing state briefly
        setUploadState((prev) => ({
          ...prev,
          status: "processing",
          progress: 95,
        }));

        // Complete upload
        setTimeout(() => {
          setUploadState({
            status: "completed",
            progress: 100,
            file,
            result,
          });

          toast.success("Document uploaded successfully!");
          onUploadComplete?.(result);
        }, 500);
      } catch (error) {
        console.error("Upload failed:", error);

        let errorMessage = "Upload failed";
        let errorDetails = "";

        if (error instanceof Error) {
          errorMessage = error.message;

          // Parse specific error types
          if (error.message.includes("413")) {
            errorMessage = "File too large";
            errorDetails = "The file exceeds the server's maximum upload size";
          } else if (error.message.includes("415")) {
            errorMessage = "Unsupported file type";
            errorDetails = "The server doesn't support this file format";
          } else if (error.message.includes("429")) {
            errorMessage = "Too many requests";
            errorDetails = "Please wait a moment before uploading another file";
          } else if (error.message.includes("503")) {
            errorMessage = "Service temporarily unavailable";
            errorDetails = "The service is currently overloaded. Please try again later";
          }
        }

        setUploadState({
          status: "error",
          progress: 0,
          file,
          error: errorMessage,
        });

        toast.error(
          errorDetails ? `${errorMessage}: ${errorDetails}` : errorMessage
        );
      } finally {
        abortControllerRef.current = null;
      }
    },
    [
      validateFile,
      onUploadStart,
      onUploadProgress,
      onUploadComplete,
    ]
  );

  // Cancel upload
  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      toast.info("Upload cancelled");
    }

    setUploadState({
      status: "idle",
      progress: 0,
    });
    setValidationResult(null);
  }, []);

  // Handle file input change
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
    // Reset input to allow re-selecting the same file
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Handle drag and drop
  const handleDragOver = (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    e.preventDefault();
    setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    if (!enableDragDrop) return;
    e.preventDefault();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  // Reset upload state
  const handleReset = () => {
    setUploadState({
      status: "idle",
      progress: 0,
    });
    setValidationResult(null);
  };

  const getStatusIcon = () => {
    switch (uploadState.status) {
      case "uploading":
      case "processing":
        return <Loader2 className="h-8 w-8 animate-spin text-blue-500" />;
      case "completed":
        return <CheckCircle2 className="h-8 w-8 text-green-500" />;
      case "error":
        return <AlertCircle className="h-8 w-8 text-red-500" />;
      default:
        return enableSecurityCheck ? (
          <Shield className="h-8 w-8 text-gray-400" />
        ) : (
          <Upload className="h-8 w-8 text-gray-400" />
        );
    }
  };

  const getStatusMessage = () => {
    switch (uploadState.status) {
      case "uploading":
        return `Uploading ${uploadState.file?.name}...`;
      case "processing":
        return "Processing document...";
      case "completed":
        return `Successfully uploaded ${uploadState.file?.name}`;
      case "error":
        return uploadState.error || "Upload failed";
      default:
        return enableDragDrop
          ? "Drag and drop a document or click to upload"
          : "Click to select a document";
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload PDF or image files for processing
          {enableSecurityCheck && (
            <Badge variant="outline" className="ml-2">
              <Shield className="h-3 w-3 mr-1" />
              Secure Upload
            </Badge>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Validation warnings */}
        {validationResult && validationResult.warnings.length > 0 && (
          <Alert className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              {validationResult.warnings.map((warning, idx) => (
                <div key={idx} className="text-sm">
                  {warning}
                </div>
              ))}
            </AlertDescription>
          </Alert>
        )}

        {/* Upload area */}
        <div
          className={`
            border-2 border-dashed rounded-lg p-8 text-center transition-all
            ${dragActive ? "border-blue-500 bg-blue-50" : "border-gray-300"}
            ${
              uploadState.status === "idle"
                ? "hover:border-gray-400 hover:bg-gray-50 cursor-pointer"
                : ""
            }
            ${uploadState.status === "error" ? "border-red-300 bg-red-50" : ""}
            ${
              uploadState.status === "completed"
                ? "border-green-300 bg-green-50"
                : ""
            }
          `}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => {
            if (uploadState.status === "idle") {
              fileInputRef.current?.click();
            }
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={acceptedTypes.join(",")}
            onChange={handleFileChange}
            className="hidden"
            disabled={uploadState.status !== "idle"}
          />

          <div className="flex flex-col items-center space-y-4">
            {getStatusIcon()}

            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">
                {getStatusMessage()}
              </p>

              {uploadState.status === "idle" && (
                <p className="text-xs text-gray-500">
                  Supported formats: {acceptedTypes
                    .map(t => t.split("/")[1].toUpperCase())
                    .join(", ")} (max {maxFileSizeMB}MB)
                </p>
              )}

              {uploadState.file && (
                <div className="text-xs text-gray-600">
                  <div className="flex items-center justify-center space-x-2">
                    <FileText className="h-4 w-4" />
                    <span className="font-medium">{uploadState.file.name}</span>
                    <span className="text-gray-400">
                      ({(uploadState.file.size / 1024 / 1024).toFixed(1)}MB)
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Progress bar */}
            {(uploadState.status === "uploading" ||
              uploadState.status === "processing") && (
              <div className="w-full max-w-xs space-y-2">
                <Progress value={uploadState.progress} className="h-2" />
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>{uploadState.progress}%</span>
                  {uploadState.status === "uploading" && (
                    <Button
                      onClick={handleCancel}
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Cancel
                    </Button>
                  )}
                </div>
              </div>
            )}

            {/* Success info */}
            {uploadState.status === "completed" &&
              uploadState.result &&
              uploadState.result.success && (
                <div className="text-xs text-gray-600 bg-white/50 p-3 rounded">
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                    <div>Document ID:</div>
                    <div className="font-medium font-mono text-[10px]">
                      {uploadState.result.document?.id?.slice(0, 8)}...
                    </div>
                    <div>File Size:</div>
                    <div className="font-medium">
                      {uploadState.result.document?.file_size
                        ? (uploadState.result.document.file_size / 1024 / 1024).toFixed(1)
                        : '0'}MB
                    </div>
                    <div>Status:</div>
                    <div className="font-medium text-green-600">
                      Uploaded
                    </div>
                  </div>
                </div>
              )}

            {/* Action buttons */}
            {(uploadState.status === "completed" ||
              uploadState.status === "error") && (
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
  );
}
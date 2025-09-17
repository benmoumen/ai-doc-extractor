"use client";

import React, { useState } from "react";
import {
  Copy,
  Download,
  Check,
  Edit2,
  Save,
  X,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  Sparkles,
  Shield,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export interface ExtractedField {
  id: string;
  name: string;
  displayName: string;
  value: unknown;
  type: "string" | "number" | "date" | "boolean" | "array" | "object";
  confidence?: number;
  source?: "schema" | "ai";
  validation?: {
    isValid: boolean;
    errors?: string[];
  };
  metadata?: {
    originalValue?: unknown;
    pageNumber?: number;
    boundingBox?: unknown;
    alternatives?: unknown[];
  };
}

export interface DocumentVerification {
  document_type_confidence?: number;
  expected_document_type?: string;
  detected_document_type?: string;
  authenticity_score?: number;
  tampering_indicators?: {
    photo_manipulation?: boolean;
    text_alterations?: boolean;
    structural_anomalies?: boolean;
    digital_artifacts?: boolean;
    font_inconsistencies?: boolean;
  };
  security_checks?: {
    mrz_checksum_valid?: boolean;
    field_consistency?: boolean;
    date_logic_valid?: boolean;
    format_compliance?: boolean;
  };
  verification_notes?: string[];
  risk_level?: "low" | "medium" | "high";
}

export interface ExtractionResult {
  id: string;
  documentType?: string;
  extractedFields: ExtractedField[];
  processingTime?: number;
  confidence?: number;
  schemaUsed?: string;
  extractionMode?: "schema" | "ai";
  warnings?: string[];
  suggestions?: string[];
  verification?: DocumentVerification;
}

interface ExtractionResultsProps {
  result: ExtractionResult;
  onFieldUpdate?: (fieldId: string, newValue: unknown) => void;
  onExport?: (format: "json" | "csv" | "excel") => void;
  className?: string;
}

export function ExtractionResults({
  result,
  onFieldUpdate,
  onExport,
  className,
}: ExtractionResultsProps) {
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, unknown>>({});
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    new Set(["all"])
  );
  const [viewMode, setViewMode] = useState<
    "table" | "json" | "grouped" | "verification"
  >("table");

  // Group fields by confidence level
  const groupedFields = {
    high: result.extractedFields.filter((f) => (f.confidence || 0) >= 0.8),
    medium: result.extractedFields.filter(
      (f) => (f.confidence || 0) >= 0.5 && (f.confidence || 0) < 0.8
    ),
    low: result.extractedFields.filter((f) => (f.confidence || 0) < 0.5),
    unverified: result.extractedFields.filter(
      (f) => f.confidence === undefined
    ),
  };

  const handleEdit = (field: ExtractedField) => {
    setEditingField(field.id);
    setEditValues({ [field.id]: field.value });
  };

  const handleSave = (field: ExtractedField) => {
    const newValue = editValues[field.id];
    if (onFieldUpdate) {
      onFieldUpdate(field.id, newValue);
    }
    setEditingField(null);
    toast.success(`Updated ${field.displayName}`);
  };

  const handleCancel = () => {
    setEditingField(null);
    setEditValues({});
  };

  const handleCopy = async (field: ExtractedField) => {
    try {
      await navigator.clipboard.writeText(String(field.value));
      setCopiedField(field.id);
      setTimeout(() => setCopiedField(null), 2000);
      toast.success("Copied to clipboard");
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      toast.error("Failed to copy");
    }
  };

  const handleCopyAll = async () => {
    const data = result.extractedFields.reduce<Record<string, unknown>>(
      (acc, field) => {
        acc[field.name] = field.value;
        return acc;
      },
      {}
    );

    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
      toast.success("All data copied to clipboard");
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      toast.error("Failed to copy data");
    }
  };

  const toggleGroup = (group: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group)) {
      newExpanded.delete(group);
    } else {
      newExpanded.add(group);
    }
    setExpandedGroups(newExpanded);
  };

  const getConfidenceBadge = (confidence?: number) => {
    if (confidence === undefined) return null;

    const level =
      confidence >= 0.8 ? "high" : confidence >= 0.5 ? "medium" : "low";
    const variant =
      level === "high"
        ? "default"
        : level === "medium"
        ? "secondary"
        : "destructive";

    return (
      <Badge variant={variant} className="text-xs">
        {Math.round(confidence * 100)}%
      </Badge>
    );
  };

  const getSourceIcon = (source?: string) => {
    if (source === "ai")
      return <Sparkles className="h-3 w-3 text-purple-500" />;
    return null;
  };

  const getVerificationIcon = (riskLevel?: string) => {
    switch (riskLevel) {
      case "low":
        return <ShieldCheck className="h-4 w-4 text-green-500" />;
      case "medium":
        return <ShieldAlert className="h-4 w-4 text-yellow-500" />;
      case "high":
        return <ShieldX className="h-4 w-4 text-red-500" />;
      default:
        return <Shield className="h-4 w-4 text-gray-500" />;
    }
  };

  const getVerificationBadge = (
    riskLevel?: string,
    authenticityScore?: number
  ) => {
    if (!riskLevel) return null;

    const variant =
      riskLevel === "low"
        ? "default"
        : riskLevel === "medium"
        ? "secondary"
        : "destructive";
    const text =
      riskLevel === "low"
        ? "Verified"
        : riskLevel === "medium"
        ? "Review Required"
        : "High Risk";

    return (
      <div className="flex items-center gap-2">
        {getVerificationIcon(riskLevel)}
        <Badge variant={variant} className="text-xs">
          {text}
        </Badge>
        {authenticityScore && authenticityScore > 0 ? (
          <span className="text-xs text-muted-foreground">
            {authenticityScore}% authentic
          </span>
        ) : null}
      </div>
    );
  };

  const renderFieldValue = (field: ExtractedField) => {
    if (editingField === field.id) {
      return (
        <div className="flex items-center gap-2">
          <Input
            value={String(editValues[field.id] ?? "")}
            onChange={(e) =>
              setEditValues({ ...editValues, [field.id]: e.target.value })
            }
            className="h-8"
            autoFocus
          />
          <Button size="sm" variant="ghost" onClick={() => handleSave(field)}>
            <Save className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="ghost" onClick={handleCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      );
    }

    const value =
      field.type === "object" || field.type === "array"
        ? JSON.stringify(field.value, null, 2)
        : String(field.value);

    return (
      <div className="flex items-center justify-between group">
        <span
          className={cn(
            "text-sm",
            field.validation?.isValid === false && "text-red-500"
          )}
        >
          {value}
        </span>
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleEdit(field)}
            className="h-7 w-7 p-0"
          >
            <Edit2 className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleCopy(field)}
            className="h-7 w-7 p-0"
          >
            {copiedField === field.id ? (
              <Check className="h-3 w-3 text-green-500" />
            ) : (
              <Copy className="h-3 w-3" />
            )}
          </Button>
        </div>
      </div>
    );
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Extraction Results
              {result.documentType && (
                <Badge variant="outline">{result.documentType}</Badge>
              )}
              {result.verification
                ? getVerificationBadge(
                    result.verification.risk_level,
                    result.verification.authenticity_score
                  )
                : null}
            </CardTitle>
            <CardDescription className="mt-2">
              {result.extractedFields.length} fields extracted
              {result.processingTime &&
                ` in ${result.processingTime.toFixed(2)}s`}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleCopyAll}>
              <Copy className="h-4 w-4 mr-1" />
              Copy All
            </Button>
            {onExport && (
              <Button size="sm" onClick={() => onExport("json")}>
                <Download className="h-4 w-4 mr-1" />
                Export
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs
          value={viewMode}
          onValueChange={(v) =>
            setViewMode(v as "table" | "json" | "grouped" | "verification")
          }
        >
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="table">Table</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
            <TabsTrigger value="grouped">Grouped</TabsTrigger>
            <TabsTrigger value="verification">Verification</TabsTrigger>
          </TabsList>

          <TabsContent value="table">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.extractedFields.map((field) => (
                  <TableRow key={field.id}>
                    <TableCell className="font-medium">
                      {field.displayName}
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {renderFieldValue(field)}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{field.type}</Badge>
                    </TableCell>
                    <TableCell>
                      {getConfidenceBadge(field.confidence)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        {getSourceIcon(field.source)}
                        <span className="text-xs">{field.source}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEdit(field)}
                          className="h-7 w-7 p-0"
                        >
                          <Edit2 className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleCopy(field)}
                          className="h-7 w-7 p-0"
                        >
                          {copiedField === field.id ? (
                            <Check className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TabsContent>

          <TabsContent value="json">
            <pre className="p-4 bg-muted rounded-lg overflow-auto max-h-[500px]">
              <code className="text-sm">
                {JSON.stringify(
                  result.extractedFields.reduce<Record<string, unknown>>(
                    (acc, field) => {
                      acc[field.name] = field.value;
                      return acc;
                    },
                    {}
                  ),
                  null,
                  2
                )}
              </code>
            </pre>
          </TabsContent>

          <TabsContent value="grouped" className="space-y-4">
            {/* High Confidence Fields */}
            {groupedFields.high.length > 0 && (
              <div className="space-y-2">
                <button
                  onClick={() => toggleGroup("high")}
                  className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  {expandedGroups.has("high") ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  High Confidence ({groupedFields.high.length})
                  <Badge variant="default" className="ml-2">
                    Verified
                  </Badge>
                </button>
                {expandedGroups.has("high") && (
                  <div className="ml-6 space-y-2">
                    {groupedFields.high.map((field) => (
                      <div
                        key={field.id}
                        className="grid grid-cols-3 gap-4 p-3 border rounded-lg"
                      >
                        <div className="flex items-center gap-2">
                          <Label className="text-sm font-medium">
                            {field.displayName}
                          </Label>
                          {getSourceIcon(field.source)}
                        </div>
                        <div className="col-span-2">
                          {renderFieldValue(field)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Medium Confidence Fields */}
            {groupedFields.medium.length > 0 && (
              <div className="space-y-2">
                <button
                  onClick={() => toggleGroup("medium")}
                  className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  {expandedGroups.has("medium") ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  Medium Confidence ({groupedFields.medium.length})
                  <Badge variant="secondary" className="ml-2">
                    Review
                  </Badge>
                </button>
                {expandedGroups.has("medium") && (
                  <div className="ml-6 space-y-2">
                    {groupedFields.medium.map((field) => (
                      <div
                        key={field.id}
                        className="grid grid-cols-3 gap-4 p-3 border rounded-lg bg-yellow-50 dark:bg-yellow-950/20"
                      >
                        <div className="flex items-center gap-2">
                          <Label className="text-sm font-medium">
                            {field.displayName}
                          </Label>
                          {getSourceIcon(field.source)}
                          {getConfidenceBadge(field.confidence)}
                        </div>
                        <div className="col-span-2">
                          {renderFieldValue(field)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Low Confidence Fields */}
            {groupedFields.low.length > 0 && (
              <div className="space-y-2">
                <button
                  onClick={() => toggleGroup("low")}
                  className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors"
                >
                  {expandedGroups.has("low") ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  Low Confidence ({groupedFields.low.length})
                  <Badge variant="destructive" className="ml-2">
                    Needs Review
                  </Badge>
                </button>
                {expandedGroups.has("low") && (
                  <div className="ml-6 space-y-2">
                    {groupedFields.low.map((field) => (
                      <div
                        key={field.id}
                        className="grid grid-cols-3 gap-4 p-3 border rounded-lg bg-red-50 dark:bg-red-950/20"
                      >
                        <div className="flex items-center gap-2">
                          <Label className="text-sm font-medium">
                            {field.displayName}
                          </Label>
                          {getSourceIcon(field.source)}
                          {getConfidenceBadge(field.confidence)}
                        </div>
                        <div className="col-span-2">
                          {renderFieldValue(field)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="verification" className="space-y-4">
            {result.verification ? (
              <>
                {/* Risk Assessment */}
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-medium">
                      Document Verification
                    </h3>
                    {getVerificationBadge(
                      result.verification.risk_level,
                      result.verification.authenticity_score
                    )}
                  </div>

                  {/* Document Type Verification */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Expected Document Type
                      </Label>
                      <p className="text-sm">
                        {result.verification.expected_document_type ||
                          "Not specified"}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Detected Document Type
                      </Label>
                      <p className="text-sm">
                        {result.verification.detected_document_type ||
                          "Unknown"}
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Type Confidence
                      </Label>
                      <p className="text-sm">
                        {result.verification.document_type_confidence || 0}%
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-xs text-muted-foreground">
                        Authenticity Score
                      </Label>
                      <p className="text-sm">
                        {result.verification.authenticity_score || 0}%
                      </p>
                    </div>
                  </div>

                  <Separator />

                  {/* Tampering Indicators */}
                  {result.verification.tampering_indicators && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium">
                        Tampering Analysis
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(
                          result.verification.tampering_indicators
                        ).map(([key, value]) => (
                          <div
                            key={key}
                            className="flex items-center justify-between p-2 bg-muted rounded"
                          >
                            <span className="text-xs capitalize">
                              {key.replace(/_/g, " ")}
                            </span>
                            <Badge
                              variant={value ? "destructive" : "default"}
                              className="text-xs"
                            >
                              {value ? "Detected" : "Clear"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Separator />

                  {/* Security Checks */}
                  {result.verification.security_checks && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium">
                        Security Validation
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        {Object.entries(
                          result.verification.security_checks
                        ).map(([key, value]) => (
                          <div
                            key={key}
                            className="flex items-center justify-between p-2 bg-muted rounded"
                          >
                            <span className="text-xs capitalize">
                              {key.replace(/_/g, " ")}
                            </span>
                            <Badge
                              variant={value ? "default" : "destructive"}
                              className="text-xs"
                            >
                              {value ? "Passed" : "Failed"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Verification Notes */}
                  {result.verification.verification_notes &&
                    result.verification.verification_notes.length > 0 && (
                      <>
                        <Separator />
                        <div className="space-y-2">
                          <h4 className="text-sm font-medium">
                            Verification Notes
                          </h4>
                          <ul className="space-y-1">
                            {result.verification.verification_notes.map(
                              (note, index) => (
                                <li
                                  key={index}
                                  className="text-xs text-muted-foreground flex items-start gap-2"
                                >
                                  <span className="text-blue-500">•</span>
                                  {note}
                                </li>
                              )
                            )}
                          </ul>
                        </div>
                      </>
                    )}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <Shield className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  No verification data available
                </p>
              </div>
            )}
          </TabsContent>
        </Tabs>
        {/* Warnings and Suggestions */}
        {(result.warnings?.length || result.suggestions?.length) && (
          <>
            <Separator className="my-4" />
            <div className="space-y-3">
              {result.warnings?.map((warning, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg"
                >
                  <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
                  <p className="text-sm">{warning}</p>
                </div>
              ))}
              {result.suggestions?.map((suggestion, idx) => (
                <div
                  key={idx}
                  className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg"
                >
                  <Sparkles className="h-4 w-4 text-blue-600 mt-0.5" />
                  <p className="text-sm">{suggestion}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

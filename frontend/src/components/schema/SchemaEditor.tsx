"use client";

import React, { useState, useEffect } from "react";
import {
  Save,
  Plus,
  Trash2,
  X,
  Check,
  AlertTriangle,
  Target,
  Eye,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
// import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { GeneratedSchema, FieldConfig } from "./types";
import { AIDebugInfo } from "@/types";
import { AIDebugDialog } from "./components/AIDebugDialog";

interface SchemaEditorProps {
  schema: GeneratedSchema | null;
  aiDebugInfo?: AIDebugInfo | null;
  onSave: (data: {
    name: string;
    description: string;
    category: string;
    fields: Record<string, FieldConfig>;
  }) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  className?: string;
}

export function SchemaEditor({
  schema,
  aiDebugInfo,
  onSave,
  onCancel,
  isLoading = false,
  className,
}: SchemaEditorProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    category: "Generated",
  });

  const [fields, setFields] = useState<Record<string, FieldConfig>>({});
  const [editingField, setEditingField] = useState<string | null>(null);

  // Initialize form data when schema changes
  useEffect(() => {
    if (schema) {
      setFormData({
        name: schema.name,
        description: schema.description || "",
        category: schema.category || "Generated",
      });
      setFields(schema.fields || {});
    } else {
      setFormData({
        name: "",
        description: "",
        category: "Generated",
      });
      setFields({});
    }
  }, [schema]);

  const handleSave = async () => {
    try {
      await onSave({
        name: formData.name,
        description: formData.description,
        category: formData.category,
        fields,
      });
    } catch {
      // Error handling is done in the parent component
    }
  };

  const addField = () => {
    const fieldName = `field_${Date.now()}`;
    setFields((prev) => ({
      ...prev,
      [fieldName]: {
        type: "text",
        description: "",
        required: false,
        confidence_score: 0.9,
        legibility: "high",
        extraction_hints: [],
        positioning_hints: [],
        validation_pattern: "",
        potential_issues: [],
      },
    }));
    setEditingField(fieldName);
  };

  const deleteField = (fieldName: string) => {
    setFields((prev) => {
      const updated = { ...prev };
      delete updated[fieldName];
      return updated;
    });
    if (editingField === fieldName) {
      setEditingField(null);
    }
  };

  const updateField = (fieldName: string, updates: Partial<FieldConfig>) => {
    setFields((prev) => ({
      ...prev,
      [fieldName]: {
        ...prev[fieldName],
        ...updates,
      },
    }));
  };

  const renameField = (oldName: string, newName: string) => {
    if (oldName === newName || !newName.trim()) return;

    setFields((prev) => {
      const updated = { ...prev };
      const fieldConfig = updated[oldName];
      delete updated[oldName];
      updated[newName] = fieldConfig;
      return updated;
    });

    if (editingField === oldName) {
      setEditingField(newName);
    }
  };

  const fieldTypes = [
    "text",
    "email",
    "phone",
    "number",
    "date",
    "currency",
    "boolean",
    "address",
    "name",
    "ssn",
    "other",
  ];

  const categories = [
    "Government",
    "Business",
    "Personal",
    "Healthcare",
    "Education",
    "Generated",
    "Other",
  ];

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>
              {schema ? "Edit Schema" : "Create New Schema"}
            </CardTitle>
            <CardDescription>
              {schema
                ? "Modify the schema fields and properties"
                : "Create a new document extraction schema"}
            </CardDescription>
          </div>
          {/* Duplicate Action Buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onCancel}
              disabled={isLoading}
            >
              <X className="h-4 w-4 mr-1" />
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={isLoading || !formData.name.trim()}
            >
              <Save className="h-4 w-4 mr-1" />
              {isLoading ? "Saving..." : "Save Schema"}
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Schema Quality Overview */}
        {schema && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/50 dark:to-purple-950/50 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium flex items-center gap-2">
                <Zap className="h-4 w-4 text-blue-500" />
                Schema Quality Assessment
              </h3>
              <AIDebugDialog schema={schema} aiDebugInfo={aiDebugInfo} />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-1">
                  <span className="text-sm font-medium">
                    Overall Confidence
                  </span>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger>
                        <Eye className="h-3 w-3 text-muted-foreground" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>AI confidence in schema accuracy</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
                <div className="flex items-center gap-2">
                  <Progress
                    value={(schema.overall_confidence || 0) * 100}
                    className="h-2 flex-1"
                  />
                  <span className="text-sm text-muted-foreground">
                    {Math.round((schema.overall_confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium">Production Ready</span>
                <div className="flex items-center gap-1">
                  {schema.production_ready ? (
                    <Badge variant="default" className="bg-green-500">
                      <Check className="h-3 w-3 mr-1" />
                      Ready
                    </Badge>
                  ) : (
                    <Badge variant="destructive">
                      <AlertTriangle className="h-3 w-3 mr-1" />
                      Needs Review
                    </Badge>
                  )}
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium">Document Quality</span>
                <Badge variant="outline">
                  {schema.document_quality || "Unknown"}
                </Badge>
              </div>
              <div className="space-y-1">
                <span className="text-sm font-medium">
                  Extraction Difficulty
                </span>
                <Badge variant="outline">
                  {schema.extraction_difficulty || "Unknown"}
                </Badge>
              </div>
            </div>
            {schema.quality_recommendations &&
              schema.quality_recommendations.length > 0 && (
                <div className="space-y-2">
                  <span className="text-sm font-medium">
                    Quality Recommendations:
                  </span>
                  <div className="space-y-1">
                    {schema.quality_recommendations
                      .slice(0, 3)
                      .map((rec, index) => (
                        <div
                          key={index}
                          className="text-sm text-muted-foreground flex items-start gap-1"
                        >
                          <Target className="h-3 w-3 mt-0.5 text-blue-500 flex-shrink-0" />
                          {rec}
                        </div>
                      ))}
                  </div>
                </div>
              )}
          </div>
        )}

        {/* Basic Information */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Schema Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                placeholder="Enter schema name"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category">Category</Label>
              <Select
                value={formData.category}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, category: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((category) => (
                    <SelectItem key={category} value={category}>
                      {category}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              placeholder="Describe what this schema is used for"
              rows={3}
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
          </div>
        </div>

        <Separator />

        {/* Fields Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium">Fields</h3>
              <p className="text-sm text-muted-foreground">
                Define the fields to extract from documents
              </p>
            </div>
            <Button onClick={addField} variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Field
            </Button>
          </div>

          {Object.keys(fields).length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <p>No fields defined</p>
              <p className="text-sm">Add your first field to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(fields).map(([fieldName, field]) => (
                <div
                  key={fieldName}
                  className="border rounded-lg p-4 space-y-3"
                >
                  {editingField === fieldName ? (
                    <FieldEditor
                      fieldName={fieldName}
                      field={field}
                      onSave={(newName, updatedField) => {
                        if (newName !== fieldName) {
                          renameField(fieldName, newName);
                        }
                        updateField(newName, updatedField);
                        setEditingField(null);
                      }}
                      onCancel={() => setEditingField(null)}
                      fieldTypes={fieldTypes}
                    />
                  ) : (
                    <FieldDisplay
                      fieldName={fieldName}
                      field={field}
                      onEdit={() => setEditingField(fieldName)}
                      onDelete={() => deleteField(fieldName)}
                    />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <Separator />

        {/* Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isLoading || !formData.name.trim()}
          >
            {isLoading ? "Saving..." : "Save Schema"}
            <Save className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// Field display component
function FieldDisplay({
  fieldName,
  field,
  onEdit,
  onDelete,
}: {
  fieldName: string;
  field: FieldConfig;
  onEdit: () => void;
  onDelete: () => void;
}) {
  const getConfidenceColor = (score?: number) => {
    if (!score) return "bg-gray-200";
    if (score >= 0.8) return "bg-green-500";
    if (score >= 0.6) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getLegibilityIcon = (legibility?: string) => {
    switch (legibility) {
      case "high":
        return "🟢";
      case "medium":
        return "🟡";
      case "low":
        return "🔴";
      default:
        return "⚪";
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium">{fieldName}</h4>
            <Badge variant="secondary" className="text-xs">
              {field.type || "text"}
            </Badge>
            {field.required && (
              <Badge variant="destructive" className="text-xs">
                Required
              </Badge>
            )}
          </div>
          {field.description && (
            <p className="text-sm text-muted-foreground mb-2">
              {field.description}
            </p>
          )}

          {/* Validation Pattern - Prominently Displayed */}
          {field.validation_pattern && (
            <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center gap-2 mb-1">
                <Check className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">
                  Validation Pattern
                </span>
              </div>
              <code className="text-xs font-mono text-blue-700 bg-blue-100 px-2 py-1 rounded">
                {field.validation_pattern}
              </code>
            </div>
          )}

          {/* Extraction Hints - Prominently Displayed */}
          {field.extraction_hints && field.extraction_hints.length > 0 && (
            <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">
                  Extraction Hints
                </span>
              </div>
              <ul className="space-y-1">
                {field.extraction_hints.slice(0, 2).map((hint, i) => (
                  <li
                    key={i}
                    className="text-xs text-green-700 flex items-start gap-1"
                  >
                    <span className="text-green-500 mt-0.5">•</span>
                    <span>{hint}</span>
                  </li>
                ))}
                {field.extraction_hints.length > 2 && (
                  <li className="text-xs text-green-600 italic">
                    +{field.extraction_hints.length - 2} more hints...
                  </li>
                )}
              </ul>
            </div>
          )}

          {/* Positioning Hints - Prominently Displayed */}
          {field.positioning_hints && (
            <div className="mb-3 p-2 bg-purple-50 border border-purple-200 rounded-md">
              <div className="flex items-center gap-2 mb-1">
                <Eye className="h-4 w-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-800">
                  Field Location
                </span>
              </div>
              <p className="text-xs text-purple-700">
                {field.positioning_hints}
              </p>
            </div>
          )}

          {/* Advanced Field Metrics */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            {field.confidence_score !== undefined && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <div className="flex items-center gap-1">
                      <div
                        className={`w-2 h-2 rounded-full ${getConfidenceColor(
                          field.confidence_score
                        )}`}
                      />
                      <span>
                        Confidence: {Math.round(field.confidence_score * 100)}%
                      </span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>AI confidence in field extraction accuracy</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            {field.legibility && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <div className="flex items-center gap-1">
                      <span>{getLegibilityIcon(field.legibility)}</span>
                      <span>Legibility: {field.legibility}</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Text legibility assessment</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
            {field.potential_issues && field.potential_issues.length > 0 && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <div className="flex items-center gap-1 text-orange-600">
                      <AlertTriangle className="h-3 w-3" />
                      <span>{field.potential_issues.length} issues</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent>
                    <div className="space-y-1 max-w-xs">
                      {field.potential_issues.slice(0, 3).map((issue, i) => (
                        <p key={i} className="text-xs">
                          {issue}
                        </p>
                      ))}
                    </div>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
        </div>
        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Edit
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// Field editor component
function FieldEditor({
  fieldName,
  field,
  onSave,
  onCancel,
  fieldTypes,
}: {
  fieldName: string;
  field: FieldConfig;
  onSave: (name: string, field: FieldConfig) => void;
  onCancel: () => void;
  fieldTypes: string[];
}) {
  const [editedName, setEditedName] = useState(fieldName);
  const [editedField, setEditedField] = useState<FieldConfig>({
    ...field,
    extraction_hints: field.extraction_hints || [],
    positioning_hints: field.positioning_hints || [],
    potential_issues: field.potential_issues || [],
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSave = () => {
    if (!editedName.trim()) return;
    onSave(editedName.trim(), editedField);
  };

  const addExtractionHint = () => {
    setEditedField((prev) => ({
      ...prev,
      extraction_hints: [...(prev.extraction_hints || []), ""],
    }));
  };

  const updateExtractionHint = (index: number, value: string) => {
    setEditedField((prev) => ({
      ...prev,
      extraction_hints:
        prev.extraction_hints?.map((hint, i) => (i === index ? value : hint)) ||
        [],
    }));
  };

  const removeExtractionHint = (index: number) => {
    setEditedField((prev) => ({
      ...prev,
      extraction_hints:
        prev.extraction_hints?.filter((_, i) => i !== index) || [],
    }));
  };

  const addPositioningHint = () => {
    setEditedField((prev) => ({
      ...prev,
      positioning_hints: [...(prev.positioning_hints || []), ""],
    }));
  };

  const updatePositioningHint = (index: number, value: string) => {
    setEditedField((prev) => ({
      ...prev,
      positioning_hints:
        prev.positioning_hints?.map((hint, i) =>
          i === index ? value : hint
        ) || [],
    }));
  };

  const removePositioningHint = (index: number) => {
    setEditedField((prev) => ({
      ...prev,
      positioning_hints:
        prev.positioning_hints?.filter((_, i) => i !== index) || [],
    }));
  };

  return (
    <div className="space-y-4 bg-muted/50 p-4 rounded">
      {/* Basic Properties */}
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Field Name</Label>
          <Input
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            placeholder="Field name"
            className="h-8"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Type</Label>
          <Select
            value={editedField.type || "text"}
            onValueChange={(value) =>
              setEditedField((prev) => ({ ...prev, type: value }))
            }
          >
            <SelectTrigger className="h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {fieldTypes.map((type) => (
                <SelectItem key={type} value={type}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="space-y-1">
        <Label className="text-xs">Description</Label>
        <textarea
          value={editedField.description || ""}
          onChange={(e) =>
            setEditedField((prev) => ({ ...prev, description: e.target.value }))
          }
          placeholder="Field description"
          rows={2}
          className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>

      {/* Quality Metrics */}
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1">
          <Label className="text-xs">Confidence Score</Label>
          <Input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={editedField.confidence_score || 0.9}
            onChange={(e) =>
              setEditedField((prev) => ({
                ...prev,
                confidence_score: parseFloat(e.target.value),
              }))
            }
            className="h-8"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Legibility</Label>
          <Select
            value={editedField.legibility || "high"}
            onValueChange={(value) =>
              setEditedField((prev) => ({
                ...prev,
                legibility: value as "high" | "medium" | "low",
              }))
            }
          >
            <SelectTrigger className="h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Validation Pattern</Label>
          <Input
            value={editedField.validation_pattern || ""}
            onChange={(e) =>
              setEditedField((prev) => ({
                ...prev,
                validation_pattern: e.target.value,
              }))
            }
            placeholder="Regex pattern"
            className="h-8"
          />
        </div>
      </div>

      {/* Advanced Properties Toggle */}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-xs"
      >
        {showAdvanced ? "Hide" : "Show"} Advanced Properties
      </Button>

      {showAdvanced && (
        <div className="space-y-4 border-t pt-4">
          {/* Extraction Hints */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Extraction Hints</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addExtractionHint}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
            {(editedField.extraction_hints || []).map((hint, index) => (
              <div key={index} className="flex gap-1">
                <Input
                  value={hint}
                  onChange={(e) => updateExtractionHint(index, e.target.value)}
                  placeholder="Extraction hint"
                  className="h-8 flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeExtractionHint(index)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>

          {/* Positioning Hints */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Positioning Hints</Label>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={addPositioningHint}
              >
                <Plus className="h-3 w-3" />
              </Button>
            </div>
            {(editedField.positioning_hints || []).map((hint, index) => (
              <div key={index} className="flex gap-1">
                <Input
                  value={hint}
                  onChange={(e) => updatePositioningHint(index, e.target.value)}
                  placeholder="Positioning hint"
                  className="h-8 flex-1"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removePositioningHint(index)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id={`required-${fieldName}`}
            checked={editedField.required || false}
            onChange={(e) =>
              setEditedField((prev) => ({
                ...prev,
                required: e.target.checked,
              }))
            }
            className="h-4 w-4 rounded border border-input bg-background"
          />
          <Label htmlFor={`required-${fieldName}`} className="text-sm">
            Required field
          </Label>
        </div>

        <div className="flex gap-1">
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={handleSave}>
            <Check className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

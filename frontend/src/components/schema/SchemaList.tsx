"use client";

import React from "react";
import {
  FileText,
  Edit2,
  Trash2,
  Calendar,
  Tag,
  Loader2,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";

interface Schema {
  id: string;
  name: string;
  description?: string;
  category: string;
  field_count: number;
  created_at: string;
  updated_at?: string;
}

interface SchemaListProps {
  schemas: Schema[];
  isLoading: boolean;
  onEditSchema: (schemaId: string) => void;
  onDeleteSchema: (schemaId: string) => Promise<void>;
  isOperationInProgress: (operation?: string) => boolean;
  className?: string;
}

export function SchemaList({
  schemas,
  isLoading,
  onEditSchema,
  onDeleteSchema,
  isOperationInProgress,
  className,
}: SchemaListProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [schemaToDelete, setSchemaToDelete] = React.useState<Schema | null>(
    null
  );

  const handleDeleteClick = (schema: Schema) => {
    setSchemaToDelete(schema);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!schemaToDelete) return;

    try {
      await onDeleteSchema(schemaToDelete.id);
      toast.success("Schema deleted successfully");
    } catch {
      toast.error("Failed to delete schema");
    } finally {
      setDeleteDialogOpen(false);
      setSchemaToDelete(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Unknown";
    }
  };

  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      Government: "bg-blue-100 text-blue-800 border-blue-200",
      Business: "bg-green-100 text-green-800 border-green-200",
      Personal: "bg-purple-100 text-purple-800 border-purple-200",
      Healthcare: "bg-red-100 text-red-800 border-red-200",
      Education: "bg-yellow-100 text-yellow-800 border-yellow-200",
      Generated: "bg-gray-100 text-gray-800 border-gray-200",
      Other: "bg-gray-100 text-gray-800 border-gray-200",
    };
    return colors[category] || colors.Other;
  };

  if (isLoading) {
    return (
      <div className={className}>
        <div className="mb-4">
          <h3 className="text-base font-medium flex items-center gap-2 text-foreground">
            <FileText className="h-4 w-4" />
            Document types
          </h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span className="ml-2 text-sm text-muted-foreground">
            Loading schemas...
          </span>
        </div>
      </div>
    );
  }

  const isCompactMode = className?.includes("max-h");

  return (
    <>
      <div className={className}>
        {/* Header */}
        <div className={`${isCompactMode ? "mb-3" : "mb-5"}`}>
          <h3
            className={`${
              isCompactMode ? "text-sm font-medium" : "text-lg font-semibold"
            } flex items-center gap-2 text-gray-900`}
          >
            <FileText className={`${isCompactMode ? "h-4 w-4" : "h-5 w-5"} text-blue-600`} />
            {isCompactMode
              ? `Schemas (${schemas.length})`
              : `Document types (${schemas.length})`}
          </h3>
          {!isCompactMode && (
            <p className="text-sm text-gray-500 mt-2">
              Manage your saved document extraction schemas
            </p>
          )}
        </div>

        {/* Content */}
        {schemas.length === 0 ? (
          <div className={`text-center ${isCompactMode ? "py-6" : "py-12"}`}>
            <div className="bg-gray-50 rounded-full w-20 h-20 mx-auto mb-4 flex items-center justify-center">
              <FileText className="h-8 w-8 text-gray-400" />
            </div>
            <h4
              className={`font-medium text-gray-900 mb-2 ${
                isCompactMode ? "text-sm" : "text-base"
              }`}
            >
              No schemas saved yet
            </h4>
            {!isCompactMode && (
              <p className="text-sm text-gray-500 max-w-sm mx-auto">
                Create your first extraction schema to get started with
                automated document processing
              </p>
            )}
          </div>
        ) : (
          <div
            className={`space-y-4 overflow-y-auto ${
              isCompactMode ? "max-h-[350px]" : "max-h-[400px]"
            }`}
          >
            {schemas.map((schema) => (
              <div
                key={schema.id}
                className={`group relative border border-gray-200 rounded-xl bg-gradient-to-r from-white via-gray-50/30 to-white shadow-sm hover:shadow-md hover:border-gray-300 transition-all duration-200 hover:scale-[1.005] ${
                  isCompactMode ? "p-4" : "p-5"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div
                      className={`flex items-center gap-2 ${
                        isCompactMode ? "mb-1" : "mb-2"
                      }`}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <FileText className="h-4 w-4 text-blue-600 flex-shrink-0" />
                        <h3
                          className={`font-semibold truncate text-gray-900 ${
                            isCompactMode ? "text-sm" : "text-base"
                          }`}
                        >
                          {schema.name}
                        </h3>
                      </div>
                      <Badge
                        variant="secondary"
                        className={`${getCategoryColor(
                          schema.category
                        )} border font-medium flex-shrink-0 ${
                          isCompactMode
                            ? "text-xs h-5 px-2"
                            : "text-xs h-6 px-3"
                        }`}
                      >
                        {schema.category}
                      </Badge>
                    </div>

                    {schema.description && !isCompactMode && (
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2 leading-relaxed">
                        {schema.description}
                      </p>
                    )}

                    <div
                      className={`flex items-center flex-wrap gap-2 ${
                        isCompactMode ? "gap-1.5" : "gap-2"
                      }`}
                    >
                      <span className="flex items-center gap-1.5 bg-blue-50 text-blue-700 rounded-full px-3 py-1 text-xs font-medium border border-blue-200">
                        <Tag className="h-3 w-3" />
                        {schema.field_count} fields
                      </span>
                      <span className="flex items-center gap-1.5 bg-green-50 text-green-700 rounded-full px-3 py-1 text-xs font-medium border border-green-200">
                        <Calendar className="h-3 w-3" />
                        {formatDate(schema.updated_at || schema.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all duration-200">
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`rounded-lg bg-white hover:bg-blue-50 hover:text-blue-700 border border-gray-200 hover:border-blue-300 shadow-sm hover:shadow transition-all duration-200 ${
                        isCompactMode ? "h-8 px-2" : "h-9 px-3"
                      }`}
                      onClick={() => onEditSchema(schema.id)}
                      disabled={isOperationInProgress(schema.id)}
                      title="Edit Schema"
                    >
                      {isOperationInProgress(schema.id) ? (
                        <Loader2
                          className={`animate-spin ${
                            isCompactMode ? "h-3 w-3" : "h-4 w-4"
                          }`}
                        />
                      ) : (
                        <Edit2
                          className={isCompactMode ? "h-3 w-3" : "h-4 w-4"}
                        />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className={`rounded-lg bg-white hover:bg-red-50 hover:text-red-700 border border-gray-200 hover:border-red-300 shadow-sm hover:shadow transition-all duration-200 ${
                        isCompactMode ? "h-8 px-2" : "h-9 px-3"
                      }`}
                      onClick={() => handleDeleteClick(schema)}
                      disabled={isOperationInProgress(schema.id)}
                      title="Delete Schema"
                    >
                      {isOperationInProgress(schema.id) ? (
                        <Loader2
                          className={`animate-spin ${
                            isCompactMode ? "h-3 w-3" : "h-4 w-4"
                          }`}
                        />
                      ) : (
                        <Trash2
                          className={isCompactMode ? "h-3 w-3" : "h-4 w-4"}
                        />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Delete Schema
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the schema &ldquo;
              {schemaToDelete?.name}&rdquo;? This action cannot be undone and
              will permanently remove the schema from your saved templates.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Delete Schema
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

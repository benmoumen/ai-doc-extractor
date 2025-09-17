"use client";

import React, { useState } from "react";
import { Check, ChevronsUpDown, Sparkles, FileText } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export interface Schema {
  id: string;
  name: string;
  description?: string;
  category?: string;
  fields_count?: number;
  last_used?: string;
  confidence_threshold?: number;
}

interface SchemaSelectorProps {
  schemas?: Schema[];
  onSchemaSelect: (schemaId: string | null, useAI: boolean) => void;
  className?: string;
}

export function SchemaSelector({
  schemas = [],
  onSchemaSelect,
  className,
}: SchemaSelectorProps) {
  const [open, setOpen] = useState(false);
  const [selectedSchema, setSelectedSchema] = useState<string | null>(null);
  const [extractionMode, setExtractionMode] = useState<"schema" | "ai">("schema");
  const [searchValue, setSearchValue] = useState("");

  // Use only provided schemas - no fallback defaults
  const availableSchemas: Schema[] = schemas;

  const handleModeChange = (mode: string) => {
    setExtractionMode(mode as "schema" | "ai");
    if (mode === "ai") {
      setSelectedSchema(null);
      onSchemaSelect(null, true);
    } else if (selectedSchema) {
      // In schema mode, AI should be off (no hybrid behavior)
      onSchemaSelect(selectedSchema, false);
    }
  };

  const handleSchemaSelect = (schemaId: string) => {
    setSelectedSchema(schemaId);
    setOpen(false);
    if (extractionMode === "schema") {
      // When a schema is selected in schema mode, disable AI
      onSchemaSelect(schemaId, false);
    }
  };

  const selectedSchemaData = availableSchemas.find(
    (s) => s.id === selectedSchema
  );

  // Group schemas by category
  const groupedSchemas = availableSchemas.reduce((acc, schema) => {
    const category = schema.category || "Other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(schema);
    return acc;
  }, {} as Record<string, Schema[]>);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Extraction Mode Selection */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Extraction Mode</Label>
        <RadioGroup value={extractionMode} onValueChange={handleModeChange}>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="schema" id="schema-mode" />
              <Label
                htmlFor="schema-mode"
                className="flex items-center gap-2 cursor-pointer"
              >
                <FileText className="h-4 w-4 text-blue-500" />
                <span>Schema</span>
                <Badge variant="secondary" className="ml-1">
                  Recommended
                </Badge>
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="ai" id="ai-mode" />
              <Label
                htmlFor="ai-mode"
                className="flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="h-4 w-4 text-purple-500" />
                <span>AI Free-form Discovery</span>
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>

      {/* Schema Selection (shown when schema mode is selected) */}
      {extractionMode === "schema" && (
        <>
          <Separator />
          <div className="space-y-3">
            <Label className="text-sm font-medium">Select Schema</Label>
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="w-full justify-between"
                >
                  {selectedSchemaData ? (
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      <span>{selectedSchemaData.name}</span>
                      {selectedSchemaData.category && (
                        <Badge variant="outline" className="ml-2">
                          {selectedSchemaData.category}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">
                      Select a schema...
                    </span>
                  )}
                  <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[400px] p-0">
                <Command>
                  <CommandInput
                    placeholder="Search schemas..."
                    value={searchValue}
                    onValueChange={setSearchValue}
                  />
                  <CommandList>
                    <CommandEmpty>No schema found.</CommandEmpty>
                    {Object.entries(groupedSchemas).map(
                      ([category, categorySchemas]) => (
                        <CommandGroup key={category} heading={category}>
                          {categorySchemas.map((schema) => (
                            <CommandItem
                              key={schema.id}
                              value={schema.id}
                              onSelect={handleSchemaSelect}
                            >
                              <Check
                                className={cn(
                                  "mr-2 h-4 w-4",
                                  selectedSchema === schema.id
                                    ? "opacity-100"
                                    : "opacity-0"
                                )}
                              />
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">
                                    {schema.name}
                                  </span>
                                  {schema.fields_count && (
                                    <Badge
                                      variant="secondary"
                                      className="text-xs"
                                    >
                                      {schema.fields_count} fields
                                    </Badge>
                                  )}
                                </div>
                                {schema.description && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {schema.description}
                                  </p>
                                )}
                                {schema.last_used && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    Last used: {schema.last_used}
                                  </p>
                                )}
                              </div>
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      )
                    )}
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>

            {/* Hybrid Mode removed: backend doesn't support it and it caused param confusion */}
          </div>
        </>
      )}

      {/* AI Mode Information */}
      {extractionMode === "ai" && (
        <>
          <Separator />
          <div className="p-4 border rounded-lg bg-purple-50 dark:bg-purple-950/20">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-purple-500 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">AI Free-form Discovery Mode</p>
                <p className="text-xs text-muted-foreground">
                  AI analyzes the document and automatically discovers all available data fields without enforcing a predefined schema. Best for exploring unknown document types or extracting all possible information.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

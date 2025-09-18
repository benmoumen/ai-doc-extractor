import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api';
import { GeneratedSchema, FieldConfig } from '../types';

interface Schema {
  id: string;
  name: string;
  description?: string;
  category: string;
  field_count: number;
  created_at: string;
  updated_at?: string;
  fields?: Record<string, FieldConfig>;
}

interface CreateSchemaData {
  name: string;
  description: string;
  category: string;
  fields: Record<string, FieldConfig>;
}

interface UpdateSchemaData {
  name: string;
  description?: string;
  category: string;
  fields: Record<string, FieldConfig>;
}

interface SchemaManagerState {
  schemas: Schema[];
  activeSchema: GeneratedSchema | null;
  isLoading: boolean;
  error: string | null;
  operationInProgress: string | null; // 'create', 'update', 'delete', or schema id for specific operations
}

export function useSchemaManager() {
  const [state, setState] = useState<SchemaManagerState>({
    schemas: [],
    activeSchema: null,
    isLoading: false,
    error: null,
    operationInProgress: null,
  });

  // Helper to update state
  const updateState = useCallback((updates: Partial<SchemaManagerState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    updateState({ error: null });
  }, [updateState]);

  // Load all schemas
  const loadSchemas = useCallback(async () => {
    try {
      updateState({ isLoading: true, error: null });

      const response = await apiClient.getAvailableSchemas();

      if (response.success && response.schemas) {
        const schemaArray = Object.values(response.schemas)
          .map((schema: unknown) => {
            const s = schema as Record<string, unknown>;
            return {
              id: s.id as string,
              name: (s.name || s.display_name) as string,
              description: s.description as string | undefined,
              category: (s.category || 'Generated') as string,
              field_count: (s.field_count || Object.keys((s.fields as Record<string, unknown>) || {}).length) as number,
              created_at: (s.created_at || new Date().toISOString()) as string,
              updated_at: s.updated_at as string | undefined,
              fields: s.fields as Record<string, FieldConfig> | undefined,
            };
          })
          .sort((a: Schema, b: Schema) => {
            const aDate = a.updated_at ? new Date(a.updated_at).getTime() : 0;
            const bDate = b.updated_at ? new Date(b.updated_at).getTime() : 0;
            return bDate - aDate;
          });
        updateState({ schemas: schemaArray });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load schemas';
      updateState({ error: message });
    } finally {
      updateState({ isLoading: false });
    }
  }, [updateState]);

  // Load specific schema details
  const loadSchema = useCallback(async (schemaId: string) => {
    try {
      updateState({ operationInProgress: schemaId, error: null });

      const response = await apiClient.getSchemaDetails(schemaId);

      if (response.success && response.schema) {
        const schema = response.schema;

        // Normalize field confidence scores from percentages to decimals
        const normalizedFields = Object.entries(schema.fields || {}).reduce((acc, [key, field]) => {
          const fieldWithConfidence = field as any;
          acc[key] = {
            ...field,
            confidence_score: fieldWithConfidence.confidence_score !== undefined
              ? (fieldWithConfidence.confidence_score > 1 ? fieldWithConfidence.confidence_score / 100 : fieldWithConfidence.confidence_score)
              : fieldWithConfidence.confidence_score
          };
          return acc;
        }, {} as Record<string, any>);

        // Convert to GeneratedSchema format
        const generatedSchema: GeneratedSchema = {
          id: schema.id,
          name: schema.name,
          description: schema.description || '',
          category: schema.category || 'Generated',
          fields: normalizedFields,
          total_fields: (schema as { field_count?: number }).field_count || Object.keys(schema.fields || {}).length,
          generation_confidence: 0.85, // Default values for generated properties
          production_ready: true,
          validation_status: 'valid',
          user_review_status: 'approved',
          overall_confidence: 0.85,
          document_quality: 'high',
          extraction_difficulty: 'medium',
          document_specific_notes: [],
          quality_recommendations: [],
        };

        updateState({ activeSchema: generatedSchema });
        return generatedSchema;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to load schema';
      updateState({ error: message });
    } finally {
      updateState({ operationInProgress: null });
    }
    return null;
  }, [updateState]);

  // Create new schema
  const createSchema = useCallback(async (data: CreateSchemaData) => {
    try {
      updateState({ operationInProgress: 'create', error: null });

      // Generate a temporary ID for optimistic update
      const tempId = `temp_${Date.now()}`;

      const response = await apiClient.saveSchema({
        id: tempId,
        name: data.name,
        description: data.description,
        category: data.category,
        fields: data.fields,
      });

      if (response.success) {
        // Refresh schemas list to get the new schema
        await loadSchemas();
        return response.schema_id;
      } else {
        throw new Error(response.message || 'Failed to create schema');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to create schema';
      updateState({ error: message });
      throw error;
    } finally {
      updateState({ operationInProgress: null });
    }
  }, [updateState, loadSchemas]);

  // Update existing schema
  const updateSchema = useCallback(async (schemaId: string, data: UpdateSchemaData) => {
    try {
      updateState({ operationInProgress: schemaId, error: null });

      const response = await apiClient.updateSchema(schemaId, {
        name: data.name,
        description: data.description,
        category: data.category,
        fields: data.fields,
      });

      if (response.success) {
        // Update the activeSchema if it's the one being updated
        if (state.activeSchema?.id === schemaId) {
          const updatedSchema: GeneratedSchema = {
            ...state.activeSchema,
            name: data.name,
            description: data.description || '',
            category: data.category,
            fields: data.fields,
            total_fields: Object.keys(data.fields).length,
          };
          updateState({ activeSchema: updatedSchema });
        }

        // Refresh schemas list
        await loadSchemas();
        return response.schema_id;
      } else {
        throw new Error(response.message || 'Failed to update schema');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to update schema';
      updateState({ error: message });
      throw error;
    } finally {
      updateState({ operationInProgress: null });
    }
  }, [updateState, loadSchemas, state.activeSchema]);

  // Delete schema
  const deleteSchema = useCallback(async (schemaId: string) => {
    try {
      updateState({ operationInProgress: schemaId, error: null });

      const response = await apiClient.deleteSchema(schemaId);

      if (response.success) {
        // Clear activeSchema if it's the one being deleted
        if (state.activeSchema?.id === schemaId) {
          updateState({ activeSchema: null });
        }

        // Remove from schemas list optimistically
        updateState({
          schemas: state.schemas.filter(schema => schema.id !== schemaId)
        });

        return true;
      } else {
        throw new Error(response.message || 'Failed to delete schema');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to delete schema';
      updateState({ error: message });
      throw error;
    } finally {
      updateState({ operationInProgress: null });
    }
  }, [updateState, state.activeSchema, state.schemas]);

  // Set active schema (for editing)
  const setActiveSchema = useCallback((schema: GeneratedSchema | null) => {
    updateState({ activeSchema: schema });
  }, [updateState]);

  // Check if operation is in progress
  const isOperationInProgress = useCallback((operation?: string) => {
    if (!operation) return state.operationInProgress !== null;
    return state.operationInProgress === operation;
  }, [state.operationInProgress]);

  return {
    // State
    schemas: state.schemas,
    activeSchema: state.activeSchema,
    isLoading: state.isLoading,
    error: state.error,

    // Operations
    loadSchemas,
    loadSchema,
    createSchema,
    updateSchema,
    deleteSchema,

    // Helpers
    setActiveSchema,
    clearError,
    isOperationInProgress,
  };
}
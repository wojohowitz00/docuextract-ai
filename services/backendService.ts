import { ExtractedData } from "../types";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export interface ExtractionResponse {
  id: string;
  data: ExtractedData;
  confidence: number;
  provider: string;
  duplicate: boolean;
}

export interface ExtractionListItem {
  id: string;
  filename: string;
  documentType: string;
  vendorName: string;
  totalAmount: number;
  currency: string;
  date: string | null;
  createdAt: string | null;
}

export interface ListExtractionsResponse {
  extractions: ExtractionListItem[];
  total: number;
  offset: number;
  limit: number;
}

/**
 * Extract data from document using backend API
 */
export const extractDocument = async (file: File): Promise<ExtractionResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BACKEND_URL}/api/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Extraction failed" }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
};

/**
 * List all extractions with optional filters
 */
export const listExtractions = async (
  filters?: {
    dateFrom?: string;
    dateTo?: string;
    vendor?: string;
    docType?: string;
    offset?: number;
    limit?: number;
  }
): Promise<ListExtractionsResponse> => {
  const params = new URLSearchParams();
  if (filters?.dateFrom) params.append("date_from", filters.dateFrom);
  if (filters?.dateTo) params.append("date_to", filters.dateTo);
  if (filters?.vendor) params.append("vendor", filters.vendor);
  if (filters?.docType) params.append("doc_type", filters.docType);
  if (filters?.offset) params.append("offset", filters.offset.toString());
  if (filters?.limit) params.append("limit", filters.limit.toString());

  const response = await fetch(`${BACKEND_URL}/api/extractions?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to list extractions: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Get single extraction by ID
 */
export const getExtraction = async (id: string): Promise<ExtractedData> => {
  const response = await fetch(`${BACKEND_URL}/api/extractions/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to get extraction: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Export extractions to CSV
 */
export const exportExtractions = async (extractionIds?: string[]): Promise<void> => {
  const params = new URLSearchParams();
  params.append("format", "csv");
  if (extractionIds && extractionIds.length > 0) {
    params.append("extraction_ids", extractionIds.join(","));
  }

  const response = await fetch(`${BACKEND_URL}/api/extractions/export?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to export: ${response.statusText}`);
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `extractions_${new Date().toISOString().split("T")[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Check backend health
 */
export const checkHealth = async (): Promise<{
  status: string;
  ollama_available: boolean;
  gemini_available: boolean;
}> => {
  const response = await fetch(`${BACKEND_URL}/api/health`);
  if (!response.ok) {
    throw new Error("Backend health check failed");
  }
  return response.json();
};

export enum DocumentType {
  INVOICE = 'Invoice',
  RECEIPT = 'Receipt',
  BANK_STATEMENT = 'Bank Statement',
  INSURANCE_EOB = 'Insurance EOB',
  UNKNOWN = 'Unknown'
}

export interface LineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
  sku?: string;
}

export interface ExtractedData {
  documentType: DocumentType;
  vendorName: string;
  vendorAddress?: string;
  invoiceNumber: string;
  date: string;
  dueDate?: string;
  totalAmount: number;
  taxAmount: number;
  currency: string;
  lineItems: LineItem[];
  summary?: string;
}

export type FileStatus = 'queued' | 'processing' | 'complete' | 'error';

export interface UploadedFile {
  id: string;
  file: File;
  previewUrl: string;
  base64Data: string;
  status: FileStatus;
  extractedData?: ExtractedData | null;
  errorMessage?: string;
  uploadTimestamp: number;
}

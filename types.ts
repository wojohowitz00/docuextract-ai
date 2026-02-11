export enum DocumentType {
  INVOICE = 'Invoice',
  RECEIPT = 'Receipt',
  BILL = 'Bill',
  BANK_STATEMENT = 'Bank Statement',
  INSURANCE_EOB = 'Insurance EOB',
  RESEARCH_PAPER = 'Research Paper',
  FINANCIAL_REPORT = 'Financial Report',
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

  // Common
  date?: string;
  summary?: string;

  // Financial document fields
  vendorName?: string;
  vendorAddress?: string;
  invoiceNumber?: string;
  dueDate?: string;
  totalAmount?: number;
  taxAmount?: number;
  currency?: string;
  lineItems: LineItem[];
  accountNumber?: string;
  billingPeriod?: string;

  // Research paper fields
  title?: string;
  authors?: string[];
  abstract?: string;
  journal?: string;
  doi?: string;
  publicationDate?: string;
  keywords?: string[];
  methodology?: string;
  findings?: string;

  // Financial report fields
  companyName?: string;
  reportType?: string;
  reportPeriod?: string;
  revenue?: number;
  expenses?: number;
  netIncome?: number;
  keyMetrics?: Record<string, any>;
}

export type FileStatus = 'queued' | 'processing' | 'complete' | 'error';

export interface UploadedFile {
  id: string;
  file: File;
  previewUrl: string;
  base64Data: string;
  status: FileStatus;
  extractedData?: ExtractedData | null;
  extractionId?: string;
  errorMessage?: string;
  uploadTimestamp: number;
}

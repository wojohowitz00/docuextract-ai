import React, { useState, useEffect, useCallback } from 'react';
import FileUpload from './components/FileUpload';
import ResultsTable from './components/ResultsTable';
import FileSidebar from './components/FileSidebar';
import { extractDocument } from './services/backendService';
import { UploadedFile } from './types';

const MAX_CONCURRENT_UPLOADS = 2;

const App: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);

  // Queue Processing Logic
  useEffect(() => {
    const processNext = async () => {
      // Check active processing count
      const activeCount = files.filter(f => f.status === 'processing').length;
      if (activeCount >= MAX_CONCURRENT_UPLOADS) return;

      // Find next queued file
      const nextFile = files.find(f => f.status === 'queued');
      if (!nextFile) return;

      // Mark as processing
      setFiles(prev => prev.map(f => f.id === nextFile.id ? { ...f, status: 'processing' } : f));

      try {
        const response = await extractDocument(nextFile.file);
        setFiles(prev => prev.map(f => 
          f.id === nextFile.id ? { 
            ...f, 
            status: 'complete', 
            extractedData: response.data,
            extractionId: response.id 
          } : f
        ));
      } catch (error: any) {
        console.error(`Error processing ${nextFile.file.name}:`, error);
        setFiles(prev => prev.map(f => f.id === nextFile.id ? { 
          ...f, 
          status: 'error', 
          errorMessage: error.message || "Extraction failed." 
        } : f));
      }
    };

    processNext();
  }, [files]); // Dependencies allow effect to run whenever status updates or files are added

  const convertFileToBase64 = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const result = reader.result as string;
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  };

  const handleAddFiles = async (newFiles: File[]) => {
    // Process files to get base64 and create objects
    const newUploadedFiles: UploadedFile[] = await Promise.all(
      newFiles.map(async (file) => {
        const base64Data = await convertFileToBase64(file);
        return {
          id: crypto.randomUUID(),
          file,
          previewUrl: URL.createObjectURL(file),
          base64Data,
          status: 'queued',
          uploadTimestamp: Date.now()
        };
      })
    );

    setFiles(prev => [...prev, ...newUploadedFiles]);
    
    // Auto-select first file if none selected
    if (!selectedFileId && newUploadedFiles.length > 0) {
      setSelectedFileId(newUploadedFiles[0].id);
    }
  };

  const handleRemoveFile = (id: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selection when clicking remove
    setFiles(prev => {
      const fileToRemove = prev.find(f => f.id === id);
      if (fileToRemove) {
        URL.revokeObjectURL(fileToRemove.previewUrl);
      }
      return prev.filter(f => f.id !== id);
    });
    
    if (selectedFileId === id) {
      setSelectedFileId(null);
    }
  };

  const handleDownloadAll = () => {
    // Generate a single merged CSV or trigger multiple downloads
    // Merged CSV is cleaner for "Download All" without a zip library
    const completedFiles = files.filter(f => f.status === 'complete' && f.extractedData);
    
    if (completedFiles.length === 0) return;

    const headers = [
      "File Name", "Document Type", "Vendor", "Invoice #", "Date", "Currency", "Tax", "Total",
      "Item Description", "Qty", "Unit Price", "Item Total"
    ];

    const allRows: any[] = [];

    completedFiles.forEach(file => {
      const data = file.extractedData!;
      data.lineItems.forEach(item => {
        allRows.push([
          `"${file.file.name}"`,
          data.documentType,
          `"${data.vendorName}"`,
          data.invoiceNumber,
          data.date,
          data.currency,
          data.taxAmount,
          data.totalAmount,
          `"${item.description.replace(/"/g, '""')}"`,
          item.quantity,
          item.unitPrice,
          item.total
        ]);
      });
    });

    const csvContent = [
      headers.join(','),
      ...allRows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `financial_extract_batch_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const selectedFile = files.find(f => f.id === selectedFileId);

  // Cleanup effect
  useEffect(() => {
    return () => {
      files.forEach(f => URL.revokeObjectURL(f.previewUrl));
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 z-10 shadow-sm flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-blue-600 text-white p-1.5 rounded-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-800">FinExtract AI</h1>
          </div>
          <div className="text-sm text-slate-500 hidden sm:block">
            Secure Local-First Document Processing
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* Sidebar if files exist */}
        {files.length > 0 && (
          <FileSidebar 
            files={files} 
            selectedId={selectedFileId} 
            onSelect={setSelectedFileId} 
            onRemove={handleRemoveFile}
            onAddFiles={handleAddFiles}
            onDownloadAll={handleDownloadAll}
          />
        )}

        <main className="flex-1 overflow-y-auto bg-slate-100 p-8 relative">
          
          {/* Empty State / Initial Upload */}
          {files.length === 0 ? (
            <div className="max-w-3xl mx-auto space-y-8 mt-12">
              <div className="text-center space-y-4">
                <h2 className="text-3xl font-bold text-slate-900">Extract financial data in seconds</h2>
                <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                  Drag & drop multiple files to start batch processing. Supports Invoices, Receipts, and Bank Statements.
                </p>
              </div>
              
              <FileUpload 
                onFilesSelect={handleAddFiles} 
              />

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8">
                {[
                  { title: 'Invoices', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
                  { title: 'Receipts', icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z' },
                  { title: 'Bank Statements', icon: 'M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M9 7H4v9a2 2 0 002 2h2m2-2h6a2 2 0 012 2v1' }
                ].map((item, i) => (
                  <div key={i} className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4">
                    <div className="bg-indigo-50 text-indigo-600 p-2 rounded-lg">
                       <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} /></svg>
                    </div>
                    <span className="font-semibold text-slate-700">{item.title}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : !selectedFile ? (
            <div className="h-full flex items-center justify-center text-gray-400">
               <p>Select a file from the sidebar to view details</p>
            </div>
          ) : (
            /* Split View for Selected File */
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 h-full">
              
              {/* Left: Preview */}
              <div className="flex flex-col gap-4 h-full min-h-[500px]">
                <div className="flex justify-between items-center">
                   <h3 className="font-semibold text-slate-700">Document Preview</h3>
                </div>
                <div className="flex-1 bg-gray-900 rounded-xl overflow-hidden border border-gray-700 relative flex items-center justify-center shadow-md">
                    {selectedFile.file.type === 'application/pdf' ? (
                      <iframe 
                        src={`${selectedFile.previewUrl}#toolbar=0&navpanes=0`} 
                        className="w-full h-full"
                        title="PDF Preview"
                      />
                    ) : (
                      <img 
                        src={selectedFile.previewUrl} 
                        alt="Preview" 
                        className="max-w-full max-h-full object-contain" 
                      />
                    )}
                </div>
              </div>

              {/* Right: Results */}
              <div className="flex flex-col gap-4 h-full min-h-[500px]">
                <h3 className="font-semibold text-slate-700">Extraction Results</h3>
                
                <div className="flex-1 overflow-y-auto">
                  {selectedFile.status === 'queued' && (
                    <div className="h-full flex flex-col items-center justify-center bg-white rounded-xl border border-gray-200 shadow-sm">
                      <div className="p-4 bg-gray-50 rounded-full mb-3 text-gray-400">
                         <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                      </div>
                      <p className="text-gray-500 font-medium">Queued for processing...</p>
                    </div>
                  )}

                  {selectedFile.status === 'processing' && (
                    <div className="h-full flex flex-col items-center justify-center space-y-6 bg-white rounded-xl border border-dashed border-blue-300 shadow-sm p-8">
                       <div className="relative w-20 h-20">
                          <div className="absolute inset-0 border-4 border-gray-100 rounded-full"></div>
                          <div className="absolute inset-0 border-4 border-blue-500 rounded-full border-t-transparent animate-spin"></div>
                       </div>
                       <div className="text-center">
                         <p className="text-lg font-medium text-gray-900">Scanning Document</p>
                         <p className="text-sm text-gray-500 mt-1">Analyzing line items, taxes, and vendor data...</p>
                       </div>
                    </div>
                  )}

                  {selectedFile.status === 'error' && (
                    <div className="h-full flex items-center justify-center">
                       <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center max-w-md">
                        <div className="text-red-500 mb-4">
                           <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                        </div>
                        <h3 className="text-lg font-bold text-red-900 mb-2">Extraction Failed</h3>
                        <p className="text-red-600 mb-6">{selectedFile.errorMessage}</p>
                        <button 
                          onClick={() => setFiles(prev => prev.map(f => f.id === selectedFile.id ? { ...f, status: 'queued' } : f))}
                          className="bg-white border border-red-300 text-red-700 px-6 py-2 rounded-lg text-sm font-medium hover:bg-red-50 transition"
                        >
                          Retry
                        </button>
                      </div>
                    </div>
                  )}

                  {selectedFile.status === 'complete' && selectedFile.extractedData && (
                    <ResultsTable data={selectedFile.extractedData} />
                  )}
                </div>
              </div>

            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
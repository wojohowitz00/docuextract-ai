import React, { useCallback } from 'react';

interface FileUploadProps {
  onFilesSelect: (files: File[]) => void;
  maxSizeBytes?: number; // Default 10MB
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onFilesSelect, 
  maxSizeBytes = 10 * 1024 * 1024 
}) => {
  
  const validateAndPass = (fileList: FileList | File[]) => {
    const validFiles: File[] = [];
    const errors: string[] = [];

    Array.from(fileList).forEach(file => {
      if (file.size > maxSizeBytes) {
        errors.push(`${file.name} exceeds the 10MB size limit.`);
      } else if (file.type === 'application/pdf' || file.type.startsWith('image/')) {
        validFiles.push(file);
      } else {
        errors.push(`${file.name} is not a valid PDF or Image.`);
      }
    });

    if (errors.length > 0) {
      alert(`Some files were not added:\n${errors.join('\n')}`);
    }

    if (validFiles.length > 0) {
      onFilesSelect(validFiles);
    }
  };

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      validateAndPass(e.dataTransfer.files);
    },
    [maxSizeBytes, onFilesSelect]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndPass(e.target.files);
      // Reset input value so the same file can be selected again if needed
      e.target.value = '';
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      className="relative border-2 border-dashed border-blue-300 rounded-xl p-12 text-center transition-all duration-200 ease-in-out bg-blue-50/50 hover:bg-blue-50 hover:border-blue-500 cursor-pointer"
    >
      <input
        type="file"
        accept="image/*,.pdf"
        multiple
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        onChange={handleChange}
      />
      
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="p-4 bg-blue-100 text-blue-600 rounded-full">
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M9 7H4v9a2 2 0 002 2h2m2-2h6a2 2 0 012 2v1" />
          </svg>
        </div>
        <div>
          <p className="text-lg font-medium text-gray-900">
            Drop invoices & receipts here
          </p>
          <p className="text-sm text-gray-500 mt-1">
            Batch upload supported • PDF, JPG, PNG • Max 10MB
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
import React from 'react';
import { UploadedFile } from '../types';

interface FileSidebarProps {
  files: UploadedFile[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRemove: (id: string, e: React.MouseEvent) => void;
  onAddFiles: (files: File[]) => void;
  onDownloadAll: () => void;
}

const FileSidebar: React.FC<FileSidebarProps> = ({ 
  files, 
  selectedId, 
  onSelect, 
  onRemove, 
  onAddFiles,
  onDownloadAll
}) => {
  const hiddenInputRef = React.useRef<HTMLInputElement>(null);

  const handleAddClick = () => {
    hiddenInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onAddFiles(Array.from(e.target.files));
      e.target.value = '';
    }
  };

  const getStatusIcon = (file: UploadedFile) => {
    switch (file.status) {
      case 'processing':
        return (
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        );
      case 'complete':
        return (
          <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default: // queued
        return (
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  // Check if any files are completed to enable download all
  const hasCompletedFiles = files.some(f => f.status === 'complete');

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h2 className="font-semibold text-gray-700">Documents ({files.length})</h2>
        <button 
          onClick={handleAddClick}
          className="p-1.5 text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
          title="Add more files"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <input 
          type="file" 
          ref={hiddenInputRef} 
          multiple 
          className="hidden" 
          accept="image/*,.pdf"
          onChange={handleFileChange} 
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {files.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">
            No files in queue.
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {files.map((file) => (
              <li 
                key={file.id}
                onClick={() => onSelect(file.id)}
                className={`
                  relative p-4 cursor-pointer hover:bg-gray-50 transition-colors group
                  ${selectedId === file.id ? 'bg-blue-50/60 border-l-4 border-blue-500' : 'border-l-4 border-transparent'}
                `}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-gray-200 rounded-lg overflow-hidden flex-shrink-0 border border-gray-300">
                    {file.file.type === 'application/pdf' ? (
                       <div className="w-full h-full flex items-center justify-center bg-red-50 text-red-500 text-xs font-bold">PDF</div>
                    ) : (
                      <img src={file.previewUrl} alt="thumb" className="w-full h-full object-cover" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${selectedId === file.id ? 'text-blue-700' : 'text-gray-900'}`}>
                      {file.file.name}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {getStatusIcon(file)}
                      <span className={`text-xs capitalize ${
                        file.status === 'error' ? 'text-red-500' : 
                        file.status === 'complete' ? 'text-emerald-600' : 
                        'text-gray-500'
                      }`}>
                        {file.status}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => onRemove(file.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                    title="Remove file"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {hasCompletedFiles && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onDownloadAll}
            className="w-full flex justify-center items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium py-2.5 rounded-lg transition-colors shadow-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download All CSVs
          </button>
        </div>
      )}
    </div>
  );
};

export default FileSidebar;
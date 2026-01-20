import React from 'react';
import { ExtractedData } from '../types';

interface ResultsTableProps {
  data: ExtractedData;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {
  
  const downloadCSV = () => {
    // Flatten data for CSV: Repeat header info for every line item
    const headers = [
      "Document Type", "Vendor", "Invoice #", "Date", "Currency", "Tax", "Total",
      "Item Description", "Qty", "Unit Price", "Item Total"
    ];

    const rows = data.lineItems.map(item => [
      data.documentType,
      data.vendorName,
      data.invoiceNumber,
      data.date,
      data.currency,
      data.taxAmount,
      data.totalAmount,
      // Line Item specifics
      `"${item.description.replace(/"/g, '""')}"`, // Escape quotes
      item.quantity,
      item.unitPrice,
      item.total
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `extract_${data.vendorName}_${data.date}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{data.vendorName}</h2>
          <p className="text-sm text-gray-500 uppercase tracking-wide font-semibold mt-1">
            {data.documentType} • {data.date}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Total Amount</p>
          <p className="text-2xl font-bold text-emerald-600">
            {new Intl.NumberFormat('en-US', { style: 'currency', currency: data.currency || 'USD' }).format(data.totalAmount)}
          </p>
        </div>
      </div>

      <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-sm">
        <div>
          <span className="block text-gray-500 mb-1">Invoice Number</span>
          <span className="font-medium text-gray-900">{data.invoiceNumber || 'N/A'}</span>
        </div>
        <div>
          <span className="block text-gray-500 mb-1">Due Date</span>
          <span className="font-medium text-gray-900">{data.dueDate || 'N/A'}</span>
        </div>
        <div>
          <span className="block text-gray-500 mb-1">Tax Amount</span>
          <span className="font-medium text-gray-900">
             {new Intl.NumberFormat('en-US', { style: 'currency', currency: data.currency || 'USD' }).format(data.taxAmount)}
          </span>
        </div>
         <div className="col-span-2 md:col-span-4">
          <span className="block text-gray-500 mb-1">Summary</span>
          <span className="text-gray-700 italic">{data.summary || 'No summary available.'}</span>
        </div>
      </div>

      <div className="border-t border-gray-100">
        <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider grid grid-cols-12 gap-4">
          <div className="col-span-6">Description</div>
          <div className="col-span-2 text-right">Qty</div>
          <div className="col-span-2 text-right">Price</div>
          <div className="col-span-2 text-right">Total</div>
        </div>
        <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
          {data.lineItems.map((item, idx) => (
            <div key={idx} className="px-6 py-4 grid grid-cols-12 gap-4 text-sm hover:bg-gray-50 transition-colors">
              <div className="col-span-6 text-gray-900 font-medium truncate">{item.description}</div>
              <div className="col-span-2 text-right text-gray-600">{item.quantity}</div>
              <div className="col-span-2 text-right text-gray-600">{item.unitPrice.toFixed(2)}</div>
              <div className="col-span-2 text-right text-gray-900 font-semibold">{item.total.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-end">
        <button
          onClick={downloadCSV}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-sm"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download CSV
        </button>
      </div>
    </div>
  );
};

export default ResultsTable;
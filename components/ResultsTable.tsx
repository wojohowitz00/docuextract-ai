import React from 'react';
import { ExtractedData, DocumentType } from '../types';

interface ResultsTableProps {
  data: ExtractedData;
}

const fmt = (amount: number | undefined, currency: string = 'USD') =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount ?? 0);

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {

  const downloadCSV = () => {
    const docType = data.documentType;
    let headers: string[];
    let rows: any[][];

    if (docType === DocumentType.RESEARCH_PAPER) {
      headers = ["Document Type", "Title", "Authors", "Journal", "Date", "DOI", "Keywords", "Abstract", "Methodology", "Findings"];
      rows = [[
        data.documentType,
        data.title || '',
        (data.authors || []).join('; '),
        data.journal || '',
        data.date || '',
        data.doi || '',
        (data.keywords || []).join('; '),
        `"${(data.abstract || '').replace(/"/g, '""')}"`,
        `"${(data.methodology || '').replace(/"/g, '""')}"`,
        `"${(data.findings || '').replace(/"/g, '""')}"`
      ]];
    } else if (docType === DocumentType.FINANCIAL_REPORT) {
      headers = ["Document Type", "Company", "Report Type", "Period", "Revenue", "Expenses", "Net Income", "Summary"];
      rows = [[
        data.documentType,
        data.companyName || '',
        data.reportType || '',
        data.reportPeriod || '',
        data.revenue ?? '',
        data.expenses ?? '',
        data.netIncome ?? '',
        `"${(data.summary || '').replace(/"/g, '""')}"`
      ]];
      // Add key metrics as additional rows
      if (data.keyMetrics) {
        Object.entries(data.keyMetrics).forEach(([k, v]) => {
          rows.push(['', '', k, '', '', '', String(v), '']);
        });
      }
    } else {
      headers = [
        "Document Type", "Vendor", "Invoice #", "Date", "Currency", "Tax", "Total",
        "Item Description", "Qty", "Unit Price", "Item Total"
      ];
      rows = data.lineItems.map(item => [
        data.documentType,
        `"${data.vendorName || ''}"`,
        data.invoiceNumber || '',
        data.date || '',
        data.currency || 'USD',
        data.taxAmount ?? 0,
        data.totalAmount ?? 0,
        `"${item.description.replace(/"/g, '""')}"`,
        item.quantity,
        item.unitPrice,
        item.total
      ]);
    }

    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const name = data.vendorName || data.title || data.companyName || 'extraction';
    link.setAttribute('href', url);
    link.setAttribute('download', `extract_${name}_${data.date || 'undated'}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ── Research Paper View ──────────────────────────────────────────────────

  if (data.documentType === DocumentType.RESEARCH_PAPER) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50">
          <p className="text-sm text-gray-500 uppercase tracking-wide font-semibold mb-2">
            {data.documentType} • {data.publicationDate || data.date || 'Date unknown'}
          </p>
          <h2 className="text-xl font-bold text-gray-800">{data.title || 'Untitled Paper'}</h2>
          {data.authors && data.authors.length > 0 && (
            <p className="text-sm text-gray-600 mt-2">{data.authors.join(', ')}</p>
          )}
        </div>

        <div className="p-6 space-y-5">
          {data.journal && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Journal / Conference</span>
              <span className="font-medium text-gray-900">{data.journal}</span>
            </div>
          )}
          {data.doi && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">DOI</span>
              <a href={`https://doi.org/${data.doi}`} target="_blank" rel="noreferrer"
                className="font-medium text-blue-600 hover:underline">{data.doi}</a>
            </div>
          )}
          {data.keywords && data.keywords.length > 0 && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Keywords</span>
              <div className="flex flex-wrap gap-2 mt-1">
                {data.keywords.map((kw, i) => (
                  <span key={i} className="bg-indigo-50 text-indigo-700 text-xs px-2.5 py-1 rounded-full font-medium">{kw}</span>
                ))}
              </div>
            </div>
          )}
          {data.abstract && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Abstract</span>
              <p className="text-gray-700 text-sm leading-relaxed">{data.abstract}</p>
            </div>
          )}
          {data.methodology && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Methodology</span>
              <p className="text-gray-700 text-sm leading-relaxed">{data.methodology}</p>
            </div>
          )}
          {data.findings && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Key Findings</span>
              <p className="text-gray-700 text-sm leading-relaxed">{data.findings}</p>
            </div>
          )}
          {data.summary && (
            <div className="pt-3 border-t border-gray-100">
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Summary</span>
              <p className="text-gray-600 italic text-sm">{data.summary}</p>
            </div>
          )}
        </div>

        <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button onClick={downloadCSV}
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
  }

  // ── Financial Report View ────────────────────────────────────────────────

  if (data.documentType === DocumentType.FINANCIAL_REPORT) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50">
          <p className="text-sm text-gray-500 uppercase tracking-wide font-semibold mb-2">
            {data.reportType || data.documentType} • {data.reportPeriod || data.date || 'Period unknown'}
          </p>
          <h2 className="text-xl font-bold text-gray-800">{data.companyName || 'Unknown Company'}</h2>
        </div>

        <div className="p-6 grid grid-cols-2 md:grid-cols-3 gap-6">
          {data.revenue != null && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Revenue</span>
              <span className="text-lg font-bold text-emerald-600">{fmt(data.revenue, data.currency)}</span>
            </div>
          )}
          {data.expenses != null && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Expenses</span>
              <span className="text-lg font-bold text-red-500">{fmt(data.expenses, data.currency)}</span>
            </div>
          )}
          {data.netIncome != null && (
            <div>
              <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Net Income</span>
              <span className={`text-lg font-bold ${(data.netIncome ?? 0) >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                {fmt(data.netIncome, data.currency)}
              </span>
            </div>
          )}
        </div>

        {data.keyMetrics && Object.keys(data.keyMetrics).length > 0 && (
          <div className="px-6 pb-6">
            <span className="block text-xs text-gray-500 uppercase tracking-wider mb-3">Key Metrics</span>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(data.keyMetrics).map(([key, val]) => (
                <div key={key} className="bg-gray-50 rounded-lg p-3">
                  <span className="block text-xs text-gray-500 mb-0.5">{key}</span>
                  <span className="font-semibold text-gray-900">{typeof val === 'number' ? val.toLocaleString() : String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.lineItems.length > 0 && (
          <div className="border-t border-gray-100">
            <div className="bg-gray-50 px-6 py-3 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider grid grid-cols-12 gap-4">
              <div className="col-span-8">Item</div>
              <div className="col-span-4 text-right">Amount</div>
            </div>
            <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
              {data.lineItems.map((item, idx) => (
                <div key={idx} className="px-6 py-4 grid grid-cols-12 gap-4 text-sm hover:bg-gray-50 transition-colors">
                  <div className="col-span-8 text-gray-900 font-medium">{item.description}</div>
                  <div className="col-span-4 text-right text-gray-900 font-semibold">{item.total.toLocaleString()}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.summary && (
          <div className="px-6 py-4 border-t border-gray-100">
            <span className="block text-xs text-gray-500 uppercase tracking-wider mb-1">Summary</span>
            <p className="text-gray-600 italic text-sm">{data.summary}</p>
          </div>
        )}

        <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button onClick={downloadCSV}
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
  }

  // ── Financial Document View (Invoice, Receipt, Bill, etc.) ───────────────

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{data.vendorName || 'Unknown Vendor'}</h2>
          <p className="text-sm text-gray-500 uppercase tracking-wide font-semibold mt-1">
            {data.documentType} • {data.date || 'Date unknown'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm text-gray-500">Total Amount</p>
          <p className="text-2xl font-bold text-emerald-600">
            {fmt(data.totalAmount, data.currency)}
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
          <span className="font-medium text-gray-900">{fmt(data.taxAmount, data.currency)}</span>
        </div>
        {data.accountNumber && (
          <div>
            <span className="block text-gray-500 mb-1">Account #</span>
            <span className="font-medium text-gray-900">{data.accountNumber}</span>
          </div>
        )}
        {data.billingPeriod && (
          <div>
            <span className="block text-gray-500 mb-1">Billing Period</span>
            <span className="font-medium text-gray-900">{data.billingPeriod}</span>
          </div>
        )}
        <div className="col-span-2 md:col-span-4">
          <span className="block text-gray-500 mb-1">Summary</span>
          <span className="text-gray-700 italic">{data.summary || 'No summary available.'}</span>
        </div>
      </div>

      {data.lineItems.length > 0 && (
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
      )}

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
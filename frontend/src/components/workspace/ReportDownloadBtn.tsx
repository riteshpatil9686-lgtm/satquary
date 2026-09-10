import React from 'react';
import { FileDown } from 'lucide-react';
import { getReportUrl } from '../../services/api';

interface ReportDownloadBtnProps {
  jobId: string;
}

export const ReportDownloadBtn: React.FC<ReportDownloadBtnProps> = ({ jobId }) => (
  <a
    href={getReportUrl(jobId)}
    download={`satquery_report_${jobId.slice(0, 8)}.pdf`}
    target="_blank"
    rel="noopener noreferrer"
    className="btn-secondary flex items-center justify-center gap-2 w-full text-center"
  >
    <FileDown size={13} />
    <span className="text-xs">Download PDF Report</span>
  </a>
);

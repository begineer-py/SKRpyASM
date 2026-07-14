import jsPDF from 'jspdf';
import type { VulnerabilityData, PoCRecord } from '../services/api_vulnerabilities';

// ==========================================
// PDF-specific constants (English labels for CJK compatibility)
// jsPDF built-in fonts don't support Chinese, so we use English in PDF
// ==========================================

const SEVERITY_LABEL_PDF = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
  info: 'INFO',
} as const;

const STATUS_LABEL_PDF = {
  unverified: 'Unverified',
  confirmed: 'Confirmed',
  false_positive: 'False Positive',
} as const;

const ENRICHMENT_LABEL_PDF = {
  pending: 'Pending',
  enriched: 'Enriched',
  no_cve: 'No CVE',
  failed: 'Failed',
} as const;

const POC_LANGUAGE_LABEL_PDF = {
  curl: 'cURL',
  python: 'Python',
  bash: 'Bash',
  http_request: 'HTTP Request',
  manual: 'Manual Steps',
} as const;

// ==========================================
// Layout constants
// ==========================================

const PAGE_WIDTH = 210; // A4 width in mm
const PAGE_HEIGHT = 297; // A4 height in mm
const MARGIN = 15;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2; // 180mm
const LINE_HEIGHT = 5;
const SECTION_GAP = 8;

// Colors (professional dark theme with green accent)
const COLOR_ACCENT = '#22C55E'; // SKRpyASM green
const COLOR_BG_DARK = '#1F2937';
const COLOR_BG_LIGHT = '#F3F4F6';
const COLOR_TEXT_PRIMARY = '#111827';
const COLOR_TEXT_SECONDARY = '#6B7280';
const COLOR_BORDER = '#E5E7EB';

// ==========================================
// Helper functions
// ==========================================

function fmtDatePdf(iso: string | null): string {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

function labelOrRawPdf<T extends string>(
  map: Readonly<Record<string, string>>,
  key: T | string,
): string {
  return map[key] ?? key;
}

// ==========================================
// PDF rendering helpers
// ==========================================

interface PdfContext {
  doc: jsPDF;
  y: number;
}

function checkPageBreak(ctx: PdfContext, neededHeight: number): void {
  if (ctx.y + neededHeight > PAGE_HEIGHT - MARGIN) {
    ctx.doc.addPage();
    ctx.y = MARGIN;
  }
}

function drawText(ctx: PdfContext, text: string, options: {
  size?: number;
  style?: 'normal' | 'bold' | 'italic';
  color?: string;
  maxWidth?: number;
  align?: 'left' | 'center' | 'right';
}): number {
  const { size = 10, style = 'normal', color = COLOR_TEXT_PRIMARY, maxWidth = CONTENT_WIDTH, align = 'left' } = options;

  ctx.doc.setFontSize(size);
  ctx.doc.setFont('helvetica', style);
  ctx.doc.setTextColor(color);

  const lines = ctx.doc.splitTextToSize(text, maxWidth);
  const lineHeight = size * 0.35 + 1; // Approximate line height in mm

  lines.forEach((line: string) => {
    checkPageBreak(ctx, lineHeight);
    const x = align === 'center' ? PAGE_WIDTH / 2 : align === 'right' ? PAGE_WIDTH - MARGIN : MARGIN;
    ctx.doc.text(line, x, ctx.y, { align });
    ctx.y += lineHeight;
  });

  return lines.length * lineHeight;
}

function drawSectionTitle(ctx: PdfContext, title: string): void {
  checkPageBreak(ctx, SECTION_GAP + LINE_HEIGHT);
  ctx.y += SECTION_GAP / 2;

  // Green accent bar
  ctx.doc.setFillColor(COLOR_ACCENT);
  ctx.doc.rect(MARGIN, ctx.y - 2, 2, 6, 'F');

  // Title text
  ctx.doc.setFontSize(14);
  ctx.doc.setFont('helvetica', 'bold');
  ctx.doc.setTextColor(COLOR_TEXT_PRIMARY);
  ctx.doc.text(title, MARGIN + 5, ctx.y + 2);

  ctx.y += SECTION_GAP;
}

function drawTableRow(ctx: PdfContext, label: string, value: string, isHeader = false): void {
  const rowHeight = 7;
  checkPageBreak(ctx, rowHeight);

  const bgColor = isHeader ? COLOR_BG_DARK : (ctx.y % 14 < 7 ? COLOR_BG_LIGHT : '#FFFFFF');
  ctx.doc.setFillColor(bgColor);
  ctx.doc.rect(MARGIN, ctx.y, CONTENT_WIDTH, rowHeight, 'F');

  // Label column (40% width)
  ctx.doc.setFontSize(9);
  ctx.doc.setFont('helvetica', 'bold');
  ctx.doc.setTextColor(isHeader ? '#FFFFFF' : COLOR_TEXT_PRIMARY);
  ctx.doc.text(label, MARGIN + 2, ctx.y + 4.5);

  // Value column (60% width)
  ctx.doc.setFont('helvetica', 'normal');
  ctx.doc.setTextColor(isHeader ? '#FFFFFF' : COLOR_TEXT_SECONDARY);
  const valueLines = ctx.doc.splitTextToSize(value, CONTENT_WIDTH * 0.58);
  ctx.doc.text(valueLines[0] || '', MARGIN + CONTENT_WIDTH * 0.4 + 2, ctx.y + 4.5);

  ctx.y += rowHeight;
}

function drawCodeBlock(ctx: PdfContext, code: string, language = ''): void {
  const codeLines = code.split('\n');
  const lineHeight = 4;
  const blockHeight = codeLines.length * lineHeight + 4;

  checkPageBreak(ctx, Math.min(blockHeight, 50)); // At least 50mm before breaking

  // Background
  ctx.doc.setFillColor('#F9FAFB');
  ctx.doc.setDrawColor(COLOR_BORDER);
  ctx.doc.rect(MARGIN, ctx.y, CONTENT_WIDTH, blockHeight, 'FD');

  // Language label (if provided)
  if (language) {
    ctx.doc.setFontSize(7);
    ctx.doc.setFont('helvetica', 'italic');
    ctx.doc.setTextColor(COLOR_TEXT_SECONDARY);
    ctx.doc.text(language.toUpperCase(), MARGIN + 2, ctx.y + 3);
  }

  // Code text
  ctx.doc.setFontSize(8);
  ctx.doc.setFont('courier', 'normal');
  ctx.doc.setTextColor(COLOR_TEXT_PRIMARY);

  let codeY = ctx.y + (language ? 6 : 3);
  codeLines.forEach((line) => {
    if (codeY > PAGE_HEIGHT - MARGIN) {
      ctx.doc.addPage();
      codeY = MARGIN + 3;
    }
    ctx.doc.text(line.substring(0, 100), MARGIN + 2, codeY); // Truncate long lines
    codeY += lineHeight;
  });

  ctx.y += blockHeight + 2;
}

// ==========================================
// Section renderers
// ==========================================

function renderHeader(ctx: PdfContext, v: VulnerabilityData): void {
  // Green accent bar at top
  ctx.doc.setFillColor(COLOR_ACCENT);
  ctx.doc.rect(0, 0, PAGE_WIDTH, 8, 'F');

  ctx.y = MARGIN + 5;

  // Title
  drawText(ctx, `Vulnerability Report: ${v.name || 'Unnamed'}`, {
    size: 18,
    style: 'bold',
    color: COLOR_TEXT_PRIMARY,
  });

  // Severity badge
  const severity = labelOrRawPdf(SEVERITY_LABEL_PDF, v.severity);
  const badgeWidth = ctx.doc.getTextWidth(severity) + 8;
  ctx.doc.setFillColor(COLOR_ACCENT);
  ctx.doc.rect(MARGIN, ctx.y + 2, badgeWidth, 6, 'F');
  ctx.doc.setFontSize(9);
  ctx.doc.setFont('helvetica', 'bold');
  ctx.doc.setTextColor('#FFFFFF');
  ctx.doc.text(severity, MARGIN + 4, ctx.y + 6);

  ctx.y += 12;
}

function renderBasicInfo(ctx: PdfContext, v: VulnerabilityData): void {
  drawSectionTitle(ctx, 'Basic Information');

  drawTableRow(ctx, 'Vulnerability ID', `#${v.id}`, true);
  drawTableRow(ctx, 'Severity', labelOrRawPdf(SEVERITY_LABEL_PDF, v.severity));
  drawTableRow(ctx, 'Status', labelOrRawPdf(STATUS_LABEL_PDF, v.status));
  if (v.target_name) drawTableRow(ctx, 'Target Asset', v.target_name);
  drawTableRow(ctx, 'Matched At', v.matched_at || '—');
  if (v.tool_source) drawTableRow(ctx, 'Tool Source', v.tool_source);
  if (v.template_id) drawTableRow(ctx, 'Template ID', v.template_id);
  drawTableRow(ctx, 'CVE Enrichment', labelOrRawPdf(ENRICHMENT_LABEL_PDF, v.enrichment_status));
  if (v.cve_intelligence_id) drawTableRow(ctx, 'Related CVE', `#${v.cve_intelligence_id}`);
  drawTableRow(ctx, 'First Seen', fmtDatePdf(v.created_at));
  drawTableRow(ctx, 'Last Seen', fmtDatePdf(v.last_seen));
  drawTableRow(ctx, 'Last Updated', fmtDatePdf(v.updated_at));

  ctx.y += 2;
}

function renderAssets(ctx: PdfContext, v: VulnerabilityData): void {
  const assets: string[] = [];
  if (v.ip_asset) assets.push(`IP: ${v.ip_asset.label}`);
  if (v.subdomain_asset) assets.push(`Subdomain: ${v.subdomain_asset.label}`);
  if (v.url_asset) assets.push(`URL: ${v.url_asset.label}`);

  if (assets.length === 0) return;

  drawSectionTitle(ctx, 'Related Assets');
  assets.forEach((asset) => {
    drawText(ctx, `• ${asset}`, { size: 9, color: COLOR_TEXT_SECONDARY });
  });
  ctx.y += 2;
}

function renderDescription(ctx: PdfContext, v: VulnerabilityData): void {
  const desc = v.description?.trim();
  if (!desc) return;

  drawSectionTitle(ctx, 'Description');
  drawText(ctx, desc, { size: 10, color: COLOR_TEXT_PRIMARY });
  ctx.y += 2;
}

function renderPoc(ctx: PdfContext, poc: PoCRecord, idx: number): void {
  const verified = poc.is_verified ? ' ✓' : '';
  const lang = labelOrRawPdf(POC_LANGUAGE_LABEL_PDF, poc.language);

  drawText(ctx, `${idx + 1}. ${poc.title}${verified}`, {
    size: 11,
    style: 'bold',
    color: COLOR_TEXT_PRIMARY,
  });

  drawText(ctx, `Language: ${lang}`, {
    size: 8,
    color: COLOR_TEXT_SECONDARY,
  });

  ctx.y += 1;
  drawCodeBlock(ctx, poc.content, poc.language);

  if (poc.result?.trim()) {
    drawText(ctx, 'Execution Result:', {
      size: 9,
      style: 'italic',
      color: COLOR_TEXT_SECONDARY,
    });
    ctx.y += 1;
    drawCodeBlock(ctx, poc.result.trim());
  }

  ctx.y += 3;
}

function renderPocs(ctx: PdfContext, v: VulnerabilityData): void {
  if (!v.pocs || v.pocs.length === 0) return;

  drawSectionTitle(ctx, 'Proof of Concept (POC)');
  v.pocs.forEach((poc, idx) => renderPoc(ctx, poc, idx));
}

function renderRawRequest(ctx: PdfContext, v: VulnerabilityData): void {
  const raw = v.request_raw?.trim();
  if (!raw) return;

  drawSectionTitle(ctx, 'Raw Request');
  drawCodeBlock(ctx, raw, 'http');
}

function renderRawResponse(ctx: PdfContext, v: VulnerabilityData): void {
  const raw = v.response_raw?.trim();
  if (!raw) return;

  drawSectionTitle(ctx, 'Raw Response');
  drawCodeBlock(ctx, raw, 'http');
}

function renderExtractedResults(ctx: PdfContext, v: VulnerabilityData): void {
  if (v.extracted_results == null) return;

  const ext =
    typeof v.extracted_results === 'string'
      ? v.extracted_results
      : JSON.stringify(v.extracted_results, null, 2);

  if (!ext || !ext.trim() || ext.trim() === 'null') return;

  drawSectionTitle(ctx, 'Extracted Results');
  drawCodeBlock(ctx, ext.trim(), 'json');
}

function renderRemediation(ctx: PdfContext, v: VulnerabilityData): void {
  const rem = v.remediation?.trim();
  if (!rem) return;

  drawSectionTitle(ctx, 'Remediation');
  drawText(ctx, rem, { size: 10, color: COLOR_TEXT_PRIMARY });
  ctx.y += 2;
}

function renderFooter(ctx: PdfContext): void {
  const totalPages = ctx.doc.getNumberOfPages();

  for (let i = 1; i <= totalPages; i++) {
    ctx.doc.setPage(i);

    // Footer line
    ctx.doc.setDrawColor(COLOR_BORDER);
    ctx.doc.line(MARGIN, PAGE_HEIGHT - MARGIN + 2, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 2);

    // Timestamp
    ctx.doc.setFontSize(7);
    ctx.doc.setFont('helvetica', 'italic');
    ctx.doc.setTextColor(COLOR_TEXT_SECONDARY);
    ctx.doc.text(
      `Generated by SKRpyASM — ${fmtDatePdf(new Date().toISOString())}`,
      MARGIN,
      PAGE_HEIGHT - MARGIN + 5,
    );

    // Page number
    ctx.doc.text(`Page ${i} / ${totalPages}`, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 5, {
      align: 'right',
    });
  }
}

// ==========================================
// Main PDF generation function
// ==========================================

export function generateVulnPdf(v: VulnerabilityData): jsPDF {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
    compress: true,
  });

  const ctx: PdfContext = { doc, y: MARGIN };

  renderHeader(ctx, v);
  renderBasicInfo(ctx, v);
  renderAssets(ctx, v);
  renderDescription(ctx, v);
  renderPocs(ctx, v);
  renderRawRequest(ctx, v);
  renderRawResponse(ctx, v);
  renderExtractedResults(ctx, v);
  renderRemediation(ctx, v);
  renderFooter(ctx);

  return doc;
}

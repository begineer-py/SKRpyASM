import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { executionApi, type ContentBlobPage } from '../services/executionApi';

interface BlobPageViewerProps {
  blobId: number;
  page: number;
}

export function BlobPageViewer({ blobId, page }: BlobPageViewerProps) {
  const [data, setData] = useState<ContentBlobPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    executionApi
      .getBlobPage(blobId, page)
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setData(null);
          setError(err instanceof Error ? err.message : 'Failed to load page');
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [blobId, page]);

  if (loading) return <div className="blob-page-viewer blob-page-viewer--loading">Loading page {page}…</div>;
  if (error) return <div className="blob-page-viewer blob-page-viewer--error">{error}</div>;
  if (!data) return null;

  return (
    <div className="blob-page-viewer" data-testid={`blob-page-${blobId}-${page}`}>
      <div className="blob-page-title">
        P{data.page}/{data.total_pages}: {data.title}
      </div>
      <div className="blob-page-content">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{data.content || '_(empty page)_'}</ReactMarkdown>
      </div>
    </div>
  );
}

export default BlobPageViewer;

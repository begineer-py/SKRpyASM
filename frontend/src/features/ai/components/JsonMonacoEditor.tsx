import MonacoPane from '../../vulnerability/components/MonacoPane';

interface JsonMonacoEditorProps {
  /** 當前的 JSON 字串內容（由呼叫端負責序列化）。 */
  value: string;
  /** 內容變更回呼，回傳原始字串（尚未解析）。 */
  onChange: (v: string) => void;
  /** 編輯器高度；預設填滿父容器。 */
  height?: string | number;
  /** 是否唯讀。 */
  readOnly?: boolean;
  /** 空白時的提示文字。 */
  placeholder?: string;
}

/**
 * JSON 專用的 Monaco 編輯器薄包裝。
 *
 * 單純 passthrough 到 MonacoPane 並鎖定 language='json'，
 * 讓 OverviewDetailPage 的 JSON 欄位獲得語法高亮與 JSON 驗證，
 * 取代原本的 `<textarea>`。
 */
export default function JsonMonacoEditor({
  value,
  onChange,
  height,
  readOnly,
  placeholder,
}: JsonMonacoEditorProps) {
  return (
    <MonacoPane
      language="json"
      value={value}
      onChange={onChange}
      height={height}
      readOnly={readOnly}
      placeholder={placeholder}
    />
  );
}

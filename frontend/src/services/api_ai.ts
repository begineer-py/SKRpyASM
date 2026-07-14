import { createApiClient } from './apiClient';

const aiApi = createApiClient('analyze_ai');
interface AnalyzeSubdomainsPayload {
  subdomains: string[];
}
interface AnalyzeSuccessResponse {
  detail: string;  
}

export const AiAnalysisService = {
  /**
   * 觸發對單個或多個子域名的 AI 分析
   * @param subdomains 一個包含子域名字符串的數組
   */
  analyzeSubdomains: async (subdomains: string[]): Promise<AnalyzeSuccessResponse> => {
    try {
      const payload: AnalyzeSubdomainsPayload = { subdomains };
      // POST /analyze_ai/subdomains
      const response = await aiApi.post<AnalyzeSuccessResponse>('/subdomains', payload);
      return response.data;
    } catch (error: any) {
      console.error('AI Analysis Trigger Failed:', error.response?.data || error.message);
      // 拋出一個用戶可讀的錯誤
      throw new Error(error.response?.data?.detail || '請求 AI 分析失敗');
    }
  }
};

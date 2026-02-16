// hardcore_test.js - 專門用來搞死靜態分析工具的

const API_BASE = "https://api.target.com";
let version = "v2";

// 1. [難度: 中] 樣板字串 (Template Literals) + 變數拼接
// jsluice 應該要能識別這是個 URL，但參數部分可能會變成通配符
const userEndpoint = `/api/${version}/user/profile?ref=header&mode=dark`;

// 2. [難度: 高] Fetch 請求 + JSON Body
// 這是我們最想測的：它能抓到 body 裡的 'username' 和 'secret_code' 嗎？
fetch("/auth/login", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    username: "admin",
    secret_code: "123456", // 這是 POST 參數
    device_id: "uuid-v4",
  }),
});

// 3. [難度: 中] Axios 風格 (常見於 React/Vue)
// 這裡沒有顯式的 URL，只有路徑，且參數是物件形式
axios.post("/api/order/create", {
  product_id: 999,
  quantity: 1,
  coupon: "DISCOUNT2024", // Body 參數
});

// 4. [難度: 高] URLSearchParams 建構子
// 這是現代瀏覽器標準 API，很多工具會漏掉這裡的 key
const params = new URLSearchParams({
  search: "keywords",
  page: "1",
  sort: "desc",
});
const fullUrl = `/search/results?${params.toString()}`;

// 5. [難度: 極高] 舊式字串拼接 + 隱藏在變數中
// 這種通常靜態分析會放棄，因為它不知道 base 是什麼
const path = "/admin/panel/";
const action = "delete_user";
const query = "?id=55";
const obscureLink = path + action + query;

// 6. [難度: 低] 傳統定義 (用來對照)
var config = {
  endpoints: {
    upload: "/files/upload_endpoint",
    status: "/system/health_check?format=json",
  },
};

// 7. [難度: 高] jQuery 風格的 data 物件
$.ajax({
  url: "/legacy/api/update",
  method: "PUT",
  data: {
    csrf_token: "xyz987",
    new_email: "test@test.com",
  },
});

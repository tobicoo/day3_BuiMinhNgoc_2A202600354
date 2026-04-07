# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Bùi Minh Ngọc
- **Student ID**: 2A202600354
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

### Các Module Đã Triển Khai

| Module | Mô tả |
| :--- | :--- |
| `src/tools/basic_tools.py` | Toàn bộ 5 travel tools: `check_weather`, `get_attractions`, `search_flights`, `search_hotels`, `calculate_total_cost` |
| `src/agent/agent.py` | Vòng lặp ReAct |
| `chatbot.py` | Chatbot baseline đơn giản để so sánh với ReAct Agent |

### Điểm Nổi Bật: Thiết Kế Tool Nhận 1 Tham Số

Một quyết định kỹ thuật quan trọng: tất cả tool function phải nhận **một chuỗi duy nhất** (`args: str`) vì `_execute_tool` trong agent gọi theo dạng `tool['func'](args)`.

### Tích Hợp Telemetry vào Agent

```python
# src/agent/agent.py — gọi tracker sau mỗi lần LLM phản hồi
tracker.track_request(
    provider=result.get("provider", "unknown"),
    model=self.llm.model_name,
    usage=result.get("usage", {}),
    latency_ms=result.get("latency_ms", 0),
)
```

---

## II. Debugging Case Study (10 Points)

### Vấn Đề: Agent Ảo Giác Tool Không Tồn Tại

**Mô Tả Vấn Đề:**
Khi hỏi *"vì sao không thể tạo ảnh trực tiếp"*, agent gọi tool `search_web` ( tool này đã bị xóa rồi ). Agent không báo lỗi mà vẫn nhận kết quả rỗng.

**Log Source** — `logs/2026-04-06.log` (dòng 19-21):
```json
{"event": "AGENT_STEP", "data": {"step": 0, "response":
  "Thought: Câu hỏi này khá mơ hồ...\nAction: search_web(lý do không thể tạo ảnh trực tiếp)"}}

{"event": "TOOL_CALL", "data": {
  "tool": "search_web",
  "args": "lý do không thể tạo ảnh trực tiếp",
  "result": "Không tìm thấy kết quả."}}
```

**Chẩn Đoán:**
Tool `search_web` tồn tại trong **system prompt cũ** nhưng đã bị xóa khỏi `get_all_tools()`. LLM nhớ tên tool từ context prompt cũ và tiếp tục gọi.

**Giải Pháp:**
System prompt được cập nhật để chỉ liệt kê đúng 5 tool hiện có. Tool descriptions được sinh động từ `get_all_tools()`.

**Bài Học:** Tool description trong system prompt phải được sinh tự động từ registry thực tế, không được viết tay để tránh drift.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**: Khối `Thought` giúp ích gì cho agent so với câu trả lời trực tiếp của Chatbot?

Chatbot trả lời dựa trên kiến thức đã học (có thể lỗi thời hoặc bịa đặt do vấn đề dữ liệu). ReAct agent dùng Thought để "lập kế hoạch trước khi hoạt động":

```
Thought: Người dùng muốn biết thời tiết Đà Nẵng trước khi đặt vé.
         Tôi cần gọi check_weather trước, rồi mới search_flights.
Action: check_weather(Đà Nẵng)
```

Không có `Thought`, LLM có xu hướng trả lời ngay bằng kiến thức nội bộ, bỏ qua gọi Tools. Trong log: các câu hỏi không liên quan đến du lịch đều kết thúc với `reason: no_action_found`.

2. **Reliability**: Trong trường hợp nào Agent thực sự hoạt động *kém hơn* Chatbot?

| Tình huống | Chatbot | Agent |
| :--- | :--- | :--- |
| Con gà đẻ trứng hay đẻ con | Trả lời ngay | Mất thời gian loop và không có tool phù hợp |
| Câu hỏi ngoài vấn đề du lịch | Có thể trả lời | Gọi tool không liên quan |
| Câu hỏi cần số liệu realtime | Bịa | Gọi tool lấy dữ liệu thực |
| Bài toán nhiều bước | Bỏ sót bước | Tuần tự từng bước |

**Kết luận:** Agent kém hơn chatbot khi câu hỏi đơn giản, không cần tool. Token của agent cao hơn đáng kể.

3. **Observation**: Phản hồi từ môi trường (observations) ảnh hưởng như thế nào đến các bước tiếp theo?

Observation là cơ chế feedback loop quan trọng nhất. Sau mỗi tool call, kết quả được append vào prompt:

```python
current_prompt += f"\n{response_text}\nObservation: {tool_result}"
```

Giả dụ `check_weather` trả về "Mưa lớn, 20°C", Thought tiếp theo của agent sẽ tự điều chỉnh gợi ý trang phục và hoạt động. Đây là điểm mà chatbot hoàn toàn không có — chatbot không phản ứng với dữ liệu giữa chừng.

---

## IV. Future Improvements (5 Points)

### Khả Năng Mở Rộng
Chuyển sang **kiến trúc async** để tool calls chạy song song thay vì tuần tự:

```python
# Thay vì gọi tuần tự check_weather → get_attractions
# Dùng asyncio.gather để gọi đồng thời → giảm latency 40-60%
results = await asyncio.gather(check_weather(dest), get_attractions(dest))
```

### An Toàn
Thêm **Supervisor LLM** kiểm tra output của agent trước khi trả lời để phát hiện hallucination, nội dung không phù hợp, hoặc tool call với tham số bất thường (giá âm, destination rỗng).

### Hiệu Năng
Tích hợp **Vector DB** để agent tự chọn tool phù hợp bằng semantic search thay vì liệt kê tất cả trong prompt. Khi hệ thống có 50+ tools, prompt sẽ quá dài và LLM dễ nhầm — vector retrieval giải quyết vấn đề này.

# Bản Đồ Tài Liệu

Thư mục `docs/` chứa hai nhóm thông tin chính:

- **Harness**: cách người dùng và agent làm việc với nhau.
- **Product contract**: LLM-Local hiện tại phải hoạt động như thế nào.

Tài liệu trong repo này không chỉ là ghi chú. Nó là mặt phẳng điều khiển để
agent biết nên sửa gì, sửa ở đâu, và cần chứng minh bằng cách nào.

## Các File Chính

- `HARNESS.md`: quy trình hợp tác giữa human và agent.
- `FEATURE_INTAKE.md`: cách biến prompt thành loại việc và risk lane:
  `tiny`, `normal`, hoặc `high-risk`.
- `ARCHITECTURE.md`: topology, boundary, Docker Compose services, network,
  bind mounts.
- `TEST_MATRIX.md`: bảng mapping giữa behavior/story và bằng chứng validation.
- `HARNESS_BACKLOG.md`: nơi ghi các điểm cần cải tiến trong quy trình harness.
- `GLOSSARY.md`: thuật ngữ dùng chung.

## Các Thư Mục

- `product/`: sự thật hiện tại của sản phẩm LLM-Local.
- `stories/`: backlog và các story packet cụ thể.
- `decisions/`: các quyết định kỹ thuật/architecture đã chốt.
- `templates/`: mẫu cho story, decision, validation report, high-risk story.

## Trạng Thái Hiện Tại

Harness v0 đang được sử dụng. LLM-Local đã có hạ tầng cơ bản cho:

- Serving qua Ollama và vLLM.
- Training qua Unsloth.
- Evaluation qua latency benchmark và lm-eval-harness.
- Observation qua summary/chart từ benchmark results.
- Model management qua thư mục `models/` và script download.

CI và một lệnh validation tổng ở cấp repo chưa được định nghĩa đầy đủ.

## Kiến Trúc Tài Liệu

```text
Prompt / spec / change request
        |
        v
FEATURE_INTAKE.md
  - phân loại việc
  - chọn risk lane
        |
        v
docs/product/*
  - điều gì phải đúng?
        |
        v
ARCHITECTURE.md
  - nó nằm ở đâu?
  - boundary thế nào?
        |
        v
docs/stories/*
  - slice nào đang được làm?
        |
        v
TEST_MATRIX.md
  - bằng chứng nào chứng minh nó chạy?
        |
        v
docs/decisions/*
  - vì sao chọn hướng này?
```

## Cách Đọc Nhanh

Nếu muốn hiểu repo:

1. Đọc `README.md` ở repo root để nắm cấu trúc và lệnh chạy nhanh.
2. Đọc `docs/product/domains.md` để biết từng domain phải làm gì.
3. Đọc `docs/ARCHITECTURE.md` để biết các service nối với nhau thế nào.
4. Đọc `docs/stories/backlog.md` để biết việc nào đang được đề xuất.
5. Đọc `docs/TEST_MATRIX.md` để biết cái gì đã có proof, cái gì chưa.

Nếu muốn sửa hoặc thêm tính năng:

1. Bắt đầu từ `FEATURE_INTAKE.md`.
2. Xác định input type: change request, maintenance, spec slice, new
   initiative, hoặc harness improvement.
3. Xác định lane: `tiny`, `normal`, hoặc `high-risk`.
4. Cập nhật product docs/story/test matrix nếu behavior thay đổi.
5. Chạy validation có liên quan và ghi evidence.

## Vai Trò Của Từng Nhóm Tài Liệu

### `docs/product/`

Đây là product truth. Nếu behavior của LLM-Local thay đổi, thư mục này phải
được cập nhật.

Ví dụ:

- Serving có Ollama và vLLM.
- Training dùng Unsloth.
- Evaluation có latency benchmark và quality eval.
- Observation đọc kết quả benchmark để tạo CSV/chart.
- Model management dùng `models/` làm nơi chia sẻ weights.

### `docs/ARCHITECTURE.md`

File này nói về hình dạng hệ thống:

- Docker Compose stack cho từng domain.
- External network `llm-net`.
- Bind mounts: `models/`, `datasets/`, `evaluation/results/`,
  `observation/dashboards/`.
- Boundary giữa config, service, script, và shared resources.

Trước khi thêm service/script mới, nên xem file này để không làm lệch topology.

### `docs/stories/`

Story là gói việc có ranh giới rõ ràng. Một story tốt nên có:

- Product contract.
- Acceptance criteria.
- Design notes.
- Validation expectations.
- Evidence sau khi validate.

Dùng:

- `docs/templates/story.md` cho việc bình thường.
- `docs/templates/high-risk-story/` cho việc có rủi ro cao.
- `docs/stories/backlog.md` cho việc mới được đề xuất, chưa chọn làm.

### `docs/TEST_MATRIX.md`

Đây là bảng proof. Mỗi behavior/story nên có dòng riêng.

Trạng thái không nên đổi thành `implemented` chỉ vì đã sửa code. Chỉ nên đổi
khi có bằng chứng validation như:

- command output,
- report,
- log,
- screenshot,
- story evidence.

### `docs/decisions/`

Dùng để ghi lại lý do của các quyết định lâu dài:

- Chọn architecture nào.
- Chọn validation strategy nào.
- Chọn network/compose convention nào.
- Thay đổi scope hoặc risk posture.

Mục tiêu là để agent sau không hỏi lại cùng một câu hỏi.

### `docs/HARNESS_BACKLOG.md`

Đây không phải backlog product. Đây là backlog cho quy trình làm việc.

Dùng file này khi phát hiện:

- Một validation step lặp lại nhiều lần nhưng chưa có template.
- Feature intake còn mơ hồ.
- Thiếu checklist cho Docker/GPU.
- Một pattern docs nên được chuẩn hóa.

Product bugs và implementation gaps nên vào `docs/stories/backlog.md`, không
đưa vào `HARNESS_BACKLOG.md`.

## Logic Làm Việc

```text
1. Đọc truth hiện tại:
   README.md -> HARNESS.md -> FEATURE_INTAKE.md -> docs/product/*

2. Phân loại request:
   input type + risk lane + docs bị ảnh hưởng

3. Chọn container công việc:
   tiny patch, normal story, hoặc high-risk story

4. Thực hiện thay đổi:
   compose, script, docs, contract, hoặc operational config

5. Ghi proof:
   cập nhật TEST_MATRIX.md và story evidence sau khi validate

6. Ghi lý do:
   thêm decision nếu quyết định ảnh hưởng về sau

7. Cải tiến harness:
   sửa docs nhỏ trực tiếp, hoặc thêm item vào HARNESS_BACKLOG.md
```


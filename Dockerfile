# HĐH GIAO/CDFL chạy ẢO HÓA — container Linux thật.
# build:  docker build -t giao-os .
# chạy :  docker run --rm giao-os                 # 3 nhịp rồi thoát
#         docker run --rm --memory=256m giao-os   # giới hạn RAM → tác tử CẢM được ràng buộc ảo hóa
#         docker run --rm giao-os python os_giao_linux.py --mãi --ngắt 5   # daemon nền
FROM python:3.11-slim
ENV PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /giao
# Chỉ lõi cần cho lương tri (không kéo Ollama/numpy gì) — nhẹ & tất định
COPY giao.py chuẩn.giao cau_noi.giao os_giao_linux.py ./
# tác tử chỉ-đề-xuất, không cần quyền gì; chạy user thường cho an toàn
RUN useradd -m giao && chown -R giao /giao
USER giao
CMD ["python", "os_giao_linux.py", "3"]

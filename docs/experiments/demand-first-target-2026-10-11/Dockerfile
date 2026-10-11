FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY target /target
RUN python -m pip install /target pytest hypothesis && python -m pip freeze > /dependencies.txt
COPY study /study
WORKDIR /study
CMD ["python", "native_http.py", "/results"]

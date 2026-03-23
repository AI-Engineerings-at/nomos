FROM python:3.11-slim
WORKDIR /app
RUN pip install streamlit
COPY . .
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN echo "force rebuild"

COPY . .

CMD ["python", "-m", "app.main"]
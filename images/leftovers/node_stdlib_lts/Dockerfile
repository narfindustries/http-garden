FROM http-garden-soil:latest

RUN apt -y update && apt -y upgrade && apt -y install --no-install-recommends nodejs

COPY app.js /app/app.js

CMD ["node", "app.js"]

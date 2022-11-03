FROM python:3.9

RUN mkdir app/

COPY ./ /app/

WORKDIR /app/

RUN chmod 774 *

RUN pip install --upgrade pip

RUN pip install -r requirements.txt
 
ENTRYPOINT ["sh", "appentry.sh"]

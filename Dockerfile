FROM python:3.7
ARG COPILOT_ENV
ENV PYTHONUNBUFFERED=1
ENV COPILOT_ENV=${COPILOT_ENV} 
RUN mkdir uuid
COPY . /uuid
RUN pip3 install -r /uuid/requirements.txt
CMD stdbuf -oL python -u /uuid/__main__.py --${COPILOT_ENV}
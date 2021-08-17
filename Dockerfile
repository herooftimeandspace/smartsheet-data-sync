FROM python:3.7
# RUN pip3 install smartsheet-python-sdk
# RUN pip3 install apscheduler
# RUN pip3 install python-dotenv
# RUN pip3 install boto3
ENV PYTHONUNBUFFERED=1
RUN mkdir uuid
COPY . /uuid
RUN pip3 install -r /uuid/requirements.txt
CMD ["stdbuf", "-oL", "python", "-u", "/uuid/__main__.py"]
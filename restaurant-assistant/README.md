# Deploy to AWS Lambda

I use SAM for deployment:

```bash
sam deploy --profile <AWS-user>
```

It requires all dependencies to be stored in the requirements.txt file. I use the following command to generate it:

```bash
pipenv requirements > restaurant-assistant/src/requirements.txt
```
# Deploy to AWS Lambda

I use SAM for deployment:

```bash
sam deploy --profile <AWS-user>
```

It requires all dependencies to be stored in the requirements.txt file. I use the following command to generate it:

```bash
pipenv requirements > restaurant-assistant/src/requirements.txt
```

This doesn't really work at the moment. I'm able to deploy the source code but Python dependencies are not installed. I think this is because there are too manu of them. I'll try to reduce the number of dependencies and see if it helps.
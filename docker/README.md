This directory has a wrapper that runs docker-compose for you.  Pass
it the same arguments that you would to docker-compose.

If you are want salesforce integration, put your `salesforce.env` file
in this directory.  If you don't want salesforce integration, delete
`salesforce.env` or make sure it is an empty file.  The wrapper will
take care of it from there.
